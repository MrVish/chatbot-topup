"""
Tests for Memory Agent.

This module tests the Memory Agent's ability to retrieve and format
explanations for metrics, fields, and concepts.
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.memory_agent import explain, _format_explanation, _clean_document_text


class TestMemoryAgent:
    """Test suite for Memory Agent."""
    
    def test_explain_funding_rate(self):
        """Test explaining funding rate."""
        response = explain("What is funding rate?")
        
        assert response is not None
        assert len(response) > 0
        assert "funding rate" in response.lower()
        # Should mention the calculation or definition
        assert any(keyword in response.lower() for keyword in ["percentage", "issued", "submitted", "conversion"])
    
    def test_explain_approval_rate(self):
        """Test explaining approval rate."""
        response = explain("What is approval rate?")
        
        assert response is not None
        assert len(response) > 0
        assert "approval rate" in response.lower()
        assert any(keyword in response.lower() for keyword in ["percentage", "approved", "offered"])
    
    def test_explain_channels(self):
        """Test explaining channels."""
        response = explain("What are the different channels?")
        
        assert response is not None
        assert len(response) > 0
        assert "channel" in response.lower()
        # Should mention at least some channel names
        assert any(channel in response for channel in ["OMB", "Email", "Search", "marketing"])
    
    def test_explain_fico(self):
        """Test explaining FICO."""
        response = explain("What is FICO?")
        
        assert response is not None
        assert len(response) > 0
        assert "fico" in response.lower()
        assert any(keyword in response.lower() for keyword in ["credit", "score", "640", "700", "760"])
    
    def test_explain_grades(self):
        """Test explaining grades."""
        response = explain("What are the different grades?")
        
        assert response is not None
        assert len(response) > 0
        assert "grade" in response.lower()
        assert any(keyword in response.lower() for keyword in ["p1", "p2", "credit", "quality"])
    
    def test_explain_issuance(self):
        """Test explaining issuance."""
        response = explain("What is issuance?")
        
        assert response is not None
        assert len(response) > 0
        assert "issuance" in response.lower() or "issued" in response.lower()
        assert any(keyword in response.lower() for keyword in ["loan", "funded", "customer"])
    
    def test_explain_mom_wow(self):
        """Test explaining MoM and WoW."""
        response = explain("What is MoM and WoW?")
        
        assert response is not None
        assert len(response) > 0
        assert any(keyword in response.lower() for keyword in ["month", "week", "comparison", "change"])
    
    def test_explain_unknown_term(self):
        """Test explaining an unknown term."""
        response = explain("What is xyzabc123?")
        
        assert response is not None
        assert len(response) > 0
        # Should provide a helpful message about not having information
        assert any(keyword in response.lower() for keyword in ["don't have", "try rephrasing", "ask about"])
    
    def test_explain_with_different_k_values(self):
        """Test retrieval with different k values."""
        response_k1 = explain("What is funding rate?", k=1)
        response_k3 = explain("What is funding rate?", k=3)
        response_k5 = explain("What is funding rate?", k=5)
        
        # All should return valid responses
        assert response_k1 is not None and len(response_k1) > 0
        assert response_k3 is not None and len(response_k3) > 0
        assert response_k5 is not None and len(response_k5) > 0
        
        # All should mention funding rate
        assert "funding rate" in response_k1.lower()
        assert "funding rate" in response_k3.lower()
        assert "funding rate" in response_k5.lower()
    
    def test_clean_document_text_with_qa_format(self):
        """Test cleaning Q&A format text."""
        text = "Q: What is funding rate? A: Funding rate is the percentage of submitted applications."
        cleaned = _clean_document_text(text)
        
        assert not cleaned.startswith("Q:")
        assert not cleaned.startswith("A:")
        assert cleaned == "Funding rate is the percentage of submitted applications."
    
    def test_clean_document_text_without_qa_format(self):
        """Test cleaning plain text."""
        text = "  Funding rate is the percentage of submitted applications.  "
        cleaned = _clean_document_text(text)
        
        assert cleaned == "Funding rate is the percentage of submitted applications."
    
    def test_format_explanation_single_document(self):
        """Test formatting with a single document."""
        documents = ["Funding rate is the percentage of submitted applications."]
        formatted = _format_explanation(documents, "What is funding rate?")
        
        assert formatted == "Funding rate is the percentage of submitted applications."
    
    def test_format_explanation_multiple_documents(self):
        """Test formatting with multiple documents."""
        documents = [
            "Funding rate is the percentage of submitted applications.",
            "It is calculated as issued loans divided by submitted applications.",
            "This metric shows overall conversion."
        ]
        formatted = _format_explanation(documents, "What is funding rate?")
        
        assert "Funding rate" in formatted
        assert len(formatted) > len(documents[0])  # Should combine information
    
    def test_format_explanation_with_duplicates(self):
        """Test formatting removes duplicate documents."""
        documents = [
            "Funding rate is the percentage of submitted applications.",
            "Funding rate is the percentage of submitted applications.",
            "It is calculated as issued loans divided by submitted applications."
        ]
        formatted = _format_explanation(documents, "What is funding rate?")
        
        # Should not repeat the same information twice
        assert formatted.count("Funding rate is the percentage of submitted applications.") == 1
    
    def test_explain_amount_vs_count(self):
        """Test explaining the difference between amounts and counts."""
        response = explain("When do metrics refer to amounts vs counts?")
        
        assert response is not None
        assert len(response) > 0
        assert any(keyword in response.lower() for keyword in ["amount", "count", "dollar", "number"])
    
    def test_explain_segments(self):
        """Test explaining segments."""
        response = explain("What segments can I filter by?")
        
        assert response is not None
        assert len(response) > 0
        assert any(keyword in response.lower() for keyword in ["segment", "filter", "channel", "grade"])
    
    def test_explain_time_windows(self):
        """Test explaining time windows."""
        response = explain("What time windows can I query?")
        
        assert response is not None
        assert len(response) > 0
        assert any(keyword in response.lower() for keyword in ["day", "week", "month", "time"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
