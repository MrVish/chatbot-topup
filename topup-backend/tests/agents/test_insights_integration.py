"""
Integration test for Insights Agent with real database.

This test verifies that the insights agent works correctly with
actual SQL query results from the database.
"""

from pathlib import Path

from agents.insights_agent import summarize
from models.schemas import Plan, SegmentFilters
from tools.sql_tool import run


def test_insights_with_real_trend_data():
    """Test insights generation with real trend query data."""
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
    
    # Get real data from database
    df = run(plan)
    
    print(f"\nTrend query returned {len(df)} rows")
    print(f"Columns: {df.columns.tolist()}")
    if not df.empty:
        print(f"Sample data:\n{df.head()}")
    
    # Generate insights
    insight = summarize(plan, df)
    
    print(f"\nInsight Title: {insight.title}")
    print(f"Summary: {insight.summary}")
    print(f"Bullets:")
    for bullet in insight.bullets:
        print(f"  - {bullet}")
    print(f"Drivers: {len(insight.drivers)}")
    for driver in insight.drivers:
        print(f"  - {driver.segment}: {driver.value} (delta: {driver.delta_pct:+.1f}%)")
    
    assert insight.title is not None
    assert insight.summary is not None
    assert len(insight.bullets) >= 2


def test_insights_with_real_variance_data():
    """Test insights generation with real WoW variance data."""
    plan = Plan(
        intent="variance",
        table="cps_tb",
        metric="issued_amnt",
        date_col="issued_d",
        window="last_30d",
        granularity="weekly",
        segments=SegmentFilters(channel="Email"),
        chart="line"
    )
    
    # Get real data from database
    df = run(plan)
    
    print(f"\nVariance query returned {len(df)} rows")
    print(f"Columns: {df.columns.tolist()}")
    if not df.empty:
        print(f"Sample data:\n{df.head()}")
    
    # Generate insights
    insight = summarize(plan, df)
    
    print(f"\nInsight Title: {insight.title}")
    print(f"Summary: {insight.summary}")
    print(f"Bullets:")
    for bullet in insight.bullets:
        print(f"  - {bullet}")
    
    assert insight.title is not None
    assert insight.summary is not None


def test_insights_with_real_forecast_data():
    """Test insights generation with real forecast vs actual data."""
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
    
    # Get real data from database
    df = run(plan)
    
    print(f"\nForecast query returned {len(df)} rows")
    print(f"Columns: {df.columns.tolist()}")
    if not df.empty:
        print(f"Sample data:\n{df.head()}")
    
    # Generate insights
    insight = summarize(plan, df)
    
    print(f"\nInsight Title: {insight.title}")
    print(f"Summary: {insight.summary}")
    print(f"Bullets:")
    for bullet in insight.bullets:
        print(f"  - {bullet}")
    print(f"Drivers: {len(insight.drivers)}")
    
    assert insight.title is not None
    assert insight.summary is not None


def test_insights_with_real_funnel_data():
    """Test insights generation with real funnel data."""
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
    
    # Get real data from database
    df = run(plan)
    
    print(f"\nFunnel query returned {len(df)} rows")
    print(f"Columns: {df.columns.tolist()}")
    if not df.empty:
        print(f"Sample data:\n{df}")
    
    # Generate insights
    insight = summarize(plan, df)
    
    print(f"\nInsight Title: {insight.title}")
    print(f"Summary: {insight.summary}")
    print(f"Bullets:")
    for bullet in insight.bullets:
        print(f"  - {bullet}")
    print(f"Drivers: {len(insight.drivers)}")
    for driver in insight.drivers:
        print(f"  - {driver.segment}: {driver.value} ({driver.delta_pct:.1f}%)")
    
    assert insight.title is not None
    assert insight.summary is not None
    assert len(insight.drivers) == 3


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])
