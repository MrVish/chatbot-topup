"""
SQL Tool for read-only query execution.

This module provides the SQL Tool that executes templated SQL queries
against the SQLite database with read-only access. It handles:
- Template selection based on query intent
- Parameter binding from segment filters
- Read-only database connections
- Row limiting (10,000 max)
- Query logging with latency tracking
"""

import logging
import sqlite3
import time
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from models.schemas import Plan

# Configure logging
logger = logging.getLogger(__name__)

# Template directory
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"

# Intent to template mapping
INTENT_TEMPLATE_MAP = {
    "trend": "trend_weekly.sql",
    "variance": "wow_delta.sql",  # Default to WoW for variance
    "forecast_vs_actual": "forecast_vs_actual_weekly.sql",
    "forecast_gap_analysis": "forecast_variance_decomposition.sql",  # Variance decomposition
    "funnel": "funnel_last_full_month.sql",
    "distribution": "distribution.sql",
    "relationship": "trend_weekly.sql",  # Use trend template for relationship
    "multi_metric": "multi_metric_trend.sql",  # Multi-metric comparison
}


def _get_date_range(window: str) -> tuple[str, str]:
    """
    Calculate start and end dates based on time window.
    
    Args:
        window: Time window specification (last_7d, last_full_week, qtd, mtd, ytd, etc.)
        
    Returns:
        Tuple of (start_date_sql, end_date_sql) as SQLite date expressions
    """
    date_ranges = {
        "last_7d": (
            "date('now', '-7 days')",
            "date('now')"
        ),
        "last_full_week": (
            "date('now', 'weekday 0', '-7 days')",
            "date('now', 'weekday 0', '-1 day')"
        ),
        "last_30d": (
            "date('now', '-30 days')",
            "date('now')"
        ),
        "last_full_month": (
            "date('now', 'start of month', '-1 month')",
            "date('now', 'start of month', '-1 day')"
        ),
        "last_3_full_months": (
            "date('now', 'start of month', '-4 months')",
            "date('now', 'start of month', '-1 day')"
        ),
        # Last full quarter (previous complete quarter)
        "last_full_quarter": (
            "date('now', 'start of month', '-' || ((strftime('%m', 'now') - 1) % 3 + 3) || ' months')",
            "date('now', 'start of month', '-' || ((strftime('%m', 'now') - 1) % 3) || ' months', '-1 day')"
        ),
        # Last full year (previous complete year)
        "last_full_year": (
            "date('now', 'start of year', '-1 year')",
            "date('now', 'start of year', '-1 day')"
        ),
        # Quarter-to-date, Month-to-date, Year-to-date
        "qtd": (
            "date('now', 'start of month', '-' || ((strftime('%m', 'now') - 1) % 3) || ' months')",
            "date('now')"
        ),
        "mtd": (
            "date('now', 'start of month')",
            "date('now')"
        ),
        "ytd": (
            "date('now', 'start of year')",
            "date('now')"
        ),
    }
    return date_ranges.get(window, date_ranges["last_30d"])


def _get_metric_expression(metric: str) -> str:
    """
    Convert metric name to SQL expression.
    
    Handles both amount and count metrics, with proper aggregation.
    
    Args:
        metric: Metric name (e.g., app_submit_amnt, issued_amnt)
        
    Returns:
        SQL expression for the metric
    """
    # Amount metrics (default)
    if metric in ["app_submit_amnt", "app_submit_amt"]:
        return "SUM(app_submit_amnt)"
    elif metric in ["apps_approved_amnt", "apps_approved_amt", "approval_amt"]:
        return "SUM(CASE WHEN cr_appr_flag = 1 THEN apps_approved_amnt ELSE 0 END)"
    elif metric in ["issued_amnt", "issued_amt"]:
        return "SUM(CASE WHEN issued_flag = 1 THEN issued_amnt ELSE 0 END)"
    
    # Count metrics
    elif metric == "app_submit_count":
        return "COUNT(app_submit_d)"
    elif metric == "apps_approved_count":
        return "SUM(cr_appr_flag)"
    elif metric == "issued_count":
        return "SUM(issued_flag)"
    
    # Rate metrics
    elif metric == "approval_rate":
        return "ROUND(CAST(SUM(cr_appr_flag) AS REAL) / NULLIF(SUM(offered_flag), 0) * 100, 2)"
    elif metric == "funding_rate":
        return "ROUND(CAST(SUM(issued_flag) AS REAL) / NULLIF(COUNT(app_submit_d), 0) * 100, 2)"
    
    # Average metrics
    elif metric == "avg_apr":
        return "ROUND(AVG(offer_apr), 2)"
    elif metric == "avg_fico":
        return "ROUND(AVG(cr_fico), 2)"
    elif metric == "avg_dti":
        return "ROUND(AVG(cr_dti), 2)"
    elif metric == "avg_income":
        return "ROUND(AVG(a_income), 2)"
    
    # Default: assume it's a column name and sum it
    else:
        return f"SUM({metric})"


def _build_segment_filters(plan: Plan) -> Dict[str, str]:
    """
    Build SQL filter clauses from segment filters.
    
    Args:
        plan: Query plan with segment filters
        
    Returns:
        Dictionary of filter placeholders and their SQL clauses
    """
    filters = {}
    segments = plan.segments
    
    # Channel filter ("ALL" means no filter, group by all values)
    if segments.channel and segments.channel != "ALL":
        filters["channel_filter"] = f"AND channel = '{segments.channel}'"
    else:
        filters["channel_filter"] = ""
    
    # Grade filter ("ALL" means no filter, group by all values)
    if segments.grade and segments.grade != "ALL":
        filters["grade_filter"] = f"AND grade = '{segments.grade}'"
    else:
        filters["grade_filter"] = ""
    
    # Product type filter ("ALL" means no filter, group by all values)
    if segments.prod_type and segments.prod_type != "ALL":
        filters["prod_type_filter"] = f"AND prod_type = '{segments.prod_type}'"
    else:
        filters["prod_type_filter"] = ""
    
    # Repeat type filter
    if segments.repeat_type:
        filters["repeat_type_filter"] = f"AND repeat_type = '{segments.repeat_type}'"
    else:
        filters["repeat_type_filter"] = ""
    
    # Term filter
    if segments.term:
        filters["term_filter"] = f"AND term = {segments.term}"
    else:
        filters["term_filter"] = ""
    
    # FICO band filter
    if segments.cr_fico_band:
        filters["fico_band_filter"] = f"AND cr_fico_band = '{segments.cr_fico_band}'"
    else:
        filters["fico_band_filter"] = ""
    
    # Purpose filter
    if segments.purpose:
        filters["purpose_filter"] = f"AND purpose = '{segments.purpose}'"
    else:
        filters["purpose_filter"] = ""
    
    return filters


def _build_forecast_columns(metric: str) -> Dict[str, str]:
    """
    Build forecast column mappings based on metric type.
    
    Args:
        metric: Metric name
        
    Returns:
        Dictionary with forecast_col, outlook_col, and actual_col
    """
    # Determine metric type from metric name
    if "submit" in metric.lower():
        return {
            "forecast_col": "forecast_app_submits",
            "outlook_col": "outlook_app_submits",
            "actual_col": "actual_app_submits",
        }
    elif "approv" in metric.lower():
        return {
            "forecast_col": "forecast_apps_approved",
            "outlook_col": "outlook_apps_approved",
            "actual_col": "actual_apps_approved",
        }
    elif "issue" in metric.lower() or "issuance" in metric.lower():
        return {
            "forecast_col": "forecast_issuance",
            "outlook_col": "outlook_issuance",
            "actual_col": "actual_issuance",
        }
    else:
        # Default to issuance
        return {
            "forecast_col": "forecast_issuance",
            "outlook_col": "outlook_issuance",
            "actual_col": "actual_issuance",
        }


def _has_segmentation(plan: Plan) -> bool:
    """
    Check if plan has any segmentation (non-None segment values).
    
    Args:
        plan: Query plan
        
    Returns:
        bool: True if any segment is not None
    """
    segments = plan.segments
    if isinstance(segments, dict):
        return any(v is not None for v in segments.values())
    return False


def _has_all_segment(plan: Plan) -> bool:
    """
    Check if plan has any segment set to "ALL" (meaning group by that dimension).
    
    Args:
        plan: Query plan
        
    Returns:
        bool: True if any segment is "ALL"
    """
    segments = plan.segments
    # Handle both dict and Pydantic model
    if hasattr(segments, 'model_dump'):
        segments_dict = segments.model_dump()
    elif isinstance(segments, dict):
        segments_dict = segments
    else:
        return False
    
    return any(v == "ALL" for v in segments_dict.values())


def run(plan: Plan, database_url: Optional[str] = None) -> pd.DataFrame:
    """
    Execute SQL query based on plan and return results as DataFrame.
    
    This is the main entry point for the SQL Tool. It:
    1. Selects the appropriate SQL template based on intent
    2. Builds parameter bindings from segment filters
    3. Opens a read-only SQLite connection
    4. Executes the query with parameters
    5. Returns results as a pandas DataFrame
    6. Logs query execution details
    
    Args:
        plan: Structured query plan from Planner Agent
        database_url: Optional database path (defaults to ./data/topup.db)
        
    Returns:
        pandas DataFrame with query results (max 10,000 rows)
        
    Raises:
        ValueError: If intent is not supported or template not found
        sqlite3.Error: If database query fails
    """
    start_time = time.time()
    
    # Default database path
    if database_url is None:
        database_url = str(Path(__file__).parent.parent / "data" / "topup.db")
    
    # Select template based on intent
    # Special case: variance with segmentation needs different template
    if plan.intent == "variance" and _has_segmentation(plan):
        template_name = "wow_by_segment.sql"
        logger.info(f"Using variance by segment template: {template_name}")
    # Special case: forecast_vs_actual with "ALL" segment needs by-segment template
    elif plan.intent == "forecast_vs_actual" and _has_all_segment(plan):
        template_name = "forecast_vs_actual_by_segment.sql"
        logger.info(f"Using forecast by segment template: {template_name}, segments: {plan.segments}")
    else:
        template_name = INTENT_TEMPLATE_MAP.get(plan.intent)
        if not template_name:
            raise ValueError(f"Unsupported intent: {plan.intent}")
        logger.info(f"Using standard template for intent {plan.intent}: {template_name}")
    
    template_path = TEMPLATE_DIR / template_name
    if not template_path.exists():
        raise ValueError(f"Template not found: {template_path}")
    
    # Load template
    with open(template_path, "r") as f:
        sql_template = f.read()
    
    # Build parameters
    params = {}
    
    # Date range parameters (for templates that use them)
    if plan.intent in ["trend", "funnel", "distribution", "forecast_vs_actual", "forecast_gap_analysis", "multi_metric"]:
        start_date_expr, end_date_expr = _get_date_range(plan.window)
        # For SQLite, we need to evaluate these expressions
        # We'll use a temporary connection to evaluate them
        temp_conn = sqlite3.connect(database_url, uri=True)
        cursor = temp_conn.cursor()
        cursor.execute(f"SELECT {start_date_expr}, {end_date_expr}")
        start_date, end_date = cursor.fetchone()
        temp_conn.close()
        
        params["start_date"] = start_date
        params["end_date"] = end_date
    
    # Build metric expression (not needed for multi_metric)
    # If multiple metrics are provided (comma-separated), use only the first one for single-metric templates
    metric_to_use = plan.metric.split(',')[0].strip() if ',' in plan.metric else plan.metric
    metric_expression = _get_metric_expression(metric_to_use)
    
    # Build segment filters
    segment_filters = _build_segment_filters(plan)
    
    # Prepare all format parameters
    format_params = {
        "granularity": plan.granularity,  # All templates need granularity
        **segment_filters
    }
    
    # Add date_col and metric_expression for templates that need them
    # (multi_metric template doesn't use these as it has hardcoded date columns)
    if plan.intent != "multi_metric":
        format_params["date_col"] = plan.date_col
        format_params["metric_expression"] = metric_expression
        
        # Add time grouping based on granularity for trend queries
        if plan.intent in ["trend", "relationship"]:
            if plan.granularity == "daily":
                format_params["time_group"] = f"strftime('%Y-%m-%d', {plan.date_col})"
                format_params["time_label"] = f"strftime('%Y-%m-%d', {plan.date_col})"
            elif plan.granularity == "weekly":
                format_params["time_group"] = f"strftime('%Y-%W', {plan.date_col})"
                format_params["time_label"] = f"strftime('%Y-%m-%d', {plan.date_col}, 'weekday 0', '-6 days')"
            elif plan.granularity == "monthly":
                format_params["time_group"] = f"strftime('%Y-%m', {plan.date_col})"
                format_params["time_label"] = f"strftime('%Y-%m-01', {plan.date_col})"
            else:
                # Default to daily
                format_params["time_group"] = f"DATE({plan.date_col})"
                format_params["time_label"] = f"DATE({plan.date_col})"
    
    # Handle forecast-specific columns
    if plan.intent in ["forecast_vs_actual", "forecast_gap_analysis"]:
        forecast_cols = _build_forecast_columns(plan.metric)
        format_params.update(forecast_cols)
        
        # If using by-segment template, determine segment_by
        if plan.intent == "forecast_vs_actual" and _has_all_segment(plan):
            segment_by = "channel"  # Default
            
            if plan.segments.channel == "ALL":
                segment_by = "channel"
            elif plan.segments.grade == "ALL":
                segment_by = "grade"
            elif plan.segments.prod_type == "ALL":
                segment_by = "prod_type"
            elif plan.segments.repeat_type == "ALL":
                segment_by = "repeat_type"
            elif plan.segments.term == "ALL":
                segment_by = "term"
            
            format_params["segment_by"] = segment_by
    
    # Handle distribution segment_by
    if plan.intent == "distribution":
        # Determine which segment to group by
        # "ALL" is a special value meaning "group by this dimension"
        segment_by = "channel"  # Default
        
        if plan.segments.channel == "ALL":
            segment_by = "channel"
        elif plan.segments.grade == "ALL":
            segment_by = "grade"
        elif plan.segments.prod_type == "ALL":
            segment_by = "prod_type"
        elif plan.segments.cr_fico_band == "ALL":
            segment_by = "cr_fico_band"
        elif plan.segments.repeat_type == "ALL":
            segment_by = "repeat_type"
        elif plan.segments.term == "ALL":
            segment_by = "term"
        elif plan.segments.purpose == "ALL":
            segment_by = "purpose"
        # If no "ALL" value, check for any non-None value (filter case)
        elif plan.segments.grade:
            segment_by = "grade"
        elif plan.segments.prod_type:
            segment_by = "prod_type"
        elif plan.segments.cr_fico_band:
            segment_by = "cr_fico_band"
        elif plan.segments.repeat_type:
            segment_by = "repeat_type"
        elif plan.segments.term:
            segment_by = "term"
        elif plan.segments.purpose:
            segment_by = "purpose"
        
        format_params["segment_by"] = segment_by
    
    # Replace all template placeholders in one go
    sql_query = sql_template.format(**format_params)
    
    # Open read-only connection
    # SQLite read-only mode requires URI format
    db_uri = f"file:{database_url}?mode=ro"
    
    try:
        conn = sqlite3.connect(db_uri, uri=True)
        
        # Execute query and fetch results
        df = pd.read_sql_query(sql_query, conn, params=params)
        
        # Apply row limit
        if len(df) > 10000:
            logger.warning(
                f"Query returned {len(df)} rows, limiting to 10,000",
                extra={"plan": plan.model_dump()}
            )
            df = df.head(10000)
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Log query execution
        logger.info(
            "SQL query executed successfully",
            extra={
                "intent": plan.intent,
                "metric": plan.metric,
                "table": plan.table,
                "window": plan.window,
                "segments": plan.segments.model_dump(exclude_none=True),
                "sql": sql_query,
                "params": params,
                "row_count": len(df),
                "execution_time_ms": round(execution_time * 1000, 2),
            }
        )
        
        return df
        
    except sqlite3.Error as e:
        execution_time = time.time() - start_time
        logger.error(
            f"SQL query failed: {str(e)}",
            extra={
                "intent": plan.intent,
                "sql": sql_query,
                "params": params,
                "execution_time_ms": round(execution_time * 1000, 2),
                "error": str(e),
            }
        )
        raise
        
    finally:
        if 'conn' in locals():
            conn.close()
