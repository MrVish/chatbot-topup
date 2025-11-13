"""
Test suite for additional FastAPI endpoints.

This module tests the /chart, /suggest, and /export endpoints
to ensure they meet requirements 14.1-14.5, 15.1-15.5, and 16.1-16.5.
"""

import json
import pytest
from fastapi.testclient import TestClient

from app.main import app
from tools import cache_tool
from models.schemas import Plan, SegmentFilters, Insight, Driver


# Create test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test."""
    cache_tool.clear()
    yield
    cache_tool.clear()


@pytest.fixture
def sample_cached_result():
    """Create a sample cached result for testing."""
    # Create a sample plan
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
    
    # Create sample data
    df_dict = [
        {"week": "2025-W01", "issued_amt": 1000000},
        {"week": "2025-W02", "issued_amt": 1200000},
        {"week": "2025-W03", "issued_amt": 1100000},
    ]
    
    # Create sample chart spec
    chart_spec = {
        "data": [
            {
                "x": ["2025-W01", "2025-W02", "2025-W03"],
                "y": [1000000, 1200000, 1100000],
                "type": "scatter",
                "mode": "lines+markers"
            }
        ],
        "layout": {
            "title": "Weekly Issuance Trend",
            "xaxis": {"title": "Week"},
            "yaxis": {"title": "Issued Amount"}
        }
    }
    
    # Create sample insight
    insight = Insight(
        title="Weekly Issuance Trend",
        summary="Issuance increased 20% in W02, then decreased 8% in W03",
        bullets=[
            "Peak issuance of $1.2M in W02",
            "Average weekly issuance: $1.1M"
        ],
        drivers=[
            Driver(segment="Channel: Email", value=500000, delta=100000, delta_pct=25.0),
            Driver(segment="Grade: P1", value=300000, delta=-50000, delta_pct=-14.3)
        ]
    )
    
    # Cache the result
    cache_key = plan.cache_key()
    cache_tool.set(cache_key, {
        "df_dict": df_dict,
        "chart_spec": chart_spec,
        "insight": insight.model_dump()
    })
    
    return cache_key, df_dict, chart_spec, insight


class TestChartEndpoint:
    """Test suite for GET /chart endpoint."""
    
    def test_get_chart_success(self, sample_cached_result):
        """Test successful chart retrieval."""
        cache_key, df_dict, chart_spec, insight = sample_cached_result
        
        response = client.get(f"/chart?cache_key={cache_key}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "chart" in data
        assert "insight" in data
        assert "data_preview" in data
        
        assert data["chart"] == chart_spec
        assert data["insight"]["title"] == insight.title
        assert len(data["data_preview"]) <= 10  # Preview limited to 10 rows
    
    def test_get_chart_not_found(self):
        """Test chart retrieval with invalid cache key."""
        response = client.get("/chart?cache_key=invalid_key_12345")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_chart_expired(self, sample_cached_result):
        """Test chart retrieval after cache expiration."""
        cache_key, _, _, _ = sample_cached_result
        
        # Clear cache to simulate expiration
        cache_tool.clear()
        
        response = client.get(f"/chart?cache_key={cache_key}")
        
        assert response.status_code == 404


class TestSuggestEndpoint:
    """Test suite for POST /suggest endpoint."""
    
    def test_suggest_trend_intent(self):
        """Test suggestions for trend intent."""
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
    
    def test_suggest_forecast_intent(self):
        """Test suggestions for forecast_vs_actual intent."""
        request_data = {
            "context": "How did actual compare to forecast?",
            "last_intent": "forecast_vs_actual"
        }
        
        response = client.post("/suggest", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["suggestions"]) == 3
        # Check that suggestions are contextual
        suggestions_text = " ".join(data["suggestions"]).lower()
        assert any(word in suggestions_text for word in ["forecast", "variance", "accuracy", "trend"])
    
    def test_suggest_funnel_intent(self):
        """Test suggestions for funnel intent."""
        request_data = {
            "context": "Show the funnel",
            "last_intent": "funnel"
        }
        
        response = client.post("/suggest", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["suggestions"]) == 3
    
    def test_suggest_no_intent(self):
        """Test suggestions with no intent specified."""
        request_data = {
            "context": "General query"
        }
        
        response = client.post("/suggest", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["suggestions"]) == 3


class TestExportEndpoint:
    """Test suite for GET /export endpoint."""
    
    def test_export_csv_success(self, sample_cached_result):
        """Test successful CSV export."""
        cache_key, df_dict, _, _ = sample_cached_result
        
        response = client.get(f"/export?cache_key={cache_key}&format=csv")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        
        # Check filename
        content_disposition = response.headers.get("content-disposition", "")
        assert "topup_export_" in content_disposition
        assert ".csv" in content_disposition
        
        # Check CSV content
        csv_content = response.text
        assert "week" in csv_content
        assert "issued_amt" in csv_content
        assert "2025-W01" in csv_content
    
    def test_export_png_returns_spec(self, sample_cached_result):
        """Test PNG export returns chart spec for client-side rendering."""
        cache_key, _, chart_spec, _ = sample_cached_result
        
        response = client.get(f"/export?cache_key={cache_key}&format=png")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "chart_spec" in data
        assert "filename" in data
        assert data["chart_spec"] == chart_spec
    
    def test_export_not_found(self):
        """Test export with invalid cache key."""
        response = client.get("/export?cache_key=invalid_key&format=csv")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_export_invalid_format(self, sample_cached_result):
        """Test export with invalid format."""
        cache_key, _, _, _ = sample_cached_result
        
        response = client.get(f"/export?cache_key={cache_key}&format=invalid")
        
        assert response.status_code == 400
        assert "invalid format" in response.json()["detail"].lower()
    
    def test_export_no_data(self):
        """Test export when cached result has no data."""
        # Create a plan and cache result without data
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
        
        cache_key = plan.cache_key()
        cache_tool.set(cache_key, {
            "df_dict": None,  # No data
            "chart_spec": None,
            "insight": None
        })
        
        response = client.get(f"/export?cache_key={cache_key}&format=csv")
        
        assert response.status_code == 400
        assert "no data" in response.json()["detail"].lower()


class TestHealthEndpoint:
    """Test suite for GET /health endpoint."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "cache_size" in data
        assert "service" in data
        assert "version" in data


class TestStructuredLogging:
    """Test suite for structured logging."""
    
    def test_logging_format(self, sample_cached_result, caplog):
        """Test that structured logs are in JSON format."""
        import logging
        
        # Set log level to capture INFO logs
        caplog.set_level(logging.INFO)
        
        cache_key, _, _, _ = sample_cached_result
        
        # Make a request that will generate logs
        response = client.get(f"/chart?cache_key={cache_key}")
        
        assert response.status_code == 200
        
        # Check that logs were generated
        assert len(caplog.records) > 0
        
        # Look for structured log entries (JSON format)
        json_logs = []
        for record in caplog.records:
            msg = record.message
            if msg.startswith("{") and msg.endswith("}"):
                try:
                    log_data = json.loads(msg)
                    json_logs.append(log_data)
                except json.JSONDecodeError:
                    pass
        
        # Verify we have at least one structured log
        assert len(json_logs) > 0, "No structured JSON logs found"
        
        # Verify JSON structure of structured logs
        for log_data in json_logs:
            assert "timestamp" in log_data, "Missing timestamp in log"
            assert "event_type" in log_data, "Missing event_type in log"
            assert "session_id" in log_data, "Missing session_id in log"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
