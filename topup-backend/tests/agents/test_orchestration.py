"""
Test suite for LangGraph orchestration.

This module tests the main orchestration flow including:
- Graph construction
- Node execution
- Conditional routing
- Error handling
- Retry logic
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from agents import (
    create_graph,
    run_query,
    router_node,
    memory_node,
    planner_node,
    cache_check_node,
    guardrail_node,
    sql_node,
    chart_node,
    insights_node,
    cache_store_node,
    should_use_memory,
    should_skip_execution,
    should_continue_after_guardrail,
    GraphState
)
from models.schemas import Plan, SegmentFilters, Insight, Driver


# Fixtures

@pytest.fixture
def sample_state():
    """Create a sample graph state for testing."""
    return GraphState(
        user_query="Show weekly issuance trend",
        intent=None,
        plan=None,
        sql=None,
        df_dict=None,
        chart_spec=None,
        insight=None,
        error=None,
        cache_key=None,
        cache_hit=False
    )


@pytest.fixture
def sample_plan():
    """Create a sample plan for testing."""
    return Plan(
        intent="trend",
        table="cps_tb",
        metric="issued_amnt",
        date_col="issued_d",
        window="last_30d",
        granularity="weekly",
        segments=SegmentFilters(),
        chart="line"
    )


@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        "week": ["2024-W01", "2024-W02", "2024-W03"],
        "metric_value": [1000000, 1200000, 1100000],
        "record_count": [100, 120, 110]
    })


@pytest.fixture
def sample_insight():
    """Create a sample insight for testing."""
    return Insight(
        title="Trend Analysis",
        summary="Issuance shows stable trend with $3.3M total over 3 weekly periods.",
        bullets=[
            "Average per period: $1.1M",
            "Latest period: $1.1M"
        ],
        drivers=[]
    )


# Node tests

def test_router_node(sample_state):
    """Test router node classifies intent correctly."""
    with patch('agents.router.classify') as mock_classify:
        mock_classify.return_value = "trend"
        
        result = router_node(sample_state)
        
        assert result["intent"] == "trend"
        assert result["error"] is None
        mock_classify.assert_called_once_with("Show weekly issuance trend")


def test_router_node_error_handling(sample_state):
    """Test router node handles errors gracefully."""
    with patch('agents.router.classify') as mock_classify:
        mock_classify.side_effect = Exception("API error")
        
        result = router_node(sample_state)
        
        # Should fallback to trend intent
        assert result["intent"] == "trend"
        assert "Intent classification failed" in result["error"]


def test_memory_node(sample_state):
    """Test memory node retrieves explanations."""
    sample_state["intent"] = "explain"
    sample_state["user_query"] = "What is funding rate?"
    
    with patch('agents.memory_agent.explain') as mock_explain:
        mock_explain.return_value = "Funding rate is the percentage of submissions that result in issuance."
        
        result = memory_node(sample_state)
        
        assert result["insight"] is not None
        assert result["insight"].title == "Explanation"
        assert "Funding rate" in result["insight"].summary
        mock_explain.assert_called_once()


def test_planner_node(sample_state, sample_plan):
    """Test planner node generates query plan."""
    sample_state["intent"] = "trend"
    
    with patch('agents.planner.make_plan') as mock_make_plan:
        mock_make_plan.return_value = sample_plan
        
        result = planner_node(sample_state)
        
        assert result["plan"] is not None
        assert result["plan"].intent == "trend"
        assert result["cache_key"] is not None
        mock_make_plan.assert_called_once()


def test_cache_check_node_hit(sample_state, sample_plan, sample_insight):
    """Test cache check node with cache hit."""
    sample_state["cache_key"] = "test_cache_key"
    
    cached_result = {
        "df_dict": [{"week": "2024-W01", "value": 1000}],
        "chart_spec": {"data": [], "layout": {}},
        "insight": sample_insight.model_dump()
    }
    
    with patch('agents.cache_tool.get') as mock_get:
        mock_get.return_value = cached_result
        
        result = cache_check_node(sample_state)
        
        assert result["cache_hit"] is True
        assert result["df_dict"] is not None
        assert result["chart_spec"] is not None
        assert result["insight"] is not None


def test_cache_check_node_miss(sample_state):
    """Test cache check node with cache miss."""
    sample_state["cache_key"] = "test_cache_key"
    
    with patch('agents.cache_tool.get') as mock_get:
        mock_get.return_value = None
        
        result = cache_check_node(sample_state)
        
        assert result["cache_hit"] is False


def test_guardrail_node_valid(sample_state, sample_plan):
    """Test guardrail node with valid plan."""
    sample_state["plan"] = sample_plan
    
    with patch('agents.guardrail.validate') as mock_validate:
        mock_result = Mock()
        mock_result.is_valid = True
        mock_validate.return_value = mock_result
        
        result = guardrail_node(sample_state)
        
        assert result["error"] is None


def test_guardrail_node_invalid(sample_state, sample_plan):
    """Test guardrail node with invalid plan."""
    sample_state["plan"] = sample_plan
    
    with patch('agents.guardrail.validate') as mock_validate:
        mock_result = Mock()
        mock_result.is_valid = False
        mock_result.error_message = "Invalid segment value"
        mock_validate.return_value = mock_result
        
        result = guardrail_node(sample_state)
        
        assert result["error"] == "Invalid segment value"


def test_sql_node(sample_state, sample_plan, sample_df):
    """Test SQL node executes query."""
    sample_state["plan"] = sample_plan
    
    with patch('agents.sql_tool.run') as mock_run:
        mock_run.return_value = sample_df
        
        result = sql_node(sample_state)
        
        assert result["df_dict"] is not None
        assert len(result["df_dict"]) == 3
        assert result["error"] is None


def test_chart_node(sample_state, sample_plan, sample_df):
    """Test chart node generates Plotly spec."""
    sample_state["plan"] = sample_plan
    sample_state["df_dict"] = sample_df.to_dict(orient="records")
    
    with patch('agents.chart_tool.build') as mock_build:
        mock_build.return_value = {"data": [], "layout": {}}
        
        result = chart_node(sample_state)
        
        assert result["chart_spec"] is not None
        mock_build.assert_called_once()


def test_insights_node(sample_state, sample_plan, sample_df, sample_insight):
    """Test insights node generates narrative."""
    sample_state["plan"] = sample_plan
    sample_state["df_dict"] = sample_df.to_dict(orient="records")
    
    with patch('agents.insights_agent.summarize') as mock_summarize:
        mock_summarize.return_value = sample_insight
        
        result = insights_node(sample_state)
        
        assert result["insight"] is not None
        assert result["insight"].title == "Trend Analysis"
        mock_summarize.assert_called_once()


def test_cache_store_node(sample_state, sample_insight):
    """Test cache store node stores result."""
    sample_state["cache_key"] = "test_cache_key"
    sample_state["df_dict"] = [{"week": "2024-W01", "value": 1000}]
    sample_state["chart_spec"] = {"data": [], "layout": {}}
    sample_state["insight"] = sample_insight
    
    with patch('agents.cache_tool.set') as mock_set:
        result = cache_store_node(sample_state)
        
        mock_set.assert_called_once()
        call_args = mock_set.call_args
        assert call_args[0][0] == "test_cache_key"
        assert call_args[1]["ex"] == 600  # 10 minutes TTL


# Conditional edge tests

def test_should_use_memory_explain():
    """Test routing to memory for explain intent."""
    state = GraphState(
        user_query="What is funding rate?",
        intent="explain",
        plan=None,
        sql=None,
        df_dict=None,
        chart_spec=None,
        insight=None,
        error=None,
        cache_key=None,
        cache_hit=False
    )
    
    assert should_use_memory(state) == "memory"


def test_should_use_memory_other():
    """Test routing to planner for non-explain intent."""
    state = GraphState(
        user_query="Show trend",
        intent="trend",
        plan=None,
        sql=None,
        df_dict=None,
        chart_spec=None,
        insight=None,
        error=None,
        cache_key=None,
        cache_hit=False
    )
    
    assert should_use_memory(state) == "planner"


def test_should_skip_execution_cache_hit():
    """Test skipping execution on cache hit."""
    state = GraphState(
        user_query="Show trend",
        intent="trend",
        plan=None,
        sql=None,
        df_dict=None,
        chart_spec=None,
        insight=None,
        error=None,
        cache_key="test_key",
        cache_hit=True
    )
    
    assert should_skip_execution(state) == "end"


def test_should_skip_execution_error():
    """Test skipping execution on error."""
    state = GraphState(
        user_query="Show trend",
        intent="trend",
        plan=None,
        sql=None,
        df_dict=None,
        chart_spec=None,
        insight=None,
        error="Some error",
        cache_key=None,
        cache_hit=False
    )
    
    assert should_skip_execution(state) == "end"


def test_should_skip_execution_continue():
    """Test continuing execution when no cache hit or error."""
    state = GraphState(
        user_query="Show trend",
        intent="trend",
        plan=None,
        sql=None,
        df_dict=None,
        chart_spec=None,
        insight=None,
        error=None,
        cache_key=None,
        cache_hit=False
    )
    
    assert should_skip_execution(state) == "guardrail"


def test_should_continue_after_guardrail_error():
    """Test stopping after guardrail error."""
    state = GraphState(
        user_query="Show trend",
        intent="trend",
        plan=None,
        sql=None,
        df_dict=None,
        chart_spec=None,
        insight=None,
        error="Validation failed",
        cache_key=None,
        cache_hit=False
    )
    
    assert should_continue_after_guardrail(state) == "end"


def test_should_continue_after_guardrail_success():
    """Test continuing after successful guardrail validation."""
    state = GraphState(
        user_query="Show trend",
        intent="trend",
        plan=None,
        sql=None,
        df_dict=None,
        chart_spec=None,
        insight=None,
        error=None,
        cache_key=None,
        cache_hit=False
    )
    
    assert should_continue_after_guardrail(state) == "sql"


# Graph construction test

def test_create_graph():
    """Test graph creation."""
    graph = create_graph()
    
    assert graph is not None
    # Verify nodes are added
    assert "router" in graph.nodes
    assert "memory" in graph.nodes
    assert "planner" in graph.nodes
    assert "cache_check" in graph.nodes
    assert "guardrail" in graph.nodes
    assert "sql" in graph.nodes
    assert "chart" in graph.nodes
    assert "insights" in graph.nodes
    assert "cache_store" in graph.nodes


# Integration test (mocked)

@patch('agents.router.classify')
@patch('agents.planner.make_plan')
@patch('agents.cache_tool.get')
@patch('agents.guardrail.validate')
@patch('agents.sql_tool.run')
@patch('agents.chart_tool.build')
@patch('agents.insights_agent.summarize')
@patch('agents.cache_tool.set')
def test_run_query_success(
    mock_cache_set,
    mock_summarize,
    mock_chart_build,
    mock_sql_run,
    mock_validate,
    mock_cache_get,
    mock_make_plan,
    mock_classify,
    sample_plan,
    sample_df,
    sample_insight
):
    """Test successful query execution through full graph."""
    # Setup mocks
    mock_classify.return_value = "trend"
    mock_make_plan.return_value = sample_plan
    mock_cache_get.return_value = None  # Cache miss
    
    mock_validation_result = Mock()
    mock_validation_result.is_valid = True
    mock_validate.return_value = mock_validation_result
    
    mock_sql_run.return_value = sample_df
    mock_chart_build.return_value = {"data": [], "layout": {}}
    mock_summarize.return_value = sample_insight
    
    # Run query
    result = run_query("Show weekly issuance trend")
    
    # Verify result
    assert result["error"] is None
    assert result["plan"] is not None
    assert result["chart_spec"] is not None
    assert result["insight"] is not None
    assert result["cache_hit"] is False
    
    # Verify all agents were called
    mock_classify.assert_called_once()
    mock_make_plan.assert_called_once()
    mock_sql_run.assert_called_once()
    mock_chart_build.assert_called_once()
    mock_summarize.assert_called_once()
    mock_cache_set.assert_called_once()


@patch('agents.memory_agent.explain')
@patch('agents.router.classify')
def test_run_query_explain(mock_classify, mock_explain):
    """Test explain query routing to memory agent."""
    # Setup mocks
    mock_classify.return_value = "explain"
    mock_explain.return_value = "Funding rate is the percentage of submissions that result in issuance."
    
    # Run query
    result = run_query("What is funding rate?")
    
    # Verify result
    assert result["error"] is None
    assert result["insight"] is not None
    assert "Funding rate" in result["insight"]["summary"]
    
    # Verify memory agent was called
    mock_explain.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
