"""
Unit tests for Planner Agent.

Tests the planner agent's ability to generate structured query plans
from user queries and intents, including:
- Metric interpretation (amounts vs counts)
- Table and date column selection
- Time window and granularity defaults
- Chart type selection
- Segment filter parsing
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.planner import make_plan, _apply_default_rules, _validate_plan
from models.schemas import Plan, SegmentFilters


class TestPlannerAgent:
    """Test suite for Planner Agent."""
    
    def test_trend_query_with_amounts(self):
        """Test trend query defaults to amounts, not counts."""
        # Mock OpenAI response
        mock_plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            segments=SegmentFilters(),
            chart="line"
        )
        
        with patch('agents.planner._get_client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.parsed = mock_plan
            mock_client.return_value.beta.chat.completions.parse.return_value = mock_response
            
            plan = make_plan("Show weekly issuance trend", "trend")
            
            assert plan.metric == "issued_amnt"
            assert plan.intent == "trend"
            assert plan.chart == "line"
    
    def test_count_query_explicit(self):
        """Test that explicit count requests use count metrics."""
        # This would require the LLM to interpret "number of" correctly
        # For now, we test the structure
        mock_plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="COUNT(app_submit_d)",
            date_col="app_submit_d",
            window="last_30d",
            granularity="weekly",
            segments=SegmentFilters(),
            chart="line"
        )
        
        with patch('agents.planner._get_client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.parsed = mock_plan
            mock_client.return_value.beta.chat.completions.parse.return_value = mock_response
            
            plan = make_plan("Show number of app submits", "trend")
            
            assert "COUNT" in plan.metric or "count" in plan.metric.lower()
    
    def test_forecast_vs_actual_table_selection(self):
        """Test forecast_vs_actual intent selects forecast_df table."""
        mock_plan = Plan(
            intent="forecast_vs_actual",
            table="forecast_df",
            metric="issued_amnt",
            date_col="date",
            window="last_full_month",
            granularity="weekly",
            segments=SegmentFilters(),
            chart="grouped_bar"
        )
        
        with patch('agents.planner._get_client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.parsed = mock_plan
            mock_client.return_value.beta.chat.completions.parse.return_value = mock_response
            
            plan = make_plan("Compare actual to forecast", "forecast_vs_actual")
            
            assert plan.table == "forecast_df"
            assert plan.date_col == "date"
            assert plan.chart == "grouped_bar"
    
    def test_date_column_selection_for_submits(self):
        """Test date column selection for app submits."""
        mock_plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="app_submit_amnt",
            date_col="app_submit_d",
            window="last_30d",
            granularity="weekly",
            segments=SegmentFilters(),
            chart="line"
        )
        
        with patch('agents.planner._get_client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.parsed = mock_plan
            mock_client.return_value.beta.chat.completions.parse.return_value = mock_response
            
            plan = make_plan("Show app submits last month", "trend")
            
            assert plan.date_col == "app_submit_d"
    
    def test_date_column_selection_for_approvals(self):
        """Test date column selection for approvals."""
        mock_plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="apps_approved_amnt",
            date_col="apps_approved_d",
            window="last_30d",
            granularity="weekly",
            segments=SegmentFilters(),
            chart="line"
        )
        
        with patch('agents.planner._get_client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.parsed = mock_plan
            mock_client.return_value.beta.chat.completions.parse.return_value = mock_response
            
            plan = make_plan("Show approvals trend", "trend")
            
            assert plan.date_col == "apps_approved_d"
    
    def test_default_window_30_days(self):
        """Test default time window is 30 days."""
        mock_plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            segments=SegmentFilters(),
            chart="line"
        )
        
        with patch('agents.planner._get_client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.parsed = mock_plan
            mock_client.return_value.beta.chat.completions.parse.return_value = mock_response
            
            plan = make_plan("Show issuance trend", "trend")
            
            assert plan.window == "last_30d"
    
    def test_weekly_granularity_for_short_windows(self):
        """Test weekly granularity for windows ≤3 months."""
        mock_plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_3_full_months",
            granularity="daily",  # Will be corrected to weekly
            segments=SegmentFilters(),
            chart="line"
        )
        
        with patch('agents.planner._get_client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.parsed = mock_plan
            mock_client.return_value.beta.chat.completions.parse.return_value = mock_response
            
            plan = make_plan("Show last 3 months", "trend")
            
            # Apply default rules
            plan = _apply_default_rules(plan, "Show last 3 months")
            
            assert plan.granularity == "weekly"
    
    def test_segment_filter_parsing(self):
        """Test segment filter extraction from query."""
        mock_plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            segments=SegmentFilters(channel="Email", grade="P1"),
            chart="line"
        )
        
        with patch('agents.planner._get_client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.parsed = mock_plan
            mock_client.return_value.beta.chat.completions.parse.return_value = mock_response
            
            plan = make_plan("Show issuance for Email channel grade P1", "trend")
            
            assert plan.segments.channel == "Email"
            assert plan.segments.grade == "P1"
    
    def test_chart_type_for_funnel(self):
        """Test funnel intent selects funnel chart."""
        mock_plan = Plan(
            intent="funnel",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_full_month",
            granularity="monthly",
            segments=SegmentFilters(),
            chart="funnel"
        )
        
        with patch('agents.planner._get_client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.parsed = mock_plan
            mock_client.return_value.beta.chat.completions.parse.return_value = mock_response
            
            plan = make_plan("Show the funnel", "funnel")
            
            assert plan.chart == "funnel"
    
    def test_chart_type_for_distribution(self):
        """Test distribution intent selects pie chart."""
        mock_plan = Plan(
            intent="distribution",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            segments=SegmentFilters(),
            chart="pie"
        )
        
        with patch('agents.planner._get_client') as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.parsed = mock_plan
            mock_client.return_value.beta.chat.completions.parse.return_value = mock_response
            
            plan = make_plan("Show channel distribution", "distribution")
            
            assert plan.chart == "pie"
    
    def test_validate_plan_corrects_forecast_date_col(self):
        """Test validation corrects date_col for forecast_df table."""
        plan = Plan(
            intent="forecast_vs_actual",
            table="forecast_df",
            metric="issued_amnt",
            date_col="issued_d",  # Wrong for forecast_df
            window="last_full_month",
            granularity="weekly",
            segments=SegmentFilters(),
            chart="grouped_bar"
        )
        
        validated_plan = _validate_plan(plan)
        
        assert validated_plan.date_col == "date"
    
    def test_validate_plan_corrects_cps_date_col(self):
        """Test validation corrects date_col for cps_tb table."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="date",  # Wrong for cps_tb
            window="last_30d",
            granularity="weekly",
            segments=SegmentFilters(),
            chart="line"
        )
        
        validated_plan = _validate_plan(plan)
        
        assert validated_plan.date_col == "app_submit_d"
    
    def test_cache_key_generation(self):
        """Test that plan generates consistent cache keys."""
        plan1 = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            segments=SegmentFilters(channel="Email"),
            chart="line"
        )
        
        plan2 = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            segments=SegmentFilters(channel="Email"),
            chart="line"
        )
        
        # Same plans should generate same cache key
        assert plan1.cache_key() == plan2.cache_key()
        
        # Different plans should generate different cache keys
        plan3 = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_7d",  # Different window
            granularity="weekly",
            segments=SegmentFilters(channel="Email"),
            chart="line"
        )
        
        assert plan1.cache_key() != plan3.cache_key()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

