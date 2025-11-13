"""
Unit tests for Router Agent.

Tests intent classification for various user queries.
"""

import os
import pytest
from unittest.mock import Mock, patch

from agents.router import classify


# Mock OpenAI responses for different intents
def create_mock_response(intent: str, reasoning: str):
    """Create a mock OpenAI response."""
    mock_response = Mock()
    mock_choice = Mock()
    mock_message = Mock()
    mock_function_call = Mock()
    
    mock_function_call.arguments = f'{{"intent": "{intent}", "reasoning": "{reasoning}"}}'
    mock_message.function_call = mock_function_call
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    
    return mock_response


class TestRouterAgent:
    """Test suite for Router Agent intent classification."""
    
    @patch('agents.router._get_client')
    def test_classify_trend_intent(self, mock_get_client):
        """Test classification of trend queries."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = create_mock_response(
            "trend",
            "Query asks for time-series data"
        )
        
        result = classify("Show weekly issuance trend")
        assert result == "trend"
        
        result = classify("How have app submits changed over the last 3 months?")
        assert result == "trend"
    
    @patch('agents.router._get_client')
    def test_classify_variance_intent(self, mock_get_client):
        """Test classification of variance queries."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = create_mock_response(
            "variance",
            "Query asks for WoW comparison"
        )
        
        result = classify("What's the WoW change in approvals?")
        assert result == "variance"
        
        result = classify("Compare this month to last month")
        assert result == "variance"
    
    @patch('agents.router._get_client')
    def test_classify_forecast_intent(self, mock_get_client):
        """Test classification of forecast vs actual queries."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = create_mock_response(
            "forecast_vs_actual",
            "Query asks for forecast comparison"
        )
        
        result = classify("How did we do vs forecast?")
        assert result == "forecast_vs_actual"
        
        result = classify("Compare actual issuance to forecast")
        assert result == "forecast_vs_actual"
    
    @patch('agents.router._get_client')
    def test_classify_funnel_intent(self, mock_get_client):
        """Test classification of funnel queries."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = create_mock_response(
            "funnel",
            "Query asks for conversion funnel"
        )
        
        result = classify("Show the funnel")
        assert result == "funnel"
        
        result = classify("What's our conversion rate?")
        assert result == "funnel"
    
    @patch('agents.router._get_client')
    def test_classify_distribution_intent(self, mock_get_client):
        """Test classification of distribution queries."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = create_mock_response(
            "distribution",
            "Query asks for breakdown by segment"
        )
        
        result = classify("What's the channel mix?")
        assert result == "distribution"
        
        result = classify("Breakdown by grade")
        assert result == "distribution"
    
    @patch('agents.router._get_client')
    def test_classify_relationship_intent(self, mock_get_client):
        """Test classification of relationship queries."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = create_mock_response(
            "relationship",
            "Query asks for correlation between metrics"
        )
        
        result = classify("How does FICO relate to approval rate?")
        assert result == "relationship"
        
        result = classify("APR vs issuance")
        assert result == "relationship"
    
    @patch('agents.router._get_client')
    def test_classify_explain_intent(self, mock_get_client):
        """Test classification of explain queries."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = create_mock_response(
            "explain",
            "Query asks for definition"
        )
        
        result = classify("What is funding rate?")
        assert result == "explain"
        
        result = classify("Define approval rate")
        assert result == "explain"
    
    @patch('agents.router._get_client')
    def test_business_friendly_terms(self, mock_get_client):
        """Test recognition of business-friendly terms."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = create_mock_response(
            "trend",
            "Query uses business-friendly term 'app submits'"
        )
        
        # Should recognize "app submits" as valid term
        result = classify("Show app submits trend")
        assert result == "trend"
        
        # Should recognize "approvals" as valid term
        result = classify("Show approvals over time")
        assert result == "trend"
        
        # Should recognize "issuances" as valid term
        result = classify("Show issuances by week")
        assert result == "trend"
    
    @patch('agents.router._get_client')
    def test_fallback_on_error(self, mock_get_client):
        """Test fallback to trend intent on API error."""
        mock_get_client.side_effect = Exception("API error")
        
        result = classify("Some query")
        assert result == "trend"  # Should fallback to trend
    
    @patch('agents.router._get_client')
    def test_invalid_intent_fallback(self, mock_get_client):
        """Test fallback when invalid intent is returned."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = create_mock_response(
            "invalid_intent",
            "This should not happen"
        )
        
        result = classify("Some query")
        assert result == "trend"  # Should fallback to trend


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
