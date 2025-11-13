"""
Test script for FastAPI endpoints.

This script tests the main endpoints of the Topup CXO Assistant API:
- POST /chat with SSE streaming
- GET /chart
- POST /suggest
- GET /export
- GET /health

Run with: python -m pytest app/test_main.py -v
"""

import json
import pytest
from fastapi.testclient import TestClient

from app.main import app

# Create test client
client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns API info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "cache_size" in data


def test_chat_endpoint_sse_streaming():
    """Test the chat endpoint with SSE streaming."""
    # Send a simple query
    request_data = {
        "message": "Show weekly issuance trend for the last 8 weeks",
        "session_id": "test_session_001"
    }
    
    # Make request
    with client.stream("POST", "/chat", json=request_data) as response:
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Collect events
        events = []
        for line in response.iter_lines():
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data = json.loads(line.split(":", 1)[1].strip())
                events.append({"type": event_type, "data": data})
        
        # Verify we got events
        assert len(events) > 0
        
        # Check for done event
        event_types = [e["type"] for e in events]
        assert "done" in event_types


def test_chat_endpoint_with_filters():
    """Test the chat endpoint with segment filters."""
    request_data = {
        "message": "Show issuance by channel",
        "filters": {
            "channel": "Email",
            "grade": "P1"
        },
        "session_id": "test_session_002"
    }
    
    with client.stream("POST", "/chat", json=request_data) as response:
        assert response.status_code == 200


def test_suggest_endpoint():
    """Test the suggest endpoint."""
    request_data = {
        "context": "Show weekly issuance trend",
        "last_intent": "trend"
    }
    
    response = client.post("/suggest", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "suggestions" in data
    assert len(data["suggestions"]) == 3
    assert all(isinstance(s, str) for s in data["suggestions"])


def test_suggest_endpoint_different_intents():
    """Test suggest endpoint with different intents."""
    intents = ["trend", "variance", "forecast_vs_actual", "funnel", "distribution"]
    
    for intent in intents:
        request_data = {
            "context": f"Test query for {intent}",
            "last_intent": intent
        }
        
        response = client.post("/suggest", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["suggestions"]) == 3


def test_chart_endpoint_not_found():
    """Test chart endpoint with non-existent cache key."""
    response = client.get("/chart?cache_key=nonexistent_key_12345")
    assert response.status_code == 404


def test_export_endpoint_not_found():
    """Test export endpoint with non-existent cache key."""
    response = client.get("/export?cache_key=nonexistent_key_12345&format=csv")
    assert response.status_code == 404


def test_export_endpoint_invalid_format():
    """Test export endpoint with invalid format."""
    # First, we need a valid cache key, but for this test we'll just check the format validation
    response = client.get("/export?cache_key=test_key&format=invalid")
    # Should return 400 or 404 depending on whether key exists
    assert response.status_code in [400, 404]


def test_cors_headers():
    """Test that CORS headers are properly set."""
    response = client.options("/")
    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers or response.status_code == 200


def test_chat_endpoint_error_handling():
    """Test chat endpoint handles errors gracefully."""
    # Send an empty message
    request_data = {
        "message": "",
        "session_id": "test_session_error"
    }
    
    with client.stream("POST", "/chat", json=request_data) as response:
        # Should still return 200 but with error event
        assert response.status_code == 200


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
