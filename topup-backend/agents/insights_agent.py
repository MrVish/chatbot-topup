"""
Insights Agent for narrative generation and variance analysis.

This module provides the Insights Agent that generates executive-level
summaries, key findings, and segment drivers from query results. It handles:
- MoM and WoW percentage delta calculations
- Top positive and negative segment driver identification
- Forecast accuracy metrics
- Funnel conversion rate analysis
- Executive summary generation
- Bullet point key findings
"""

import logging
import os
from typing import List

import pandas as pd
from openai import OpenAI

from models.schemas import Driver, Insight, Plan

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


def _format_number(value: float, is_currency: bool = False, is_percentage: bool = False) -> str:
    """
    Format number for display in insights.
    
    Args:
        value: Numeric value to format
        is_currency: Whether to format as currency
        is_percentage: Whether to format as percentage
        
    Returns:
        Formatted string
    """
    if pd.isna(value):
        return "N/A"
    
    if is_percentage:
        return f"{value:+.1f}%"
    elif is_currency:
        if abs(value) >= 1_000_000:
            return f"${value/1_000_000:.1f}M"
        elif abs(value) >= 1_000:
            return f"${value/1_000:.1f}K"
        else:
            return f"${value:,.0f}"
    else:
        if abs(value) >= 1_000_000:
            return f"{value/1_000_000:.1f}M"
        elif abs(value) >= 1_000:
            return f"{value/1_000:.1f}K"
        else:
            return f"{value:,.0f}"


def _is_currency_metric(metric: str) -> bool:
    """Check if metric represents currency values."""
    currency_keywords = ["amt", "amnt", "amount", "apr", "income"]
    return any(keyword in metric.lower() for keyword in currency_keywords)


def _is_percentage_metric(metric: str) -> bool:
    """Check if metric represents percentage values."""
    percentage_keywords = ["rate", "pct", "percent", "accuracy"]
    return any(keyword in metric.lower() for keyword in percentage_keywords)


def _generate_llm_insights(plan: Plan, df: pd.DataFrame, statistical_summary: dict) -> dict:
    """
    Use LLM to generate executive-level insights from data and statistical analysis.
    
    Args:
        plan: Query plan with context
        df: DataFrame with query results
        statistical_summary: Dict with pre-calculated statistics (anomalies, trends, etc.)
        
    Returns:
        dict with 'summary' and 'bullets' keys
    """
    try:
        client = _get_client()
        
        # Prepare data summary for LLM (limit to avoid token overflow)
        data_summary = df.head(20).to_dict('records') if len(df) <= 20 else {
            "first_5": df.head(5).to_dict('records'),
            "last_5": df.tail(5).to_dict('records'),
            "total_rows": len(df)
        }
        
        # Create prompt for LLM
        prompt = f"""You are an executive business analyst providing insights for a CXO dashboard.

**Context:**
- Query Intent: {plan.intent}
- Metric: {plan.metric}
- Time Window: {plan.window}
- Granularity: {plan.granularity}

**Data Summary:**
{data_summary}

**Statistical Analysis:**
{statistical_summary}

**Your Task:**
Generate executive-level insights that are:
1. **Actionable** - Focus on what matters and what to do about it
2. **Prioritized** - Lead with problems/anomalies, then opportunities
3. **Concise** - One summary sentence and 2-3 bullet points
4. **Executive-friendly** - Use business language, not technical jargon

**Format your response as JSON:**
{{
    "summary": "One executive summary sentence (max 150 chars) - use ⚠️ for concerns, ✓ for positive",
    "bullets": [
        "First bullet - most important finding",
        "Second bullet - supporting insight or trend",
        "Third bullet - actionable recommendation (start with →)"
    ]
}}

**Guidelines:**
- Prioritize negative trends and anomalies first
- Use specific numbers and percentages
- Include period references when relevant
- End with an actionable recommendation
- Keep each bullet under 100 characters"""

        # Call OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert business analyst providing executive insights. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,  # Lower temperature for more consistent, factual insights
            max_tokens=300
        )
        
        # Parse response
        import json
        content = response.choices[0].message.content
        insights = json.loads(content)
        
        logger.info("LLM insights generated successfully")
        return insights
        
    except Exception as e:
        logger.error(f"Failed to generate LLM insights: {str(e)}")
        # Return fallback
        return {
            "summary": statistical_summary.get("summary", "Analysis complete"),
            "bullets": statistical_summary.get("bullets", ["Data analyzed successfully"])
        }


def _calculate_variance_insights(plan: Plan, df: pd.DataFrame) -> Insight:
    """
    Generate insights for variance queries (MoM/WoW).
    
    Args:
        plan: Query plan
        df: DataFrame with columns: week/month, current_value, prior_value, delta, delta_pct
        
    Returns:
        Insight object with variance analysis
    """
    if df.empty:
        return Insight(
            title="Variance Analysis",
            summary="No data available for the selected period.",
            bullets=["No variance data to analyze."],
            drivers=[]
        )
    
    # Get most recent period
    latest = df.iloc[0]  # Already sorted DESC in SQL
    current_value = latest.get("current_value", 0)
    prior_value = latest.get("prior_week_value") or latest.get("prior_month_value", 0)
    delta = latest.get("delta", 0)
    delta_pct = latest.get("delta_pct", 0)
    
    # Determine if currency or percentage
    is_currency = _is_currency_metric(plan.metric)
    is_percentage = _is_percentage_metric(plan.metric)
    
    # Format values
    current_str = _format_number(current_value, is_currency, is_percentage)
    prior_str = _format_number(prior_value, is_currency, is_percentage)
    delta_str = _format_number(delta, is_currency, False)
    delta_pct_str = _format_number(delta_pct, False, True)
    
    # Determine period type
    period_type = "week" if "week" in df.columns[0].lower() else "month"
    
    # Generate executive summary - prioritize negative trends
    metric_name = plan.metric.replace('_', ' ').replace('amnt', '').replace('amt', '').title().strip()
    period_type_cap = period_type.title()
    
    if delta < 0:
        # Negative trend - lead with concern
        summary = f"⚠️ {metric_name} declined {delta_pct_str} {period_type}-over-{period_type}, down {_format_number(abs(delta), is_currency, False)} to {current_str}."
    elif delta > 0:
        # Positive trend
        if delta_pct > 20:
            summary = f"✓ Strong performance: {metric_name} surged {delta_pct_str} {period_type}-over-{period_type} to {current_str}."
        else:
            summary = f"✓ {metric_name} grew {delta_pct_str} {period_type}-over-{period_type} to {current_str}."
    else:
        summary = f"{metric_name} remained flat at {current_str} {period_type}-over-{period_type}."
    
    # Generate actionable bullets - negative first, then positive, then context
    bullets = []
    
    # Add trend context if we have multiple periods
    if len(df) >= 3:
        avg_delta_pct = df.head(3)["delta_pct"].mean()
        
        # Negative insights first
        if delta < 0:
            bullets.append(f"⚠️ Requires attention: {period_type}-over-{period_type} decline of {_format_number(abs(delta), is_currency, False)}")
            if abs(delta_pct) > abs(avg_delta_pct) * 1.5:
                bullets.append(f"⚠️ Decline accelerating: {abs(delta_pct):.1f}% vs. recent average of {abs(avg_delta_pct):.1f}%")
        
        # Positive insights
        if delta > 0:
            bullets.append(f"✓ Period-over-period growth: +{_format_number(delta, is_currency, False)} ({delta_pct_str})")
            if delta_pct > avg_delta_pct * 1.5:
                bullets.append(f"✓ Outperforming recent trend: {delta_pct:.1f}% vs. average {avg_delta_pct:.1f}%")
        
        # Context
        if len(bullets) < 2:
            bullets.append(f"Prior {period_type}: {prior_str} | Current: {current_str}")
    else:
        # Fallback if limited data
        if delta < 0:
            bullets.append(f"⚠️ {period_type_cap}-over-{period_type} decline: {prior_str} → {current_str}")
        else:
            bullets.append(f"Period comparison: {prior_str} → {current_str} ({delta_pct_str})")
    
    # Add actionable recommendation
    if delta < -10:
        bullets.append("→ Recommend: Investigate segment-level drivers and channel performance")
    elif delta > 20:
        bullets.append("→ Opportunity: Analyze successful drivers for replication")
    
    # Limit to 3 bullets
    bullets = bullets[:3]
    
    return Insight(
        title=f"{period_type_cap}-over-{period_type_cap} Performance",
        summary=summary,
        bullets=bullets,
        drivers=[]  # Variance queries don't have segment breakdowns
    )


def _calculate_forecast_insights(plan: Plan, df: pd.DataFrame) -> Insight:
    """
    Generate insights for forecast vs actual queries.
    
    Args:
        plan: Query plan
        df: DataFrame with columns: week, forecast_value, outlook_value, actual_value, 
            delta_vs_forecast, delta_vs_outlook, accuracy_vs_forecast_pct, accuracy_vs_outlook_pct
        
    Returns:
        Insight object with forecast accuracy analysis
    """
    if df.empty:
        return Insight(
            title="Forecast Accuracy",
            summary="No forecast data available for the selected period.",
            bullets=["No forecast data to analyze."],
            drivers=[]
        )
    
    # Calculate overall metrics
    total_forecast = df["forecast_value"].sum()
    total_outlook = df["outlook_value"].sum()
    total_actual = df["actual_value"].sum()
    
    delta_vs_forecast = total_actual - total_forecast
    delta_vs_outlook = total_actual - total_outlook
    
    accuracy_vs_forecast = (total_actual / total_forecast * 100) if total_forecast > 0 else 0
    accuracy_vs_outlook = (total_actual / total_outlook * 100) if total_outlook > 0 else 0
    
    abs_error_vs_forecast = abs(delta_vs_forecast) / total_forecast * 100 if total_forecast > 0 else 0
    abs_error_vs_outlook = abs(delta_vs_outlook) / total_outlook * 100 if total_outlook > 0 else 0
    
    # Determine if currency
    is_currency = _is_currency_metric(plan.metric)
    
    # Format values
    actual_str = _format_number(total_actual, is_currency)
    forecast_str = _format_number(total_forecast, is_currency)
    outlook_str = _format_number(total_outlook, is_currency)
    delta_forecast_str = _format_number(delta_vs_forecast, is_currency)
    delta_outlook_str = _format_number(delta_vs_outlook, is_currency)
    
    # Generate summary
    if abs(accuracy_vs_forecast - 100) < 5:
        performance = "closely matched"
    elif accuracy_vs_forecast > 105:
        performance = "exceeded"
    else:
        performance = "fell short of"
    
    summary = f"Actual {plan.metric.replace('_', ' ')} {performance} forecast by {delta_forecast_str} ({accuracy_vs_forecast:.1f}% of forecast)."
    
    # Generate bullets
    bullets = [
        f"Actual: {actual_str} vs. Forecast: {forecast_str} (error: {abs_error_vs_forecast:.1f}%)",
        f"Actual: {actual_str} vs. Outlook: {outlook_str} (error: {abs_error_vs_outlook:.1f}%)"
    ]
    
    # Add weekly trend if available
    if len(df) >= 2:
        recent_weeks = df.head(2)
        recent_accuracy = recent_weeks["accuracy_vs_forecast_pct"].mean()
        if recent_accuracy > accuracy_vs_forecast:
            bullets.append(f"Recent weeks show improving accuracy ({recent_accuracy:.1f}% vs. overall {accuracy_vs_forecast:.1f}%)")
        elif recent_accuracy < accuracy_vs_forecast:
            bullets.append(f"Recent weeks show declining accuracy ({recent_accuracy:.1f}% vs. overall {accuracy_vs_forecast:.1f}%)")
    
    # Limit to 3 bullets
    bullets = bullets[:3]
    
    # Identify weeks with largest variances as drivers
    drivers = []
    df_sorted = df.copy()
    df_sorted["abs_delta"] = df_sorted["delta_vs_forecast"].abs()
    df_sorted = df_sorted.sort_values("abs_delta", ascending=False)
    
    for idx, row in df_sorted.head(3).iterrows():
        week = row.get("week", "Unknown")
        delta = row["delta_vs_forecast"]
        delta_pct = (delta / row["forecast_value"] * 100) if row["forecast_value"] > 0 else 0
        
        drivers.append(Driver(
            segment=f"Week {week}",
            value=row["actual_value"],
            delta=delta,
            delta_pct=delta_pct
        ))
    
    return Insight(
        title="Forecast Accuracy Analysis",
        summary=summary,
        bullets=bullets,
        drivers=drivers
    )


def _calculate_funnel_insights(plan: Plan, df: pd.DataFrame) -> Insight:
    """
    Generate insights for funnel queries.
    
    Args:
        plan: Query plan
        df: DataFrame with columns: stage, stage_order, value_amt, value_count, conversion_rate
        
    Returns:
        Insight object with funnel conversion analysis
    """
    if df.empty or len(df) < 3:
        return Insight(
            title="Funnel Analysis",
            summary="Insufficient data for funnel analysis.",
            bullets=["Need at least 3 funnel stages."],
            drivers=[]
        )
    
    # Get funnel stages (should be 3: Submissions, Approvals, Issuances)
    submissions = df[df["stage"] == "Submissions"].iloc[0]
    approvals = df[df["stage"] == "Approvals"].iloc[0]
    issuances = df[df["stage"] == "Issuances"].iloc[0]
    
    # Determine if we're looking at amounts or counts
    is_currency = _is_currency_metric(plan.metric)
    value_col = "value_amt" if is_currency else "value_count"
    
    # Get values
    submissions_val = submissions[value_col]
    approvals_val = approvals[value_col]
    issuances_val = issuances[value_col]
    
    # Get conversion rates
    approval_rate = approvals["conversion_rate"]
    issuance_rate = issuances["conversion_rate"]
    
    # Format values
    submissions_str = _format_number(submissions_val, is_currency)
    approvals_str = _format_number(approvals_val, is_currency)
    issuances_str = _format_number(issuances_val, is_currency)
    
    # Calculate approval to issuance rate
    approval_to_issuance_rate = (issuances_val / approvals_val * 100) if approvals_val > 0 else 0
    
    # Generate executive summary - prioritize bottlenecks
    if approval_rate < 50:
        summary = f"⚠️ Critical bottleneck at approval stage: Only {approval_rate:.1f}% of {submissions_str} submissions approved. Overall funding rate: {issuance_rate:.1f}%."
    elif approval_to_issuance_rate < 70:
        summary = f"⚠️ Issuance conversion needs attention: {approval_to_issuance_rate:.1f}% of approvals funded. Approval rate: {approval_rate:.1f}%, overall funding: {issuance_rate:.1f}%."
    elif issuance_rate < 50:
        summary = f"⚠️ Overall funnel efficiency below target: {issuance_rate:.1f}% funding rate from {submissions_str} submissions."
    else:
        summary = f"✓ Healthy funnel performance: {approval_rate:.1f}% approval rate, {issuance_rate:.1f}% overall funding rate from {submissions_str} submissions."
    
    # Generate actionable bullets - bottlenecks first
    bullets = []
    
    # Identify and prioritize bottlenecks
    if approval_rate < 50:
        bullets.append(f"⚠️ Approval bottleneck: {submissions_str} → {approvals_str} ({approval_rate:.1f}% conversion)")
        bullets.append(f"→ Recommend: Review credit criteria and underwriting process")
    elif approval_to_issuance_rate < 70:
        bullets.append(f"⚠️ Issuance bottleneck: {approvals_str} → {issuances_str} ({approval_to_issuance_rate:.1f}% conversion)")
        bullets.append(f"→ Recommend: Analyze post-approval drop-off reasons")
    else:
        # Positive performance
        bullets.append(f"✓ Strong approval conversion: {submissions_str} → {approvals_str} ({approval_rate:.1f}%)")
        bullets.append(f"✓ Solid issuance rate: {approvals_str} → {issuances_str} ({approval_to_issuance_rate:.1f}%)")
    
    # Add overall context if not already included
    if len(bullets) < 3:
        bullets.append(f"Overall funnel efficiency: {issuance_rate:.1f}% of submissions result in issuance")
    
    # Limit to 3 bullets
    bullets = bullets[:3]
    
    # Create drivers for each stage
    drivers = [
        Driver(
            segment="Submissions",
            value=submissions_val,
            delta=0,
            delta_pct=100.0
        ),
        Driver(
            segment="Approvals",
            value=approvals_val,
            delta=approvals_val - submissions_val,
            delta_pct=approval_rate
        ),
        Driver(
            segment="Issuances",
            value=issuances_val,
            delta=issuances_val - submissions_val,
            delta_pct=issuance_rate
        )
    ]
    
    return Insight(
        title="Funnel Conversion Analysis",
        summary=summary,
        bullets=bullets,
        drivers=drivers
    )


def _calculate_multi_metric_insights(plan: Plan, df: pd.DataFrame) -> Insight:
    """
    Generate insights for multi-metric comparison queries.
    
    Args:
        plan: Query plan
        df: DataFrame with columns: period, app_submit_amnt, apps_approved_amnt, issued_amnt
        
    Returns:
        Insight object with multi-metric analysis
    """
    if df.empty:
        return Insight(
            title="Multi-Metric Analysis",
            summary="No data available for comparison.",
            bullets=["Unable to compare metrics."],
            drivers=[]
        )
    
    # Parse which metrics are included
    requested_metrics = [m.strip() for m in plan.metric.split(',')]
    has_submits = "app_submit_amnt" in requested_metrics and "app_submit_amnt" in df.columns
    has_approvals = "apps_approved_amnt" in requested_metrics and "apps_approved_amnt" in df.columns
    has_issuances = "issued_amnt" in requested_metrics and "issued_amnt" in df.columns
    
    # Calculate totals for available metrics
    total_submits = df["app_submit_amnt"].sum() if has_submits else 0
    total_approvals = df["apps_approved_amnt"].sum() if has_approvals else 0
    total_issuances = df["issued_amnt"].sum() if has_issuances else 0
    
    # Calculate conversion rates only if we have the necessary metrics
    approval_rate = (total_approvals / total_submits * 100) if has_submits and has_approvals and total_submits > 0 else None
    issuance_rate = (total_issuances / total_submits * 100) if has_submits and has_issuances and total_submits > 0 else None
    approval_to_issuance = (total_issuances / total_approvals * 100) if has_approvals and has_issuances and total_approvals > 0 else None
    
    # Format values
    submits_str = _format_number(total_submits, True)
    approvals_str = _format_number(total_approvals, True)
    issuances_str = _format_number(total_issuances, True)
    
    # Calculate trends and detect anomalies for each available metric
    submits_growth = 0
    approvals_growth = 0
    issuances_growth = 0
    
    # Detect anomalies (spikes, drops, unusual patterns)
    anomalies = []
    
    if has_submits and len(df) > 1:
        submits_mean = df["app_submit_amnt"].mean()
        submits_std = df["app_submit_amnt"].std()
        
        # Calculate growth
        if df["app_submit_amnt"].iloc[0] > 0:
            submits_growth = ((df["app_submit_amnt"].iloc[-1] - df["app_submit_amnt"].iloc[0]) / df["app_submit_amnt"].iloc[0] * 100)
        
        # Detect spikes/drops (values > 2 std deviations from mean)
        for idx, row in df.iterrows():
            value = row["app_submit_amnt"]
            if abs(value - submits_mean) > 2 * submits_std:
                anomaly_type = "spike" if value > submits_mean else "drop"
                pct_diff = ((value - submits_mean) / submits_mean * 100)
                anomalies.append({
                    "metric": "App Submits",
                    "type": anomaly_type,
                    "period": row[df.columns[0]],
                    "value": value,
                    "pct_diff": pct_diff
                })
    
    if has_approvals and len(df) > 1:
        approvals_mean = df["apps_approved_amnt"].mean()
        approvals_std = df["apps_approved_amnt"].std()
        
        # Calculate growth
        if df["apps_approved_amnt"].iloc[0] > 0:
            approvals_growth = ((df["apps_approved_amnt"].iloc[-1] - df["apps_approved_amnt"].iloc[0]) / df["apps_approved_amnt"].iloc[0] * 100)
        
        # Detect anomalies
        for idx, row in df.iterrows():
            value = row["apps_approved_amnt"]
            if abs(value - approvals_mean) > 2 * approvals_std:
                anomaly_type = "spike" if value > approvals_mean else "drop"
                pct_diff = ((value - approvals_mean) / approvals_mean * 100)
                anomalies.append({
                    "metric": "Approvals",
                    "type": anomaly_type,
                    "period": row[df.columns[0]],
                    "value": value,
                    "pct_diff": pct_diff
                })
    
    if has_issuances and len(df) > 1:
        issuances_mean = df["issued_amnt"].mean()
        issuances_std = df["issued_amnt"].std()
        
        # Calculate growth
        if df["issued_amnt"].iloc[0] > 0:
            issuances_growth = ((df["issued_amnt"].iloc[-1] - df["issued_amnt"].iloc[0]) / df["issued_amnt"].iloc[0] * 100)
        
        # Detect anomalies
        for idx, row in df.iterrows():
            value = row["issued_amnt"]
            if abs(value - issuances_mean) > 2 * issuances_std:
                anomaly_type = "spike" if value > issuances_mean else "drop"
                pct_diff = ((value - issuances_mean) / issuances_mean * 100)
                anomalies.append({
                    "metric": "Issuances",
                    "type": anomaly_type,
                    "period": row[df.columns[0]],
                    "value": value,
                    "pct_diff": pct_diff
                })
    
    # Generate executive summary based on available metrics
    metric_names = []
    if has_submits:
        metric_names.append(f"{submits_str} submissions")
    if has_approvals:
        metric_names.append(f"{approvals_str} approvals")
    if has_issuances:
        metric_names.append(f"{issuances_str} issuances")
    
    # Generate summary based on what metrics we have
    if approval_rate is not None and approval_rate < 50:
        summary = f"⚠️ Approval bottleneck: {approval_rate:.1f}% of {submits_str} submissions approved."
    elif issuance_rate is not None and issuance_rate < 50:
        summary = f"⚠️ Issuance conversion needs attention: {issuance_rate:.1f}% overall funding rate."
    elif len(metric_names) >= 2:
        summary = f"Comparing {' vs '.join(metric_names)} over {len(df)} periods."
    else:
        summary = f"Analyzing {metric_names[0] if metric_names else 'metrics'} over {len(df)} periods."
    
    # Generate actionable bullets - prioritize anomalies first
    bullets = []
    
    # Report anomalies first (drops before spikes)
    drops = [a for a in anomalies if a["type"] == "drop"]
    spikes = [a for a in anomalies if a["type"] == "spike"]
    
    if drops:
        # Report most significant drop
        worst_drop = min(drops, key=lambda x: x["pct_diff"])
        period_str = str(worst_drop["period"])
        bullets.append(f"⚠️ Anomaly detected: {worst_drop['metric']} dropped {abs(worst_drop['pct_diff']):.1f}% below average in {period_str}")
    
    if spikes and len(bullets) < 2:
        # Report most significant spike
        biggest_spike = max(spikes, key=lambda x: x["pct_diff"])
        period_str = str(biggest_spike["period"])
        bullets.append(f"✓ Spike detected: {biggest_spike['metric']} surged {biggest_spike['pct_diff']:.1f}% above average in {period_str}")
    
    # If no anomalies, report trends
    if len(bullets) == 0:
        # Identify declining metrics
        declining_metrics = []
        if has_submits and submits_growth < -5:
            declining_metrics.append(f"App Submits ({submits_growth:.1f}%)")
        if has_approvals and approvals_growth < -5:
            declining_metrics.append(f"Approvals ({approvals_growth:.1f}%)")
        if has_issuances and issuances_growth < -5:
            declining_metrics.append(f"Issuances ({issuances_growth:.1f}%)")
        
        if declining_metrics:
            bullets.append(f"⚠️ Declining: {', '.join(declining_metrics)}")
        
        # Positive trends
        growing_metrics = []
        if has_submits and submits_growth > 5:
            growing_metrics.append(f"App Submits (+{submits_growth:.1f}%)")
        if has_approvals and approvals_growth > 5:
            growing_metrics.append(f"Approvals (+{approvals_growth:.1f}%)")
        if has_issuances and issuances_growth > 5:
            growing_metrics.append(f"Issuances (+{issuances_growth:.1f}%)")
        
        if growing_metrics:
            bullets.append(f"✓ Growing: {', '.join(growing_metrics)}")
    
    # Conversion rates (only if we have the necessary metrics)
    if approval_rate is not None and approval_to_issuance is not None:
        bullets.append(f"Conversion: {approval_rate:.1f}% approval, {approval_to_issuance:.1f}% approval-to-issuance")
    elif approval_rate is not None:
        bullets.append(f"Approval rate: {approval_rate:.1f}%")
    elif issuance_rate is not None:
        bullets.append(f"Overall funding rate: {issuance_rate:.1f}%")
    
    # Add totals if we don't have enough bullets
    if len(bullets) < 2:
        if has_submits:
            bullets.append(f"Total submissions: {submits_str}")
        if has_approvals:
            bullets.append(f"Total approvals: {approvals_str}")
        if has_issuances:
            bullets.append(f"Total issuances: {issuances_str}")
    
    # Limit to 3 bullets
    bullets = bullets[:3]
    
    # Prepare statistical summary for LLM
    statistical_summary = {
        "totals": {
            "submissions": total_submits if has_submits else None,
            "approvals": total_approvals if has_approvals else None,
            "issuances": total_issuances if has_issuances else None
        },
        "growth_rates": {
            "submissions": submits_growth if has_submits else None,
            "approvals": approvals_growth if has_approvals else None,
            "issuances": issuances_growth if has_issuances else None
        },
        "conversion_rates": {
            "approval_rate": approval_rate,
            "issuance_rate": issuance_rate,
            "approval_to_issuance": approval_to_issuance
        },
        "anomalies": anomalies,
        "periods": len(df),
        "summary": summary,
        "bullets": bullets
    }
    
    # Use LLM to generate enhanced insights
    llm_insights = _generate_llm_insights(plan, df, statistical_summary)
    
    # Use LLM-generated insights if available, otherwise fall back to statistical insights
    final_summary = llm_insights.get("summary", summary)
    final_bullets = llm_insights.get("bullets", bullets)[:3]  # Limit to 3
    
    # Create drivers for each requested metric
    drivers = []
    
    if has_submits:
        drivers.append(Driver(
            segment="App Submits",
            value=total_submits,
            delta=df["app_submit_amnt"].iloc[-1] - df["app_submit_amnt"].iloc[0] if len(df) > 1 else 0,
            delta_pct=submits_growth
        ))
    
    if has_approvals:
        drivers.append(Driver(
            segment="Approvals",
            value=total_approvals,
            delta=df["apps_approved_amnt"].iloc[-1] - df["apps_approved_amnt"].iloc[0] if len(df) > 1 else 0,
            delta_pct=approvals_growth
        ))
    
    if has_issuances:
        drivers.append(Driver(
            segment="Issuances",
            value=total_issuances,
            delta=df["issued_amnt"].iloc[-1] - df["issued_amnt"].iloc[0] if len(df) > 1 else 0,
            delta_pct=issuances_growth
        ))
    
    return Insight(
        title="Multi-Metric Performance",
        summary=final_summary,
        bullets=final_bullets,
        drivers=drivers
    )


def _calculate_trend_insights(plan: Plan, df: pd.DataFrame) -> Insight:
    """
    Generate insights for trend queries.
    
    Args:
        plan: Query plan
        df: DataFrame with columns: week/month, metric_value, record_count
        
    Returns:
        Insight object with trend analysis
    """
    if df.empty:
        return Insight(
            title="Trend Analysis",
            summary="No data available for the selected period.",
            bullets=["No trend data to analyze."],
            drivers=[]
        )
    
    # Calculate trend metrics
    total_value = df["metric_value"].sum()
    avg_value = df["metric_value"].mean()
    
    # Get first and last periods for growth calculation
    first_value = df.iloc[-1]["metric_value"]  # Oldest (sorted ASC)
    last_value = df.iloc[-1]["metric_value"] if len(df) == 1 else df.iloc[-2]["metric_value"]  # Most recent complete period
    current_value = df.iloc[-1]["metric_value"]  # Latest
    
    # Calculate growth
    growth = ((last_value - first_value) / first_value * 100) if first_value > 0 else 0
    
    # Determine if currency or percentage
    is_currency = _is_currency_metric(plan.metric)
    is_percentage = _is_percentage_metric(plan.metric)
    
    # Format values
    total_str = _format_number(total_value, is_currency, is_percentage)
    avg_str = _format_number(avg_value, is_currency, is_percentage)
    current_str = _format_number(current_value, is_currency, is_percentage)
    
    # Determine period type
    period_type = "weekly" if "week" in df.columns[0].lower() else "monthly" if "month" in df.columns[0].lower() else "daily"
    
    # Generate executive summary - prioritize negative trends
    metric_name = plan.metric.replace('_', ' ').replace('amnt', '').replace('amt', '').title().strip()
    
    if growth < -10:
        # Significant decline - lead with concern
        summary = f"⚠️ {metric_name} trending down {growth:.1f}% over {len(df)} periods. Total: {total_str}, latest: {current_str}."
    elif growth < -5:
        # Moderate decline
        summary = f"⚠️ {metric_name} shows declining trend ({growth:.1f}%) with {total_str} total across {len(df)} periods."
    elif growth > 15:
        # Strong growth
        summary = f"✓ {metric_name} demonstrates strong growth ({growth:+.1f}%) with {total_str} total over {len(df)} periods."
    elif growth > 5:
        # Moderate growth
        summary = f"✓ {metric_name} trending upward ({growth:+.1f}%) with {total_str} total across {len(df)} periods."
    else:
        # Stable
        summary = f"{metric_name} remains stable with {total_str} total over {len(df)} periods."
    
    # Generate actionable bullets - negative first, then positive, then context
    bullets = []
    
    # Negative insights first
    if growth < -5:
        bullets.append(f"⚠️ Declining trajectory: {growth:.1f}% from {_format_number(first_value, is_currency, is_percentage)} to {_format_number(last_value, is_currency, is_percentage)}")
        # Check for acceleration
        if len(df) >= 4:
            recent_growth = ((df.iloc[-1]["metric_value"] - df.iloc[-3]["metric_value"]) / df.iloc[-3]["metric_value"] * 100) if df.iloc[-3]["metric_value"] > 0 else 0
            if recent_growth < growth:
                bullets.append(f"⚠️ Decline accelerating in recent periods")
    
    # Positive insights
    if growth > 5:
        bullets.append(f"✓ Positive momentum: {growth:+.1f}% growth from {_format_number(first_value, is_currency, is_percentage)} to {_format_number(last_value, is_currency, is_percentage)}")
        if len(df) >= 4:
            recent_growth = ((df.iloc[-1]["metric_value"] - df.iloc[-3]["metric_value"]) / df.iloc[-3]["metric_value"] * 100) if df.iloc[-3]["metric_value"] > 0 else 0
            if recent_growth > growth:
                bullets.append(f"✓ Growth accelerating in recent periods")
    
    # Context - always include average
    if len(bullets) < 2:
        bullets.append(f"Average per period: {avg_str} | Latest: {current_str}")
    
    # Add actionable recommendation
    if growth < -10:
        bullets.append("→ Urgent: Conduct root cause analysis and implement corrective actions")
    elif growth < -5:
        bullets.append("→ Recommend: Review segment performance and identify improvement opportunities")
    elif growth > 15:
        bullets.append("→ Opportunity: Document success factors for scaling across segments")
    
    # Limit to 3 bullets
    bullets = bullets[:3]
    
    # Identify top and bottom periods as drivers
    drivers = []
    df_sorted = df.sort_values("metric_value", ascending=False)
    
    # Top 3 periods
    for idx, row in df_sorted.head(3).iterrows():
        period = row[df.columns[0]]  # First column is the period
        value = row["metric_value"]
        delta = value - avg_value
        delta_pct = (delta / avg_value * 100) if avg_value > 0 else 0
        
        drivers.append(Driver(
            segment=f"Period {period}",
            value=value,
            delta=delta,
            delta_pct=delta_pct
        ))
    
    return Insight(
        title=f"{period_type.title()} Trend Analysis",
        summary=summary,
        bullets=bullets,
        drivers=drivers[:3]  # Limit to top 3
    )


def summarize(plan: Plan, df: pd.DataFrame) -> Insight:
    """
    Generate narrative insights from query results.
    
    This is the main entry point for the Insights Agent. It:
    1. Analyzes the query intent and DataFrame structure
    2. Calculates relevant metrics (deltas, drivers, conversions)
    3. Generates executive summary
    4. Creates 2-3 key finding bullets
    5. Identifies top segment drivers
    
    Args:
        plan: Structured query plan from Planner Agent
        df: Query results from SQL Agent
        
    Returns:
        Insight object with title, summary, bullets, and drivers
        
    Raises:
        ValueError: If intent is not supported
    """
    logger.info(
        f"Generating insights for intent: {plan.intent}",
        extra={
            "intent": plan.intent,
            "metric": plan.metric,
            "row_count": len(df)
        }
    )
    
    try:
        # Route to appropriate insight generator based on intent
        if plan.intent == "variance":
            insight = _calculate_variance_insights(plan, df)
        elif plan.intent == "forecast_vs_actual":
            insight = _calculate_forecast_insights(plan, df)
        elif plan.intent == "funnel":
            insight = _calculate_funnel_insights(plan, df)
        elif plan.intent == "multi_metric":
            insight = _calculate_multi_metric_insights(plan, df)
        elif plan.intent in ["trend", "distribution", "relationship"]:
            insight = _calculate_trend_insights(plan, df)
        else:
            # Default fallback
            insight = Insight(
                title="Analysis Results",
                summary=f"Query returned {len(df)} records for {plan.metric}.",
                bullets=[
                    f"Intent: {plan.intent}",
                    f"Time window: {plan.window}"
                ],
                drivers=[]
            )
        
        logger.info(
            "Insights generated successfully",
            extra={
                "intent": plan.intent,
                "title": insight.title,
                "driver_count": len(insight.drivers)
            }
        )
        
        return insight
        
    except Exception as e:
        logger.error(
            f"Failed to generate insights: {str(e)}",
            extra={
                "intent": plan.intent,
                "error": str(e)
            }
        )
        # Return fallback insight on error
        return Insight(
            title="Analysis Results",
            summary=f"Generated insights for {plan.metric} over {plan.window}.",
            bullets=[
                f"Query returned {len(df)} records",
                f"Analysis type: {plan.intent}"
            ],
            drivers=[]
        )
