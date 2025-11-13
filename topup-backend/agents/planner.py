"""
Planner Agent for structured query plan generation.

This module provides the Planner Agent that converts user queries and
classified intents into structured Plan objects using OpenAI structured
outputs. It handles:
- Query plan generation with all required fields
- Default rules (30-day window, weekly granularity for ≤3 months)
- Metric interpretation (amounts vs counts)
- Table and date column selection
- Chart type selection based on intent
- Segment filter parsing and validation
"""

import json
import logging
import os
import re
from typing import Dict, List, Optional

from openai import OpenAI
from pydantic import ValidationError

from models.schemas import Plan, SegmentFilters

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client (lazy initialization)
_client = None

def _get_client():
    """Get or create OpenAI client."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        _client = OpenAI(api_key=api_key)
    return _client


# System prompt for planner agent
PLANNER_SYSTEM_PROMPT = """You are a query planning expert for a CXO marketing analytics assistant.

Your task is to convert user queries into structured query plans that will be executed against a SQLite database.

**IMPORTANT**: You must respond with valid JSON following the specified schema.

**Database Schema:**

Table: cps_tb (Customer Acquisition Data)
- loan_id: BIGINT (unique loan identifier)
- app_create_d: DATE (application creation date)
- app_submit_d: DATE (application submission date)
- app_submit_amnt: FLOAT (submitted loan amount)
- apps_approved_d: DATE (approval date)
- apps_approved_amnt: FLOAT (approved loan amount)
- issued_d: DATE (issuance/funding date)
- issued_amnt: FLOAT (issued loan amount)
- prod_type: TEXT (Prime, NP, D2P)
- repeat_type: TEXT (Repeat, New)
- channel: TEXT (OMB, Email, Search, D2LC, DM, LT, Experian, Karma, Small Partners)
- grade: TEXT (P1, P2, P3, P4, P5, P6)
- term: BIGINT (36, 48, 60, 72, 84)
- offered_flag: BOOLEAN (whether offer was made)
- website_complete_flag: BOOLEAN (whether website application completed)
- cr_appr_flag: BIGINT (0/1 - credit approval flag)
- issued_flag: BIGINT (0/1 - issuance flag)
- cr_fico: BIGINT (credit score)
- cr_fico_band: TEXT (<640, 640-699, 700-759, 760+)
- a_income: BIGINT (annual income)
- cr_dti: FLOAT (debt-to-income ratio)
- purpose: TEXT (debt_consolidation, home_improvement, major_purchase, medical, car, other)
- interest_rate: FLOAT (interest rate)
- offer_apr: FLOAT (offered APR)
- origination_fee: FLOAT (origination fee)

Table: forecast_df (Forecast Data)
- date: DATE
- prod_type: TEXT (Prime, NP, D2P)
- repeat_type: TEXT (Repeat, New)
- channel: TEXT
- grade: TEXT
- term: BIGINT
- forecast_app_submits: FLOAT (forecasted app submissions)
- forecast_apps_approved: FLOAT (forecasted approvals)
- forecast_issuance: FLOAT (forecasted issuances)
- outlook_app_submits: FLOAT (outlook app submissions)
- outlook_apps_approved: FLOAT (outlook approvals)
- outlook_issuance: FLOAT (outlook issuances)
- actual_app_submits: FLOAT (actual app submissions)
- actual_apps_approved: FLOAT (actual approvals)
- actual_issuance: FLOAT (actual issuances)

**Metric Interpretation Rules:**

1. **Default to AMOUNTS (not counts):**
   - "app submits" or "submissions" → app_submit_amnt (sum of loan amounts)
   - "app approvals" or "approvals" → apps_approved_amnt (sum of approved amounts)
   - "issuances" or "funded" → issued_amnt (sum of issued amounts)

2. **Use COUNTS only when explicitly requested:**
   - "number of app submits" → COUNT(app_submit_d)
   - "count of approvals" → SUM(cr_appr_flag)
   - "number of issuances" → SUM(issued_flag)

3. **Other metrics:**
   - "approval rate" → calculated metric (SUM(cr_appr_flag) / SUM(offered_flag))
   - "funding rate" → calculated metric (SUM(issued_flag) / COUNT(app_submit_d))
   - "average APR" → AVG(offer_apr)
   - "average FICO" → AVG(cr_fico)

4. **For multi_metric intent:**
   - Use a comma-separated string to indicate which metrics to include
   - "app_submit_amnt" = only submissions
   - "app_submit_amnt,apps_approved_amnt" = submissions and approvals
   - "app_submit_amnt,apps_approved_amnt,issued_amnt" = all three metrics
   - "apps_approved_amnt,issued_amnt" = approvals and issuances only
   - Parse the user query to determine which metrics they want:
     * "app submits" or "submissions" → include app_submit_amnt
     * "approvals" or "approved" → include apps_approved_amnt
     * "issuances" or "issued" or "funded" → include issued_amnt
   - If user says "vs" or "and" between metrics, include all mentioned metrics
   - Examples:
     * "Show app submits vs approvals" → "app_submit_amnt,apps_approved_amnt"
     * "Compare all three metrics" → "app_submit_amnt,apps_approved_amnt,issued_amnt"
     * "Submissions and issuances" → "app_submit_amnt,issued_amnt"

**Date Column Selection Rules:**
- For app submits/submissions → app_submit_d
- For app approvals → apps_approved_d
- For issuances/funded → issued_d
- For forecast queries → date (from forecast_df table)

**Table Selection Rules:**
- forecast_vs_actual intent → forecast_df
- forecast_gap_analysis intent → forecast_df
- All other intents → cps_tb

**Time Window Rules:**
- If not specified → default to "last_30d"
- "last 7 days" → last_7d
- "last week" or "last full week" → last_full_week
- "last 30 days" → last_30d
- "last month" or "last full month" → last_full_month
- "last 3 months" or "last 3 full months" → last_3_full_months
- "last quarter" or "last full quarter" → last_full_quarter
- "last year" or "last full year" → last_full_year
- "quarter to date" or "QTD" or "this quarter" → qtd
- "month to date" or "MTD" or "this month" → mtd
- "year to date" or "YTD" or "this year" → ytd

**Granularity Rules (IMPORTANT):**
- Time window ≤ 1 month (last_7d, last_full_week, last_30d, last_full_month) → daily granularity
- Time window > 1 month and ≤ 4 months (last_3_full_months) → weekly granularity
- Time window > 3 months → monthly granularity
- User can override with explicit request (e.g., "daily trend", "weekly breakdown", "monthly summary")

**Chart Type Selection by Intent:**
- trend → line
- variance → grouped_bar
- forecast_vs_actual → grouped_bar
- forecast_gap_analysis → waterfall (shows variance decomposition by segment)
- funnel → funnel
- distribution → pie
- relationship → scatter
- multi_metric → line (multiple lines on same chart)

**Intent Classification - Forecast Queries:**
IMPORTANT: Distinguish between two types of forecast queries:

1. **forecast_vs_actual** - Comparing forecast to actual over time or by segment
   - Keywords: "forecast vs actual", "compare forecast", "forecast performance"
   - Shows: Time series or segment comparison of forecast vs actual values
   - Chart: grouped_bar

2. **forecast_gap_analysis** - Analyzing WHY there's a gap (variance decomposition)
   - Keywords: "forecast gap", "gap analysis", "largest gap", "biggest gap", "driving the forecast", "forecast miss", "forecast variance", "variance decomposition"
   - Shows: Which segments contribute most to the overall forecast variance
   - Chart: waterfall
   - Example: "Where are we seeing the largest gap?" → forecast_gap_analysis

**Segment Filter Parsing:**
Extract segment filters from the user query:
- Channel: OMB, Email, Search, D2LC, DM, LT, Experian, Karma, Small Partners
- Grade: P1, P2, P3, P4, P5, P6
- Product Type: Prime, NP, D2P
- Repeat Type: Repeat, New (also recognize "repeat customers" or "new customers")
- Term: 36, 48, 60, 72, 84
- FICO Band: <640, 640-699, 700-759, 760+
- Purpose: debt_consolidation, home_improvement, major_purchase, medical, car, other

**IMPORTANT: "by X" means segment by that dimension:**
- "by channel" → set channel to "ALL" (means group by all channels)
- "by grade" → set grade to "ALL" (means group by all grades)
- "by product type" → set prod_type to "ALL" (means group by all product types)
- "for Email" → set channel to "Email" (means filter to Email only)
- "for Prime" → set prod_type to "Prime" (means filter to Prime only)

Use "ALL" as a special value to indicate grouping by that dimension rather than filtering.

**CRITICAL: You MUST return a JSON object with ALL of these exact fields:**

```json
{
  "intent": "<the classified intent>",
  "table": "cps_tb or forecast_df",
  "metric": "<metric column name>",
  "date_col": "<date column name>",
  "window": "<time window code like last_30d>",
  "granularity": "daily or weekly or monthly",
  "chart": "<chart type>",
  "segments": {
    "channel": "<value or null>",
    "grade": "<value or null>",
    "prod_type": "<value or null>",
    "repeat_type": "<value or null>",
    "term": "<value or null>",
    "cr_fico_band": "<value or null>",
    "purpose": "<value or null>"
  }
}
```

ALL fields are required. Use null for segments not mentioned in the query."""


def _parse_multi_metric_request(user_query: str, default_metric: str) -> str:
    """
    Parse user query to determine which metrics they want for multi_metric queries.
    
    Args:
        user_query: User's natural language query
        default_metric: Default metric if parsing fails
        
    Returns:
        str: Comma-separated list of metric column names
    """
    user_query_lower = user_query.lower()
    metrics = []
    
    # Check for each metric type
    if any(term in user_query_lower for term in ["submit", "submission", "app submit", "application"]):
        metrics.append("app_submit_amnt")
    
    if any(term in user_query_lower for term in ["approval", "approved", "app approval"]):
        metrics.append("apps_approved_amnt")
    
    if any(term in user_query_lower for term in ["issuance", "issued", "funded", "funding"]):
        metrics.append("issued_amnt")
    
    # If no metrics found, return default
    if not metrics:
        return default_metric if default_metric else "app_submit_amnt"
    
    # Return comma-separated list
    return ",".join(metrics)


def make_plan(user_query: str, intent: str) -> Plan:
    """
    Generate a structured query plan from user query and intent.
    
    Uses OpenAI structured outputs to create a validated Plan object
    that includes table selection, metric, date column, time window,
    granularity, segments, and chart type.
    
    Args:
        user_query: Natural language query from the user
        intent: Classified intent (from Router Agent)
        
    Returns:
        Plan: Validated Plan object ready for SQL execution
        
    Raises:
        ValueError: If plan generation fails or validation errors occur
        
    Examples:
        >>> make_plan("Show weekly issuance by channel last 8 weeks", "trend")
        Plan(intent='trend', table='cps_tb', metric='issued_amnt', ...)
        
        >>> make_plan("How did actual issuance compare to forecast?", "forecast_vs_actual")
        Plan(intent='forecast_vs_actual', table='forecast_df', ...)
    """
    logger.info(
        "Generating query plan",
        extra={"user_query": user_query, "intent": intent}
    )
    
    try:
        # Get OpenAI client
        client = _get_client()
        
        # Create user message with query and intent
        user_message = f"""User Query: {user_query}
Classified Intent: {intent}

Generate a complete query plan following all the rules. Return the result as a JSON object."""
        
        # Call OpenAI with JSON mode for structured outputs
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Model that supports structured outputs
            messages=[
                {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.0  # Deterministic planning
        )
        
        # Extract and parse the JSON response
        import json
        content = response.choices[0].message.content
        
        if not content:
            logger.error("No content in OpenAI response")
            raise ValueError("OpenAI did not return a response")
        
        # Parse JSON and create Plan object
        plan_dict = json.loads(content)
        
        # Handle nested structure if OpenAI wraps the response
        if 'query_plan' in plan_dict:
            plan_dict = plan_dict['query_plan']
        
        # Fix multi_metric queries if OpenAI returns a dict for metric
        if plan_dict.get('intent') == 'multi_metric' and isinstance(plan_dict.get('metric'), dict):
            # For multi_metric, we only need one metric string
            # The SQL template handles all metrics automatically
            plan_dict['metric'] = 'app_submit_amnt'
        
        # Parse multi_metric queries to extract which metrics user wants
        if plan_dict.get('intent') == 'multi_metric':
            plan_dict['metric'] = _parse_multi_metric_request(user_query, plan_dict.get('metric', ''))
        
        # Apply defaults for missing required fields
        if not plan_dict.get('metric'):
            # Default metric based on intent
            if plan_dict.get('intent') == 'funnel':
                plan_dict['metric'] = 'issued_amnt'
            else:
                plan_dict['metric'] = 'app_submit_amnt'
        
        if not plan_dict.get('date_col'):
            # Default date column based on metric
            metric = plan_dict.get('metric', '')
            if 'approved' in metric:
                plan_dict['date_col'] = 'apps_approved_d'
            elif 'issued' in metric:
                plan_dict['date_col'] = 'issued_d'
            else:
                plan_dict['date_col'] = 'app_submit_d'
        
        plan = Plan(**plan_dict)
        
        # Apply post-processing and validation
        plan = _apply_default_rules(plan, user_query)
        plan = _validate_plan(plan)
        
        logger.info(
            "Query plan generated successfully",
            extra={
                "user_query": user_query,
                "intent": intent,
                "plan": plan.model_dump()
            }
        )
        
        return plan
        
    except ValidationError as e:
        logger.error(
            f"Plan validation failed: {str(e)}",
            extra={
                "user_query": user_query,
                "intent": intent,
                "error": str(e)
            }
        )
        raise ValueError(f"Invalid plan generated: {str(e)}")
        
    except Exception as e:
        logger.error(
            f"Failed to generate plan: {str(e)}",
            extra={
                "user_query": user_query,
                "intent": intent,
                "error": str(e)
            }
        )
        raise ValueError(f"Plan generation failed: {str(e)}")


def _parse_multi_metric_request(user_query: str, default_metric: str) -> str:
    """
    Parse user query to determine which metrics they want for multi_metric queries.
    
    Args:
        user_query: User's natural language query
        default_metric: Default metric if parsing fails
        
    Returns:
        str: Comma-separated list of metric column names
    """
    user_query_lower = user_query.lower()
    metrics = []
    
    # Check for each metric type
    if any(term in user_query_lower for term in ["submit", "submission", "app submit", "application"]):
        metrics.append("app_submit_amnt")
    
    if any(term in user_query_lower for term in ["approval", "approved", "app approval"]):
        metrics.append("apps_approved_amnt")
    
    if any(term in user_query_lower for term in ["issuance", "issued", "funded", "funding"]):
        metrics.append("issued_amnt")
    
    # If no metrics found, return default
    if not metrics:
        return default_metric if default_metric else "app_submit_amnt"
    
    # Return comma-separated list
    return ",".join(metrics)


def _apply_default_rules(plan: Plan, user_query: str) -> Plan:
    """
    Apply default rules and post-processing to the plan.
    
    Args:
        plan: Initial plan from OpenAI
        user_query: Original user query for context
        
    Returns:
        Plan: Plan with default rules applied
    """
    user_query_lower = user_query.lower()
    
    # Ensure granularity follows time window rules (unless user explicitly requested)
    if "daily" not in user_query_lower and "weekly" not in user_query_lower and "monthly" not in user_query_lower:
        # Apply automatic granularity based on time window
        if plan.window in ["last_7d", "last_full_week", "last_30d", "last_full_month", "mtd"]:
            # ≤ 1 month → daily granularity
            plan.granularity = "daily"
        elif plan.window in ["last_3_full_months", "last_full_quarter", "qtd"]:
            # > 1 month and ≤ 4 months → weekly granularity
            plan.granularity = "weekly"
        elif plan.window in ["last_full_year", "ytd"]:
            # Year-to-date or full year → monthly granularity
            plan.granularity = "monthly"
        else:
            # Default → weekly granularity
            plan.granularity = "weekly"
    
    # Ensure chart type matches intent - trends should use line charts
    chart_mapping = {
        "trend": "line",
        "variance": "line",  # Changed from grouped_bar to line for better trend visualization
        "forecast_vs_actual": "grouped_bar",
        "forecast_gap_analysis": "waterfall",  # Variance decomposition
        "funnel": "funnel",
        "distribution": "pie",
        "relationship": "scatter",
        "multi_metric": "line",  # Multiple lines on same chart
        "explain": "line"  # Default, though explain queries don't use charts
    }
    
    if plan.intent in chart_mapping:
        plan.chart = chart_mapping[plan.intent]
    
    # Ensure table selection is correct
    if plan.intent in ["forecast_vs_actual", "forecast_gap_analysis"]:
        plan.table = "forecast_df"
        plan.date_col = "date"
    else:
        plan.table = "cps_tb"
    
    # Ensure metrics default to amounts (not counts) for trend queries
    if plan.intent in ["trend", "variance"] and "_count" in plan.metric:
        # Replace count metrics with amount metrics unless explicitly requested
        if "number" not in user_query_lower and "count" not in user_query_lower:
            plan.metric = plan.metric.replace("_count", "_amnt")
    
    return plan


def _validate_plan(plan: Plan) -> Plan:
    """
    Validate the plan for consistency and correctness.
    
    Args:
        plan: Plan to validate
        
    Returns:
        Plan: Validated plan
        
    Raises:
        ValueError: If validation fails
    """
    # Validate table and date_col consistency
    if plan.table == "forecast_df" and plan.date_col != "date":
        logger.warning(
            f"Invalid date_col '{plan.date_col}' for forecast_df table, correcting to 'date'"
        )
        plan.date_col = "date"
    
    if plan.table == "cps_tb" and plan.date_col == "date":
        logger.warning(
            f"Invalid date_col 'date' for cps_tb table, correcting to 'app_submit_d'"
        )
        plan.date_col = "app_submit_d"
    
    # Validate metric for forecast queries
    # Note: forecast_gap_analysis uses regular metrics (issued_amnt, etc.) not forecast columns
    if plan.intent == "forecast_vs_actual":
        if "forecast" not in plan.metric.lower() and "actual" not in plan.metric.lower():
            logger.warning(
                f"Forecast query should use forecast/actual metrics, got '{plan.metric}'"
            )
            # Default to issuance for forecast queries
            plan.metric = "issued_amnt"
    
    return plan


def _validate_plan(plan: Plan) -> Plan:
    """
    Validate the plan for consistency and correctness.
    
    Args:
        plan: Plan to validate
        
    Returns:
        Plan: Validated plan
        
    Raises:
        ValueError: If validation fails
    """
    # Validate table and date_col consistency
    if plan.table == "forecast_df" and plan.date_col != "date":
        logger.warning(
            f"Invalid date_col '{plan.date_col}' for forecast_df table, correcting to 'date'"
        )
        plan.date_col = "date"
    
    if plan.table == "cps_tb" and plan.date_col == "date":
        logger.warning(
            f"Invalid date_col 'date' for cps_tb table, correcting to 'app_submit_d'"
        )
        plan.date_col = "app_submit_d"
    
    # Validate metric for forecast queries
    # Note: forecast_gap_analysis uses regular metrics (issued_amnt, etc.) not forecast columns
    if plan.intent == "forecast_vs_actual":
        if "forecast" not in plan.metric.lower() and "actual" not in plan.metric.lower():
            logger.warning(
                f"Forecast query should use forecast/actual metrics, got '{plan.metric}'"
            )
            # Default to issuance for forecast queries
            plan.metric = "issued_amnt"
    
    return plan


def make_plan(user_query: str, intent: str, conversation_history: Optional[List[Dict]] = None) -> Plan:
    """
    Generate a structured query plan from user query and intent with conversation context.
    
    Args:
        user_query: Natural language query from user
        intent: Classified intent from router
        conversation_history: List of previous messages for context
        
    Returns:
        Plan: Structured query plan
        
    Raises:
        ValueError: If plan generation fails
    """
    logger.info(f"Generating plan for intent: {intent}")
    
    try:
        client = _get_client()
        
        # Extract context from conversation history
        context_info = ""
        if conversation_history:
            last_plan = _extract_last_plan(conversation_history)
            if last_plan:
                context_info = f"""

Previous Query Context:
- Intent: {last_plan.get('intent', 'N/A')}
- Metric: {last_plan.get('metric', 'N/A')}
- Time Window: {last_plan.get('window', 'N/A')}
- Segments: {last_plan.get('segments', 'N/A')}
- Chart Type: {last_plan.get('chart', 'N/A')}

Use this context to infer missing parameters in the current query. For example:
- If user says "what about for X?" and previous intent was "funnel", keep intent="funnel" and change the segment
- If user says "what about last quarter?" and previous metric was "issuances", use metric="issued_amnt"
- If user says "show me by channel" and previous query had specific metrics, keep those metrics
- If user says "that" or "it", refer to the previous query's parameters
- IMPORTANT: If the previous query was a funnel/distribution/forecast, preserve that intent unless explicitly changed"""
        
        user_message = f"User Query: {user_query}\nClassified Intent: {intent}{context_info}"
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=300
        )
        
        content = response.choices[0].message.content
        plan_dict = json.loads(content)
        
        # Create Plan object
        plan = Plan(**plan_dict)
        
        # Apply default rules and validation
        plan = _apply_default_rules(plan, user_query)
        plan = _validate_plan(plan)
        
        logger.info(f"Plan generated successfully: {plan.model_dump()}")
        return plan
        
    except Exception as e:
        logger.error(f"Failed to generate plan: {str(e)}")
        raise ValueError(f"Could not generate query plan: {str(e)}")


def _extract_last_plan(conversation_history: List[Dict]) -> Optional[Dict]:
    """
    Extract the last query plan from conversation history.
    
    Args:
        conversation_history: List of conversation messages
        
    Returns:
        Dict with last plan parameters or None
    """
    # Look for assistant messages that might contain plan info
    for msg in reversed(conversation_history):
        if msg.get('role') == 'assistant':
            content = msg.get('content', '')
            # Try to extract plan info from content
            # This is a simple heuristic - in production, you'd store plan in message metadata
            if 'plan' in msg:
                return msg['plan']
            
            # Try to infer from content patterns
            plan_hints = {}
            
            # Look for intent hints in content
            if 'funnel' in content.lower() or 'conversion' in content.lower():
                plan_hints['intent'] = 'funnel'
                plan_hints['chart'] = 'funnel'
            # Check for forecast gap analysis BEFORE general forecast queries
            elif any(keyword in content.lower() for keyword in ['forecast gap', 'gap analysis', 'variance decomposition', 'driving the forecast', 'largest gap', 'biggest gap', 'forecast miss', 'forecast variance']):
                plan_hints['intent'] = 'forecast_gap_analysis'
                plan_hints['chart'] = 'waterfall'
            elif 'forecast' in content.lower() or 'vs actual' in content.lower():
                plan_hints['intent'] = 'forecast_vs_actual'
            elif 'breakdown' in content.lower() or 'distribution' in content.lower():
                plan_hints['intent'] = 'distribution'
            
            # Look for metric hints in content
            if 'issuance' in content.lower() or 'issued' in content.lower():
                plan_hints['metric'] = 'issued_amnt'
            elif 'approval' in content.lower() or 'approved' in content.lower():
                plan_hints['metric'] = 'apps_approved_amnt'
            elif 'submit' in content.lower() or 'application' in content.lower():
                plan_hints['metric'] = 'app_submit_amnt'
            
            # Look for time window hints
            if 'last quarter' in content.lower() or 'quarter' in content.lower():
                plan_hints['window'] = 'last_full_quarter'
            elif 'last month' in content.lower():
                plan_hints['window'] = 'last_full_month'
            elif 'last week' in content.lower():
                plan_hints['window'] = 'last_full_week'
            
            if plan_hints:
                return plan_hints
    
    return None
