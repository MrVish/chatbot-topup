"""
Tests for Insights Agent.

This module tests the insights generation functionality for different
query intents: variance, forecast_vs_actual, funnel, and trend.
"""

import pandas as pd
import pytest

from agents.insights_agent import summarize
from models.schemas import Plan, SegmentFilters


def test_variance_insights_wow():
    """Test WoW variance insights generation."""
    # Create sample WoW data
    df = pd.DataFrame({
        "week": ["2025-45", "2025-44", "2025-43"],
        "week_start": ["2025-11-04", "2025-10-28", "2025-10-21"],
        "current_value": [1500000, 1400000, 1300000],
        "prior_week_value": [1400000, 1300000, 1200000],
        "delta": [100000, 100000, 100000],
        "delta_pct": [7.14, 7.69, 8.33]
    })
    
    plan = Plan(
        intent="variance",
        table="cps_tb",
        metric="issued_amnt",
        date_col="issued_d",
        window="last_30d",
        granularity="weekly",
        segments=SegmentFilters(),
        chart="line"
    )
    
    insight = summarize(plan, df)
    
    assert insight.title == "WEEK Variance Analysis"
    assert "increased" in insight.summary.lower() or "decreased" in insight.summary.lower()
    assert len(insight.bullets) >= 2
    assert len(insight.bullets) <= 3


def test_forecast_insights():
    """Test forecast vs actual insights generation."""
    # Create sample forecast data
    df = pd.DataFrame({
        "week": ["2025-45", "2025-44", "2025-43"],
        "week_start": ["2025-11-04", "2025-10-28", "2025-10-21"],
        "forecast_value": [1000000, 950000, 900000],
        "outlook_value": [1050000, 1000000, 950000],
        "actual_value": [1100000, 980000, 920000],
        "delta_vs_forecast": [100000, 30000, 20000],
        "delta_vs_outlook": [50000, -20000, -30000],
        "accuracy_vs_forecast_pct": [110.0, 103.2, 102.2],
        "accuracy_vs_outlook_pct": [104.8, 98.0, 96.8],
        "abs_error_vs_forecast_pct": [10.0, 3.2, 2.2],
        "abs_error_vs_outlook_pct": [4.8, 2.0, 3.2]
    })
    
    plan = Plan(
        intent="forecast_vs_actual",
        table="forecast_df",
        metric="issued_amnt",
        date_col="date",
        window="last_30d",
        granularity="weekly",
        segments=SegmentFilters(),
        chart="grouped_bar"
    )
    
    insight = summarize(plan, df)
    
    assert insight.title == "Forecast Accuracy Analysis"
    assert "forecast" in insight.summary.lower()
    assert len(insight.bullets) >= 2
    assert len(insight.bullets) <= 3
    assert len(insight.drivers) > 0


def test_funnel_insights():
    """Test funnel conversion insights generation."""
    # Create sample funnel data
    df = pd.DataFrame({
        "stage": ["Submissions", "Approvals", "Issuances"],
        "stage_order": [1, 2, 3],
        "value_amt": [5000000, 3500000, 2800000],
        "value_count": [1000, 700, 560],
        "conversion_rate": [100.0, 70.0, 56.0]
    })
    
    plan = Plan(
        intent="funnel",
        table="cps_tb",
        metric="issued_amnt",
        date_col="issued_d",
        window="last_full_month",
        granularity="monthly",
        segments=SegmentFilters(),
        chart="funnel"
    )
    
    insight = summarize(plan, df)
    
    assert insight.title == "Funnel Conversion Analysis"
    assert "funnel" in insight.summary.lower()
    assert len(insight.bullets) == 3
    assert len(insight.drivers) == 3
    assert insight.drivers[0].segment == "Submissions"
    assert insight.drivers[1].segment == "Approvals"
    assert insight.drivers[2].segment == "Issuances"


def test_trend_insights():
    """Test trend analysis insights generation."""
    # Create sample trend data
    df = pd.DataFrame({
        "week": ["2025-41", "2025-42", "2025-43", "2025-44", "2025-45"],
        "week_start": ["2025-10-07", "2025-10-14", "2025-10-21", "2025-10-28", "2025-11-04"],
        "metric_value": [1200000, 1300000, 1250000, 1400000, 1450000],
        "record_count": [240, 260, 250, 280, 290]
    })
    
    plan = Plan(
        intent="trend",
        table="cps_tb",
        metric="issued_amnt",
        date_col="issued_d",
        window="last_30d",
        granularity="weekly",
        segments=SegmentFilters(),
        chart="line"
    )
    
    insight = summarize(plan, df)
    
    assert insight.title == "Weekly Trend Analysis"
    assert "trend" in insight.summary.lower()
    assert len(insight.bullets) >= 2
    assert len(insight.bullets) <= 3
    assert len(insight.drivers) <= 3


def test_empty_dataframe():
    """Test insights generation with empty DataFrame."""
    df = pd.DataFrame()
    
    plan = Plan(
        intent="trend",
        table="cps_tb",
        metric="issued_amnt",
        date_col="issued_d",
        window="last_30d",
        granularity="weekly",
        segments=SegmentFilters(),
        chart="line"
    )
    
    insight = summarize(plan, df)
    
    assert insight.title is not None
    assert insight.summary is not None
    assert len(insight.bullets) >= 1


def test_currency_formatting():
    """Test that currency metrics are formatted correctly."""
    df = pd.DataFrame({
        "week": ["2025-45"],
        "week_start": ["2025-11-04"],
        "metric_value": [1500000],
        "record_count": [300]
    })
    
    plan = Plan(
        intent="trend",
        table="cps_tb",
        metric="issued_amnt",  # Currency metric
        date_col="issued_d",
        window="last_7d",
        granularity="weekly",
        segments=SegmentFilters(),
        chart="line"
    )
    
    insight = summarize(plan, df)
    
    # Should contain currency formatting ($ or M/K)
    assert "$" in insight.summary or "M" in insight.summary or "K" in insight.summary


def test_percentage_metric():
    """Test insights for percentage metrics like approval_rate."""
    df = pd.DataFrame({
        "week": ["2025-45", "2025-44"],
        "week_start": ["2025-11-04", "2025-10-28"],
        "current_value": [72.5, 70.0],
        "prior_week_value": [70.0, 68.5],
        "delta": [2.5, 1.5],
        "delta_pct": [3.57, 2.19]
    })
    
    plan = Plan(
        intent="variance",
        table="cps_tb",
        metric="approval_rate",
        date_col="apps_approved_d",
        window="last_30d",
        granularity="weekly",
        segments=SegmentFilters(),
        chart="line"
    )
    
    insight = summarize(plan, df)
    
    assert insight.title == "WEEK Variance Analysis"
    assert len(insight.bullets) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
