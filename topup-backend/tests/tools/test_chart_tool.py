"""
Tests for chart_tool.py

Verifies Plotly specification generation for various chart types.
"""

import pandas as pd
import pytest
from models.schemas import Plan, SegmentFilters
from tools import chart_tool


def test_build_trend_chart():
    """Test line chart generation for trend intent."""
    plan = Plan(
        intent="trend",
        table="cps_tb",
        metric="issued_amt",
        date_col="issued_d",
        window="last_30d",
        granularity="weekly",
        segments=SegmentFilters(),
        chart="line"
    )
    
    # Sample data
    df = pd.DataFrame({
        "week": ["2025-W01", "2025-W02", "2025-W03", "2025-W04"],
        "issued_amt": [1000000, 1200000, 1100000, 1300000]
    })
    
    spec = chart_tool.build(plan, df, theme="light")
    
    # Verify structure
    assert "data" in spec
    assert "layout" in spec
    assert len(spec["data"]) == 1
    
    # Verify trace
    trace = spec["data"][0]
    assert trace["type"] == "scatter"
    assert trace["mode"] == "lines+markers"
    assert len(trace["x"]) == 4
    assert len(trace["y"]) == 4
    
    # Verify annotations for last two periods
    assert "annotations" in spec["layout"]
    assert len(spec["layout"]["annotations"]) == 2


def test_build_area_chart():
    """Test area chart generation."""
    plan = Plan(
        intent="trend",
        table="cps_tb",
        metric="issued_amt",
        date_col="issued_d",
        window="last_30d",
        granularity="weekly",
        segments=SegmentFilters(),
        chart="area"
    )
    
    df = pd.DataFrame({
        "week": ["2025-W01", "2025-W02"],
        "issued_amt": [1000000, 1200000]
    })
    
    spec = chart_tool.build(plan, df, theme="light")
    
    trace = spec["data"][0]
    assert trace["type"] == "scatter"
    assert "fill" in trace
    assert trace["fill"] in ["tozeroy", "tonexty"]


def test_build_forecast_chart():
    """Test grouped bar chart for forecast vs actual."""
    plan = Plan(
        intent="forecast_vs_actual",
        table="forecast_df",
        metric="issuance",
        date_col="date",
        window="last_full_month",
        granularity="weekly",
        segments=SegmentFilters(),
        chart="grouped_bar"
    )
    
    df = pd.DataFrame({
        "week": ["2025-W01", "2025-W02"],
        "forecast_issuance": [1000000, 1100000],
        "actual_issuance": [950000, 1150000]
    })
    
    spec = chart_tool.build(plan, df, theme="light")
    
    # Verify two traces (forecast and actual)
    assert len(spec["data"]) == 2
    assert spec["data"][0]["type"] == "bar"
    assert spec["data"][1]["type"] == "bar"
    assert spec["data"][0]["name"] == "Forecast"
    assert spec["data"][1]["name"] == "Actual"
    
    # Verify grouped bar mode
    assert spec["layout"]["barmode"] == "group"


def test_build_funnel_chart():
    """Test funnel chart generation."""
    plan = Plan(
        intent="funnel",
        table="cps_tb",
        metric="count",
        date_col="app_submit_d",
        window="last_full_month",
        granularity="monthly",
        segments=SegmentFilters(),
        chart="funnel"
    )
    
    df = pd.DataFrame({
        "stage": ["Submitted", "Approved", "Issued"],
        "count": [10000, 7000, 5000]
    })
    
    spec = chart_tool.build(plan, df, theme="light")
    
    # Verify funnel trace
    assert len(spec["data"]) == 1
    trace = spec["data"][0]
    assert trace["type"] == "funnel"
    assert len(trace["y"]) == 3
    assert len(trace["x"]) == 3


def test_build_pie_chart():
    """Test pie chart generation."""
    plan = Plan(
        intent="distribution",
        table="cps_tb",
        metric="issued_amt",
        date_col="issued_d",
        window="last_full_month",
        granularity="monthly",
        segments=SegmentFilters(),
        chart="pie"
    )
    
    df = pd.DataFrame({
        "channel": ["Email", "OMB", "Search"],
        "issued_amt": [5000000, 3000000, 2000000]
    })
    
    spec = chart_tool.build(plan, df, theme="light")
    
    # Verify pie trace
    assert len(spec["data"]) == 1
    trace = spec["data"][0]
    assert trace["type"] == "pie"
    assert len(trace["labels"]) == 3
    assert len(trace["values"]) == 3


def test_build_scatter_chart():
    """Test scatter chart generation."""
    plan = Plan(
        intent="relationship",
        table="cps_tb",
        metric="issued_amt",
        date_col="issued_d",
        window="last_full_month",
        granularity="monthly",
        segments=SegmentFilters(),
        chart="scatter"
    )
    
    df = pd.DataFrame({
        "cr_fico": [650, 700, 750, 800],
        "issued_amt": [10000, 15000, 20000, 25000]
    })
    
    spec = chart_tool.build(plan, df, theme="light")
    
    # Verify scatter trace
    assert len(spec["data"]) == 1
    trace = spec["data"][0]
    assert trace["type"] == "scatter"
    assert trace["mode"] == "markers"
    assert len(trace["x"]) == 4
    assert len(trace["y"]) == 4


def test_fico_band_sorting():
    """Test FICO band sort order in charts."""
    plan = Plan(
        intent="distribution",
        table="cps_tb",
        metric="issued_amt",
        date_col="issued_d",
        window="last_full_month",
        granularity="monthly",
        segments=SegmentFilters(),
        chart="pie"
    )
    
    # Unsorted FICO bands
    df = pd.DataFrame({
        "cr_fico_band": ["760+", "<640", "700-759", "640-699"],
        "issued_amt": [5000000, 1000000, 3000000, 2000000]
    })
    
    spec = chart_tool.build(plan, df, theme="light")
    
    # Verify sorted order
    labels = spec["data"][0]["labels"]
    assert labels == ["<640", "640-699", "700-759", "760+"]


def test_theme_dark():
    """Test dark theme colors."""
    plan = Plan(
        intent="trend",
        table="cps_tb",
        metric="issued_amt",
        date_col="issued_d",
        window="last_30d",
        granularity="weekly",
        segments=SegmentFilters(),
        chart="line"
    )
    
    df = pd.DataFrame({
        "week": ["2025-W01", "2025-W02"],
        "issued_amt": [1000000, 1200000]
    })
    
    spec = chart_tool.build(plan, df, theme="dark")
    
    # Verify dark theme
    assert spec["layout"]["template"] == "plotly_dark"
    assert spec["layout"]["plot_bgcolor"] == chart_tool.COLORS_DARK["background"]
    assert spec["layout"]["paper_bgcolor"] == chart_tool.COLORS_DARK["paper"]


def test_empty_dataframe():
    """Test handling of empty DataFrame."""
    plan = Plan(
        intent="trend",
        table="cps_tb",
        metric="issued_amt",
        date_col="issued_d",
        window="last_30d",
        granularity="weekly",
        segments=SegmentFilters(),
        chart="line"
    )
    
    df = pd.DataFrame()
    
    spec = chart_tool.build(plan, df, theme="light")
    
    # Verify empty chart
    assert "data" in spec
    assert "layout" in spec
    assert len(spec["data"]) == 0
    assert "No data" in spec["layout"]["title"]["text"]


def test_multi_series_trend():
    """Test trend chart with multiple series."""
    plan = Plan(
        intent="trend",
        table="cps_tb",
        metric="issued_amt",
        date_col="issued_d",
        window="last_30d",
        granularity="weekly",
        segments=SegmentFilters(),
        chart="line"
    )
    
    df = pd.DataFrame({
        "week": ["2025-W01", "2025-W02"],
        "Email": [1000000, 1200000],
        "OMB": [800000, 900000],
        "Search": [500000, 600000]
    })
    
    spec = chart_tool.build(plan, df, theme="light")
    
    # Verify multiple traces
    assert len(spec["data"]) == 3
    assert spec["data"][0]["name"] == "Email"
    assert spec["data"][1]["name"] == "OMB"
    assert spec["data"][2]["name"] == "Search"


def test_scatter_with_groups():
    """Test scatter chart with grouping."""
    plan = Plan(
        intent="relationship",
        table="cps_tb",
        metric="issued_amt",
        date_col="issued_d",
        window="last_full_month",
        granularity="monthly",
        segments=SegmentFilters(),
        chart="scatter"
    )
    
    df = pd.DataFrame({
        "cr_fico": [650, 700, 650, 700],
        "issued_amt": [10000, 15000, 12000, 16000],
        "channel": ["Email", "Email", "OMB", "OMB"]
    })
    
    spec = chart_tool.build(plan, df, theme="light")
    
    # Verify grouped scatter traces
    assert len(spec["data"]) == 2
    assert spec["data"][0]["name"] == "Email"
    assert spec["data"][1]["name"] == "OMB"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
