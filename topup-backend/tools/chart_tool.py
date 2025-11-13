"""
Chart Tool for Plotly specification generation.

This module generates Plotly JSON specifications for various chart types
based on query plans and data results. Supports theme-aware colors,
FICO band sorting, and annotations for trend charts.
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from models.schemas import Plan


# FICO band sort order for categorical axes
FICO_BAND_ORDER = ["<640", "640-699", "700-759", "760+"]

# Theme-aware color palettes
COLORS_LIGHT = {
    "primary": "#2563eb",  # Blue
    "secondary": "#7c3aed",  # Purple
    "success": "#059669",  # Green
    "warning": "#d97706",  # Orange
    "danger": "#dc2626",  # Red
    "series": [
        "#2563eb", "#7c3aed", "#059669", "#d97706", "#dc2626",
        "#0891b2", "#db2777", "#65a30d", "#ea580c", "#4f46e5"
    ],
    "background": "#ffffff",
    "paper": "#f9fafb",
    "text": "#111827",
    "grid": "#e5e7eb"
}

COLORS_DARK = {
    "primary": "#60a5fa",  # Light Blue
    "secondary": "#a78bfa",  # Light Purple
    "success": "#34d399",  # Light Green
    "warning": "#fbbf24",  # Light Orange
    "danger": "#f87171",  # Light Red
    "series": [
        "#60a5fa", "#a78bfa", "#34d399", "#fbbf24", "#f87171",
        "#22d3ee", "#f472b6", "#a3e635", "#fb923c", "#818cf8"
    ],
    "background": "#111827",
    "paper": "#1f2937",
    "text": "#f9fafb",
    "grid": "#374151"
}


def build(plan: Plan, df: pd.DataFrame, theme: str = "light") -> Dict[str, Any]:
    """
    Generate Plotly JSON specification based on query plan and data.
    
    Args:
        plan: Query plan with intent, metric, and chart type
        df: Query results as pandas DataFrame
        theme: Color theme ("light" or "dark")
    
    Returns:
        dict: Plotly JSON specification
    
    Raises:
        ValueError: If chart type is not supported or data is invalid
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Building chart for intent: {plan.intent}, chart type: {plan.chart}, metric: {plan.metric}")
    logger.info(f"DataFrame columns: {df.columns.tolist()}")
    
    if df.empty:
        return _empty_chart(theme)
    
    # Select chart builder based on intent (check multi_metric FIRST before chart type)
    if plan.intent == "multi_metric":
        logger.info("Using _build_multi_metric_chart")
        return _build_multi_metric_chart(plan, df, theme)
    elif plan.intent == "forecast_gap_analysis" or plan.chart == "waterfall":
        logger.info("Using _build_waterfall_chart")
        return _build_waterfall_chart(plan, df, theme)
    elif plan.intent == "trend" or plan.chart in ["line", "area"]:
        logger.info("Using _build_trend_chart")
        return _build_trend_chart(plan, df, theme)
    elif plan.intent == "forecast_vs_actual" or plan.chart == "grouped_bar":
        return _build_forecast_chart(plan, df, theme)
    elif plan.intent == "funnel" or plan.chart == "funnel":
        return _build_funnel_chart(plan, df, theme)
    elif plan.intent == "distribution" or plan.chart == "pie":
        return _build_pie_chart(plan, df, theme)
    elif plan.intent == "relationship" or plan.chart == "scatter":
        return _build_scatter_chart(plan, df, theme)
    else:
        # Default to bar chart
        return _build_bar_chart(plan, df, theme)


def _build_trend_chart(plan: Plan, df: pd.DataFrame, theme: str) -> Dict[str, Any]:
    """
    Build line or area chart for trend analysis.
    
    Adds annotations for the last two periods to highlight recent values.
    """
    colors = COLORS_DARK if theme == "dark" else COLORS_LIGHT
    
    # Identify time column (first column is typically the time dimension)
    time_col = df.columns[0]
    
    # Get value columns - filter out metadata/helper columns
    # For trend charts, we want to plot the actual metric, not helper columns
    all_cols = df.columns[1:].tolist()
    
    # Filter out known metadata columns that shouldn't be plotted
    metadata_cols = ['week_start', 'month_start', 'quarter_start', 'year_start', 'record_count']
    value_cols = [col for col in all_cols if col not in metadata_cols]
    
    # If no value columns found after filtering, default to metric_value
    if not value_cols:
        if 'metric_value' in all_cols:
            value_cols = ['metric_value']
        else:
            value_cols = [all_cols[0]] if all_cols else []
    
    # Sort by FICO band if present
    df = _sort_by_fico_if_present(df, time_col)
    
    # Create traces
    traces = []
    for idx, col in enumerate(value_cols):
        color = colors["series"][idx % len(colors["series"])]
        
        # Format legend name to be human-readable
        legend_name = _format_label(col)
        
        trace = {
            "x": df[time_col].tolist(),
            "y": df[col].tolist(),
            "type": "scatter",
            "mode": "lines+markers",
            "name": legend_name,
            "line": {"color": color, "width": 2},
            "marker": {"size": 6, "color": color},
            "hovertemplate": f"<b>{legend_name}</b><br>%{{x}}<br>%{{y:,.0f}}<extra></extra>"
        }
        
        if plan.chart == "area":
            trace["fill"] = "tonexty" if idx > 0 else "tozeroy"
            trace["fillcolor"] = color + "40"  # Add transparency
        
        traces.append(trace)
    
    # Add annotations for last two periods (only for first series)
    annotations = []
    if len(df) >= 2 and len(value_cols) > 0:
        col = value_cols[0]
        for i in range(-2, 0):
            value = df[col].iloc[i]
            # Format text based on value type
            if isinstance(value, (int, float)):
                text = f"${value:,.0f}" if "amnt" in col.lower() or "amt" in col.lower() else f"{value:,.0f}"
            else:
                text = str(value)
            
            annotations.append({
                "x": df[time_col].iloc[i],
                "y": df[col].iloc[i],
                "text": text,
                "showarrow": True,
                "arrowhead": 2,
                "arrowsize": 1,
                "arrowwidth": 1,
                "arrowcolor": colors["text"],
                "ax": 0,
                "ay": -30,
                "font": {"size": 10, "color": colors["text"]},
                "bgcolor": colors["paper"],
                "bordercolor": colors["grid"],
                "borderwidth": 1,
                "borderpad": 4
            })
    
    layout = _base_layout(plan, theme)
    layout["annotations"] = annotations
    layout["xaxis"]["title"] = _format_label(time_col)
    layout["yaxis"]["title"] = _format_label(plan.metric)
    
    return {"data": traces, "layout": layout}


def _build_multi_metric_chart(plan: Plan, df: pd.DataFrame, theme: str) -> Dict[str, Any]:
    """
    Build multi-line chart for comparing multiple metrics.
    
    Shows ONLY the requested metrics based on plan.metric (comma-separated list).
    """
    import logging
    logger = logging.getLogger(__name__)
    
    colors = COLORS_DARK if theme == "dark" else COLORS_LIGHT
    
    # Identify time column (first column)
    time_col = df.columns[0]
    
    # Parse which metrics to display from plan.metric (comma-separated)
    requested_metrics = [m.strip() for m in plan.metric.split(',')]
    
    logger.info(f"Building multi-metric chart. Requested metrics: {requested_metrics}")
    logger.info(f"Available columns in dataframe: {df.columns.tolist()}")
    
    # Map metric names to display names and colors
    metric_display_map = {
        "app_submit_amnt": ("App Submits ($)", colors["series"][0]),
        "app_submit_count": ("App Submits (Count)", colors["series"][0]),
        "apps_approved_amnt": ("Approvals ($)", colors["series"][1]),
        "apps_approved_count": ("Approvals (Count)", colors["series"][1]),
        "issued_amnt": ("Issuances ($)", colors["series"][2]),
        "issued_count": ("Issuances (Count)", colors["series"][2])
    }
    
    # Create traces ONLY for the requested metrics that exist in the dataframe
    traces = []
    for idx, metric_col in enumerate(requested_metrics):
        # Skip if this column doesn't exist in the dataframe
        if metric_col not in df.columns:
            continue
        
        # Get display name and color
        display_name, color = metric_display_map.get(
            metric_col, 
            (_format_label(metric_col), colors["series"][idx % len(colors["series"])])
        )
        
        # Determine if this is a currency value
        is_currency = "amnt" in metric_col or "amt" in metric_col
        
        trace = {
            "x": df[time_col].tolist(),
            "y": df[metric_col].tolist(),
            "type": "scatter",
            "mode": "lines+markers",
            "name": display_name,
            "line": {"color": color, "width": 2},
            "marker": {"size": 6, "color": color},
            "hovertemplate": f"<b>{display_name}</b><br>%{{x}}<br>{'$' if is_currency else ''}%{{y:,.0f}}<extra></extra>"
        }
        traces.append(trace)
    
    logger.info(f"Created {len(traces)} traces for metrics: {[t['name'] for t in traces]}")
    
    layout = _base_layout(plan, theme)
    layout["xaxis"]["title"] = _format_label(time_col)
    
    # Set y-axis title based on metric type
    if requested_metrics and "count" in requested_metrics[0].lower():
        layout["yaxis"]["title"] = "Count"
    else:
        layout["yaxis"]["title"] = "Amount ($)"
    
    # Title is already set by _base_layout with time window context
    # Just update it to include metric names if we have multiple traces
    if len(traces) > 1:
        metric_names = [trace["name"] for trace in traces]
        # Extract window from existing title
        existing_title = layout["title"]["text"]
        if "(" in existing_title:
            window_part = existing_title[existing_title.index("("):]
            layout["title"]["text"] = f"{' vs '.join(metric_names)} Comparison {window_part}"
    # For single trace or no traces, keep the default title from _base_layout
    
    return {"data": traces, "layout": layout}


def _build_waterfall_chart(plan: Plan, df: pd.DataFrame, theme: str) -> Dict[str, Any]:
    """
    Build waterfall chart for forecast variance decomposition.
    
    Shows how different segments contribute to the overall forecast gap as percentages.
    """
    colors = COLORS_DARK if theme == "dark" else COLORS_LIGHT
    
    # Filter out the OVERALL row for the waterfall segments
    segments_df = df[df['dimension'] != 'OVERALL'].copy()
    overall_row = df[df['dimension'] == 'OVERALL'].iloc[0] if len(df[df['dimension'] == 'OVERALL']) > 0 else None
    
    # Build x-axis labels (dimension: value)
    x_labels = [f"{row['dimension']}: {row['segment_value']}" for _, row in segments_df.iterrows()]
    
    # Use contribution percentages for the waterfall
    # Start at 0%, each segment adds/subtracts its contribution, end at 100%
    if overall_row is not None:
        x_labels = ['Start (0%)'] + x_labels + ['Total (100%)']
        # Use contribution_pct for each segment
        y_values = [0] + segments_df['contribution_pct'].tolist() + [100]
        
        # Measure types: absolute for start/end, relative for segments
        measures = ['absolute'] + ['relative'] * len(segments_df) + ['total']
        
        # Format text labels with percentage and absolute value
        text_labels = ['0%']
        for _, row in segments_df.iterrows():
            text_labels.append(f"{row['contribution_pct']:+.1f}%<br>({row['delta']:+,.0f})")
        text_labels.append('100%')
    else:
        # Fallback if no overall row
        x_labels = x_labels
        y_values = segments_df['contribution_pct'].tolist()
        measures = ['relative'] * len(segments_df)
        text_labels = [f"{v:+.1f}%" for v in y_values]
    
    # Create waterfall trace
    trace = {
        "type": "waterfall",
        "x": x_labels,
        "y": y_values,
        "measure": measures,
        "text": text_labels,
        "textposition": "outside",
        "connector": {
            "line": {
                "color": colors["grid"],
                "width": 2,
                "dash": "dot"
            }
        },
        "increasing": {"marker": {"color": colors["success"]}},
        "decreasing": {"marker": {"color": colors["danger"]}},
        "totals": {"marker": {"color": colors["primary"]}}
    }
    
    # Build layout
    layout = _base_layout(plan, theme)
    layout["xaxis"]["title"] = "Segment"
    layout["yaxis"]["title"] = "Contribution to Total Variance (%)"
    layout["yaxis"]["ticksuffix"] = "%"
    layout["title"]["text"] = f"Forecast Gap Analysis: {plan.metric.replace('_', ' ').title()}"
    
    # Add subtitle with overall variance if available
    if overall_row is not None:
        variance_pct = overall_row['delta_pct']
        variance_abs = overall_row['delta']
        layout["title"]["text"] += f"<br><sub>Total Variance: {variance_abs:,.0f} ({variance_pct:+.1f}%)</sub>"
    
    return {"data": [trace], "layout": layout}


def _build_forecast_chart(plan: Plan, df: pd.DataFrame, theme: str) -> Dict[str, Any]:
    """
    Build grouped bar chart for forecast vs actual comparison.
    
    Handles two cases:
    1. Time-based: forecast vs actual over time (week/month)
    2. Segment-based: forecast vs actual by segment (grade/channel) with multiple metrics
    """
    colors = COLORS_DARK if theme == "dark" else COLORS_LIGHT
    
    # Identify first column (time or segment)
    x_col = df.columns[0]
    
    # Sort by FICO band if present
    df = _sort_by_fico_if_present(df, x_col)
    
    traces = []
    
    # Check if this is a by-segment query (has multiple metric pairs)
    # Look for patterns like forecast_app_submits, forecast_apps_approved, forecast_issuance
    metric_types = []
    if "forecast_app_submits" in df.columns:
        metric_types.append(("app_submits", "App Submits"))
    if "forecast_apps_approved" in df.columns:
        metric_types.append(("apps_approved", "Apps Approved"))
    if "forecast_issuance" in df.columns:
        metric_types.append(("issuance", "Issuance"))
    
    if metric_types:
        # By-segment chart with multiple metrics
        for idx, (metric_key, metric_label) in enumerate(metric_types):
            forecast_col = f"forecast_{metric_key}"
            actual_col = f"actual_{metric_key}"
            
            # Use different colors for each metric pair
            forecast_color = colors["series"][idx * 2 % len(colors["series"])]
            actual_color = colors["series"][(idx * 2 + 1) % len(colors["series"])]
            
            traces.append({
                "x": df[x_col].tolist(),
                "y": df[forecast_col].tolist(),
                "type": "bar",
                "name": f"Forecast {metric_label}",
                "marker": {"color": forecast_color},
                "hovertemplate": f"<b>Forecast {metric_label}</b><br>%{{x}}<br>%{{y:,.0f}}<extra></extra>"
            })
            
            traces.append({
                "x": df[x_col].tolist(),
                "y": df[actual_col].tolist(),
                "type": "bar",
                "name": f"Actual {metric_label}",
                "marker": {"color": actual_color},
                "hovertemplate": f"<b>Actual {metric_label}</b><br>%{{x}}<br>%{{y:,.0f}}<extra></extra>"
            })
    else:
        # Time-based chart with single metric
        forecast_cols = [col for col in df.columns if "forecast" in col.lower() and "accuracy" not in col.lower() and "delta" not in col.lower()]
        actual_cols = [col for col in df.columns if "actual" in col.lower() and "accuracy" not in col.lower() and "delta" not in col.lower()]
        
        # Create forecast trace
        if forecast_cols:
            traces.append({
                "x": df[x_col].tolist(),
                "y": df[forecast_cols[0]].tolist(),
                "type": "bar",
                "name": "Forecast",
                "marker": {"color": colors["secondary"]},
                "hovertemplate": "<b>Forecast</b><br>%{x}<br>%{y:,.0f}<extra></extra>"
            })
        
        # Create actual trace
        if actual_cols:
            traces.append({
                "x": df[x_col].tolist(),
                "y": df[actual_cols[0]].tolist(),
                "type": "bar",
                "name": "Actual",
                "marker": {"color": colors["primary"]},
                "hovertemplate": "<b>Actual</b><br>%{x}<br>%{y:,.0f}<extra></extra>"
            })
    
    layout = _base_layout(plan, theme)
    layout["barmode"] = "group"
    layout["xaxis"]["title"] = _format_label(x_col)
    layout["yaxis"]["title"] = "Value"
    
    return {"data": traces, "layout": layout}


def _build_funnel_chart(plan: Plan, df: pd.DataFrame, theme: str) -> Dict[str, Any]:
    """
    Build funnel chart for conversion analysis.
    
    Expects data with stage names and values.
    The data should already be in the correct funnel order (top to bottom).
    """
    colors = COLORS_DARK if theme == "dark" else COLORS_LIGHT
    
    # Identify stage and value columns
    stage_col = df.columns[0]
    
    # Look for stage_order column if present, otherwise use first numeric column
    if "stage_order" in df.columns:
        # Sort by stage_order to maintain funnel flow
        df_sorted = df.sort_values("stage_order")
        # Use value_amt if present, otherwise second column
        value_col = "value_amt" if "value_amt" in df.columns else df.columns[1]
    else:
        # Fallback: assume data is already in correct order or sort by value descending
        value_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
        df_sorted = df.copy()
    
    trace = {
        "type": "funnel",
        "y": df_sorted[stage_col].tolist(),
        "x": df_sorted[value_col].tolist(),
        "textinfo": "value+percent initial",
        "marker": {
            "color": colors["series"][:len(df_sorted)]
        },
        "hovertemplate": "<b>%{y}</b><br>%{x:,.0f}<br>%{percentInitial}<extra></extra>"
    }
    
    layout = _base_layout(plan, theme)
    layout["yaxis"]["title"] = ""
    layout["xaxis"]["title"] = _format_label(plan.metric)
    # Increase left margin for funnel charts to accommodate stage labels
    layout["margin"] = {"l": 120, "r": 40, "t": 60, "b": 60}
    
    return {"data": [trace], "layout": layout}


def _build_pie_chart(plan: Plan, df: pd.DataFrame, theme: str) -> Dict[str, Any]:
    """
    Build pie chart for distribution analysis.
    """
    colors = COLORS_DARK if theme == "dark" else COLORS_LIGHT
    
    # Identify label and value columns
    label_col = df.columns[0]
    value_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
    
    # Sort by FICO band if present
    df = _sort_by_fico_if_present(df, label_col)
    
    trace = {
        "type": "pie",
        "labels": df[label_col].tolist(),
        "values": df[value_col].tolist(),
        "marker": {
            "colors": colors["series"]
        },
        "textinfo": "label+percent",
        "hovertemplate": "<b>%{label}</b><br>%{value:,.0f}<br>%{percent}<extra></extra>"
    }
    
    layout = _base_layout(plan, theme)
    
    return {"data": [trace], "layout": layout}


def _build_scatter_chart(plan: Plan, df: pd.DataFrame, theme: str) -> Dict[str, Any]:
    """
    Build scatter chart for relationship analysis.
    """
    colors = COLORS_DARK if theme == "dark" else COLORS_LIGHT
    
    # Identify x and y columns
    x_col = df.columns[0]
    y_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
    
    # Check if there's a grouping column (3rd column)
    group_col = df.columns[2] if len(df.columns) > 2 else None
    
    traces = []
    
    if group_col:
        # Create separate traces for each group
        for idx, group in enumerate(df[group_col].unique()):
            df_group = df[df[group_col] == group]
            color = colors["series"][idx % len(colors["series"])]
            
            traces.append({
                "x": df_group[x_col].tolist(),
                "y": df_group[y_col].tolist(),
                "type": "scatter",
                "mode": "markers",
                "name": str(group),
                "marker": {"size": 8, "color": color},
                "hovertemplate": f"<b>{group}</b><br>{x_col}: %{{x:,.0f}}<br>{y_col}: %{{y:,.0f}}<extra></extra>"
            })
    else:
        # Single scatter trace
        traces.append({
            "x": df[x_col].tolist(),
            "y": df[y_col].tolist(),
            "type": "scatter",
            "mode": "markers",
            "marker": {"size": 8, "color": colors["primary"]},
            "hovertemplate": f"{x_col}: %{{x:,.0f}}<br>{y_col}: %{{y:,.0f}}<extra></extra>"
        })
    
    layout = _base_layout(plan, theme)
    layout["xaxis"]["title"] = _format_label(x_col)
    layout["yaxis"]["title"] = _format_label(y_col)
    
    return {"data": traces, "layout": layout}


def _build_bar_chart(plan: Plan, df: pd.DataFrame, theme: str) -> Dict[str, Any]:
    """
    Build simple bar chart (fallback).
    """
    colors = COLORS_DARK if theme == "dark" else COLORS_LIGHT
    
    # Identify columns
    label_col = df.columns[0]
    value_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
    
    # Sort by FICO band if present
    df = _sort_by_fico_if_present(df, label_col)
    
    trace = {
        "x": df[label_col].tolist(),
        "y": df[value_col].tolist(),
        "type": "bar",
        "marker": {"color": colors["primary"]},
        "hovertemplate": "<b>%{x}</b><br>%{y:,.0f}<extra></extra>"
    }
    
    layout = _base_layout(plan, theme)
    layout["xaxis"]["title"] = _format_label(label_col)
    layout["yaxis"]["title"] = _format_label(value_col)
    
    return {"data": [trace], "layout": layout}


def _base_layout(plan: Plan, theme: str) -> Dict[str, Any]:
    """
    Generate base layout configuration with theme-aware colors.
    """
    colors = COLORS_DARK if theme == "dark" else COLORS_LIGHT
    
    return {
        "template": "plotly_dark" if theme == "dark" else "plotly_white",
        "plot_bgcolor": colors["background"],
        "paper_bgcolor": colors["paper"],
        "font": {"color": colors["text"], "family": "Inter, sans-serif"},
        "title": {
            "text": _generate_title(plan),
            "font": {"size": 16, "color": colors["text"]},
            "x": 0.5,
            "xanchor": "center"
        },
        "xaxis": {
            "gridcolor": colors["grid"],
            "linecolor": colors["grid"],
            "tickfont": {"color": colors["text"]}
        },
        "yaxis": {
            "gridcolor": colors["grid"],
            "linecolor": colors["grid"],
            "tickfont": {"color": colors["text"]}
        },
        "legend": {
            "font": {"color": colors["text"]},
            "bgcolor": colors["paper"],
            "bordercolor": colors["grid"],
            "borderwidth": 1
        },
        "hovermode": "closest",
        "margin": {"l": 60, "r": 40, "t": 60, "b": 60}
    }


def _generate_title(plan: Plan) -> str:
    """
    Generate chart title from plan with time window context.
    """
    metric_name = _format_label(plan.metric)
    
    # Format window name to be more readable
    window_mapping = {
        "last_7d": "Last 7 Days",
        "last_full_week": "Last Week",
        "last_30d": "Last 30 Days",
        "last_full_month": "Last Month",
        "last_3_full_months": "Last 3 Months",
        "last_full_quarter": "Last Quarter",
        "last_full_year": "Last Year",
        "qtd": "Quarter to Date",
        "mtd": "Month to Date",
        "ytd": "Year to Date",
    }
    window_name = window_mapping.get(plan.window, plan.window.replace("_", " ").title())
    
    # Format granularity
    granularity_name = plan.granularity.title()
    
    # Generate title with time window context
    if plan.intent == "trend":
        return f"{granularity_name} {metric_name} Trend ({window_name})"
    elif plan.intent == "multi_metric":
        return f"{metric_name} Comparison ({window_name})"
    elif plan.intent == "variance":
        return f"{metric_name} - {window_name}"
    elif plan.intent == "forecast_vs_actual":
        return f"Forecast vs Actual: {metric_name} ({window_name})"
    elif plan.intent == "funnel":
        return f"Conversion Funnel ({window_name})"
    elif plan.intent == "distribution":
        return f"{metric_name} Distribution ({window_name})"
    elif plan.intent == "relationship":
        return f"{metric_name} Relationship ({window_name})"
    else:
        return f"{metric_name} ({window_name})"


def _format_label(label: str) -> str:
    """
    Format column names and labels to be human-readable.
    
    Args:
        label: Raw column name or label
        
    Returns:
        str: Human-readable formatted label
    """
    # Handle common abbreviations and patterns
    replacements = {
        "amnt": "Amount",
        "amt": "Amount",
        "app_submit": "App Submits",
        "apps_approved": "Approvals",
        "issued": "Issuances",
        "cr_fico": "FICO Score",
        "cr_fico_band": "FICO Band",
        "cr_dti": "DTI",
        "a_income": "Income",
        "offer_apr": "APR",
        "prod_type": "Product Type",
        "repeat_type": "Customer Type",
        "_d": " Date",
        "_": " ",
    }
    
    formatted = label
    for old, new in replacements.items():
        formatted = formatted.replace(old, new)
    
    # Title case and clean up
    formatted = formatted.strip().title()
    
    # Remove duplicate spaces
    formatted = " ".join(formatted.split())
    
    return formatted


def _sort_by_fico_if_present(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """
    Sort DataFrame by FICO band order if the column contains FICO bands.
    
    Args:
        df: DataFrame to sort
        col: Column name to check for FICO bands
    
    Returns:
        pd.DataFrame: Sorted DataFrame (or original if no FICO bands)
    """
    if "fico" in col.lower() or "cr_fico_band" in col.lower():
        # Check if values match FICO band pattern
        values = df[col].unique()
        if any(val in FICO_BAND_ORDER for val in values):
            # Create categorical with specified order
            df = df.copy()
            df[col] = pd.Categorical(
                df[col],
                categories=FICO_BAND_ORDER,
                ordered=True
            )
            df = df.sort_values(col)
    
    return df


def _empty_chart(theme: str) -> Dict[str, Any]:
    """
    Generate empty chart placeholder.
    """
    colors = COLORS_DARK if theme == "dark" else COLORS_LIGHT
    
    return {
        "data": [],
        "layout": {
            "template": "plotly_dark" if theme == "dark" else "plotly_white",
            "plot_bgcolor": colors["background"],
            "paper_bgcolor": colors["paper"],
            "font": {"color": colors["text"]},
            "title": {
                "text": "No data available",
                "font": {"size": 16, "color": colors["text"]},
                "x": 0.5,
                "xanchor": "center"
            },
            "xaxis": {"visible": False},
            "yaxis": {"visible": False},
            "annotations": [{
                "text": "No data to display",
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"size": 14, "color": colors["text"]}
            }]
        }
    }
