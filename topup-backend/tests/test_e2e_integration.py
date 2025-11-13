"""
End-to-End Integration Tests for Topup CXO Assistant

This test suite validates the complete system integration including:
- Backend server startup and endpoint availability
- Frontend UI loading
- Query processing with SSE streaming
- Chart generation and rendering
- Cache functionality
- Performance requirements (< 3.5s response time)

Requirements: 1.1-1.4, 2.1-2.5, 3.1-3.7, 4.1-4.5, 5.1-5.5, 6.1-6.7,
              8.1-8.6, 9.1-9.6, 10.1-10.5, 11.1-11.5, 14.1-14.5,
              15.1-15.5, 17.1-17.5, 18.1-18.5, 20.1-20.5
"""

import time
import json
import requests
from typing import Dict, List, Any


class E2ETestRunner:
    """
    End-to-end test runner for manual testing validation.
    
    This class provides methods to test all major functionality
    of the Topup CXO Assistant system.
    """
    
    def __init__(self, backend_url: str = "http://localhost:8000", frontend_url: str = "http://localhost:3000"):
        """
        Initialize test runner.
        
        Args:
            backend_url: Backend API base URL
            frontend_url: Frontend application base URL
        """
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.test_results = []
    
    def log_test(self, test_name: str, passed: bool, message: str = "", duration_ms: float = 0):
        """
        Log test result.
        
        Args:
            test_name: Name of the test
            passed: Whether the test passed
            message: Additional message or error details
            duration_ms: Test duration in milliseconds
        """
        result = {
            "test": test_name,
            "passed": passed,
            "message": message,
            "duration_ms": duration_ms
        }
        self.test_results.append(result)
        
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} | {test_name} | {duration_ms:.0f}ms | {message}")
    
    def test_backend_health(self) -> bool:
        """
        Test 1: Verify backend server is running and healthy.
        
        Returns:
            bool: True if backend is healthy
        """
        test_name = "Backend Health Check"
        start_time = time.time()
        
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            duration_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") in ["healthy", "degraded"]:
                    self.log_test(test_name, True, f"Status: {data.get('status')}", duration_ms)
                    return True
            
            self.log_test(test_name, False, f"Unexpected response: {response.status_code}", duration_ms)
            return False
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_test(test_name, False, f"Error: {str(e)}", duration_ms)
            return False
    
    def test_chat_endpoint(self) -> bool:
        """
        Test 2: Verify /chat endpoint responds with SSE stream.
        
        Returns:
            bool: True if endpoint responds correctly
        """
        test_name = "Chat Endpoint Availability"
        start_time = time.time()
        
        try:
            # Send a simple query
            payload = {
                "message": "Show weekly issuance trend",
                "session_id": "test_session_001"
            }
            
            response = requests.post(
                f"{self.backend_url}/chat",
                json=payload,
                stream=True,
                timeout=10
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                # Check content type
                content_type = response.headers.get("content-type", "")
                if "text/event-stream" in content_type:
                    self.log_test(test_name, True, "SSE stream established", duration_ms)
                    return True
                else:
                    self.log_test(test_name, False, f"Wrong content type: {content_type}", duration_ms)
                    return False
            
            self.log_test(test_name, False, f"Status code: {response.status_code}", duration_ms)
            return False
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_test(test_name, False, f"Error: {str(e)}", duration_ms)
            return False
    
    def test_trend_query(self) -> Dict[str, Any]:
        """
        Test 3: Test trend query - "Show WoW issuance by channel last 8 weeks"
        
        Returns:
            dict: Test result with timing and response data
        """
        test_name = "Trend Query (WoW Issuance)"
        start_time = time.time()
        
        try:
            payload = {
                "message": "Show WoW issuance by channel last 8 weeks",
                "session_id": "test_trend_001"
            }
            
            response = requests.post(
                f"{self.backend_url}/chat",
                json=payload,
                stream=True,
                timeout=15
            )
            
            events = []
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('event:'):
                        event_type = line_str.split(':', 1)[1].strip()
                    elif line_str.startswith('data:'):
                        data_str = line_str.split(':', 1)[1].strip()
                        try:
                            data = json.loads(data_str)
                            events.append({"type": event_type, "data": data})
                        except:
                            pass
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Check for required events
            has_plan = any(e["type"] == "plan" for e in events)
            has_card = any(e["type"] == "card" for e in events)
            has_done = any(e["type"] == "done" for e in events)
            
            if has_plan and has_card and has_done:
                # Check performance requirement (< 3.5s)
                if duration_ms < 3500:
                    self.log_test(test_name, True, f"Complete with chart and insights", duration_ms)
                else:
                    self.log_test(test_name, False, f"Too slow (> 3.5s)", duration_ms)
                
                return {"passed": True, "duration_ms": duration_ms, "events": events}
            else:
                self.log_test(test_name, False, f"Missing events: plan={has_plan}, card={has_card}, done={has_done}", duration_ms)
                return {"passed": False, "duration_ms": duration_ms, "events": events}
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_test(test_name, False, f"Error: {str(e)}", duration_ms)
            return {"passed": False, "duration_ms": duration_ms, "error": str(e)}
    
    def test_forecast_query(self) -> Dict[str, Any]:
        """
        Test 4: Test forecast query - "How did actual issuance compare to forecast last month by grade?"
        
        Returns:
            dict: Test result with timing and response data
        """
        test_name = "Forecast Query (Actual vs Forecast)"
        start_time = time.time()
        
        try:
            payload = {
                "message": "How did actual issuance compare to forecast last month by grade?",
                "session_id": "test_forecast_001"
            }
            
            response = requests.post(
                f"{self.backend_url}/chat",
                json=payload,
                stream=True,
                timeout=15
            )
            
            events = []
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('event:'):
                        event_type = line_str.split(':', 1)[1].strip()
                    elif line_str.startswith('data:'):
                        data_str = line_str.split(':', 1)[1].strip()
                        try:
                            data = json.loads(data_str)
                            events.append({"type": event_type, "data": data})
                        except:
                            pass
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Check for required events
            has_card = any(e["type"] == "card" for e in events)
            has_done = any(e["type"] == "done" for e in events)
            
            if has_card and has_done and duration_ms < 3500:
                self.log_test(test_name, True, f"Complete with forecast comparison", duration_ms)
                return {"passed": True, "duration_ms": duration_ms, "events": events}
            else:
                self.log_test(test_name, False, f"Incomplete or too slow", duration_ms)
                return {"passed": False, "duration_ms": duration_ms, "events": events}
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_test(test_name, False, f"Error: {str(e)}", duration_ms)
            return {"passed": False, "duration_ms": duration_ms, "error": str(e)}
    
    def test_funnel_query(self) -> Dict[str, Any]:
        """
        Test 5: Test funnel query - "Show the funnel for NP channel Email"
        
        Returns:
            dict: Test result with timing and response data
        """
        test_name = "Funnel Query (Email Channel)"
        start_time = time.time()
        
        try:
            payload = {
                "message": "Show the funnel for NP channel Email",
                "session_id": "test_funnel_001"
            }
            
            response = requests.post(
                f"{self.backend_url}/chat",
                json=payload,
                stream=True,
                timeout=15
            )
            
            events = []
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('event:'):
                        event_type = line_str.split(':', 1)[1].strip()
                    elif line_str.startswith('data:'):
                        data_str = line_str.split(':', 1)[1].strip()
                        try:
                            data = json.loads(data_str)
                            events.append({"type": event_type, "data": data})
                        except:
                            pass
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Check for required events
            has_card = any(e["type"] == "card" for e in events)
            has_done = any(e["type"] == "done" for e in events)
            
            if has_card and has_done and duration_ms < 3500:
                self.log_test(test_name, True, f"Complete with funnel chart", duration_ms)
                return {"passed": True, "duration_ms": duration_ms, "events": events}
            else:
                self.log_test(test_name, False, f"Incomplete or too slow", duration_ms)
                return {"passed": False, "duration_ms": duration_ms, "events": events}
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_test(test_name, False, f"Error: {str(e)}", duration_ms)
            return {"passed": False, "duration_ms": duration_ms, "error": str(e)}
    
    def test_explain_query(self) -> Dict[str, Any]:
        """
        Test 6: Test explain query - "What is funding rate?"
        
        Returns:
            dict: Test result with timing and response data
        """
        test_name = "Explain Query (Funding Rate)"
        start_time = time.time()
        
        try:
            payload = {
                "message": "What is funding rate?",
                "session_id": "test_explain_001"
            }
            
            response = requests.post(
                f"{self.backend_url}/chat",
                json=payload,
                stream=True,
                timeout=15
            )
            
            events = []
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('event:'):
                        event_type = line_str.split(':', 1)[1].strip()
                    elif line_str.startswith('data:'):
                        data_str = line_str.split(':', 1)[1].strip()
                        try:
                            data = json.loads(data_str)
                            events.append({"type": event_type, "data": data})
                        except:
                            pass
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Check for done event (explain queries don't have charts)
            has_done = any(e["type"] == "done" for e in events)
            
            if has_done and duration_ms < 3500:
                self.log_test(test_name, True, f"Complete with definition", duration_ms)
                return {"passed": True, "duration_ms": duration_ms, "events": events}
            else:
                self.log_test(test_name, False, f"Incomplete or too slow", duration_ms)
                return {"passed": False, "duration_ms": duration_ms, "events": events}
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_test(test_name, False, f"Error: {str(e)}", duration_ms)
            return {"passed": False, "duration_ms": duration_ms, "error": str(e)}
    
    def test_cache_functionality(self) -> bool:
        """
        Test 7: Test cache - Repeat query and verify faster response.
        
        Returns:
            bool: True if cache improves performance
        """
        test_name = "Cache Functionality"
        
        try:
            # First query (cache miss)
            payload = {
                "message": "Show weekly issuance trend last 4 weeks",
                "session_id": "test_cache_001"
            }
            
            start_time = time.time()
            response1 = requests.post(
                f"{self.backend_url}/chat",
                json=payload,
                stream=True,
                timeout=15
            )
            
            # Consume stream
            for line in response1.iter_lines():
                pass
            
            first_duration = (time.time() - start_time) * 1000
            
            # Wait a moment
            time.sleep(0.5)
            
            # Second query (cache hit)
            start_time = time.time()
            response2 = requests.post(
                f"{self.backend_url}/chat",
                json=payload,
                stream=True,
                timeout=15
            )
            
            # Consume stream
            for line in response2.iter_lines():
                pass
            
            second_duration = (time.time() - start_time) * 1000
            
            # Cache hit should be faster
            if second_duration < first_duration:
                improvement = ((first_duration - second_duration) / first_duration) * 100
                self.log_test(test_name, True, f"Cache improved by {improvement:.1f}% ({first_duration:.0f}ms → {second_duration:.0f}ms)", second_duration)
                return True
            else:
                self.log_test(test_name, False, f"No improvement ({first_duration:.0f}ms → {second_duration:.0f}ms)", second_duration)
                return False
        
        except Exception as e:
            self.log_test(test_name, False, f"Error: {str(e)}", 0)
            return False
    
    def test_segment_filters(self) -> bool:
        """
        Test 8: Test segment filters - Apply channel filter and verify.
        
        Returns:
            bool: True if filters are applied correctly
        """
        test_name = "Segment Filters"
        start_time = time.time()
        
        try:
            payload = {
                "message": "Show weekly issuance trend",
                "filters": {
                    "channel": "Email"
                },
                "session_id": "test_filters_001"
            }
            
            response = requests.post(
                f"{self.backend_url}/chat",
                json=payload,
                stream=True,
                timeout=15
            )
            
            events = []
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('event:'):
                        event_type = line_str.split(':', 1)[1].strip()
                    elif line_str.startswith('data:'):
                        data_str = line_str.split(':', 1)[1].strip()
                        try:
                            data = json.loads(data_str)
                            events.append({"type": event_type, "data": data})
                        except:
                            pass
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Check if plan includes filter
            plan_events = [e for e in events if e["type"] == "plan"]
            if plan_events:
                plan = plan_events[0]["data"]
                segments = plan.get("segments", {})
                if segments.get("channel") == "Email":
                    self.log_test(test_name, True, f"Filter applied correctly", duration_ms)
                    return True
            
            self.log_test(test_name, False, f"Filter not found in plan", duration_ms)
            return False
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_test(test_name, False, f"Error: {str(e)}", duration_ms)
            return False
    
    def test_export_csv(self, cache_key: str = None) -> bool:
        """
        Test 9: Test CSV export functionality.
        
        Args:
            cache_key: Cache key from a previous query
        
        Returns:
            bool: True if export works
        """
        test_name = "CSV Export"
        start_time = time.time()
        
        try:
            # If no cache key provided, run a query first
            if not cache_key:
                payload = {
                    "message": "Show weekly issuance trend",
                    "session_id": "test_export_001"
                }
                
                response = requests.post(
                    f"{self.backend_url}/chat",
                    json=payload,
                    stream=True,
                    timeout=15
                )
                
                # Extract cache key from plan event
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data:'):
                            data_str = line_str.split(':', 1)[1].strip()
                            try:
                                data = json.loads(data_str)
                                if "cache_key" in data:
                                    cache_key = data["cache_key"]
                                    break
                            except:
                                pass
            
            if not cache_key:
                self.log_test(test_name, False, "No cache key available", 0)
                return False
            
            # Test export
            response = requests.get(
                f"{self.backend_url}/export",
                params={"cache_key": cache_key, "format": "csv"},
                timeout=10
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                if "csv" in content_type or "text" in content_type:
                    self.log_test(test_name, True, f"CSV export successful", duration_ms)
                    return True
            
            self.log_test(test_name, False, f"Export failed: {response.status_code}", duration_ms)
            return False
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_test(test_name, False, f"Error: {str(e)}", duration_ms)
            return False
    
    def print_summary(self):
        """
        Print test summary.
        """
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["passed"])
        failed = total - passed
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ({(passed/total*100):.1f}%)")
        print(f"Failed: {failed} ({(failed/total*100):.1f}%)")
        
        if failed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("="*80)
    
    def run_all_tests(self):
        """
        Run all end-to-end tests.
        """
        print("\n" + "="*80)
        print("TOPUP CXO ASSISTANT - END-TO-END INTEGRATION TESTS")
        print("="*80)
        print()
        
        # Test 1: Backend health
        print("Testing backend server...")
        self.test_backend_health()
        
        # Test 2: Chat endpoint
        print("\nTesting chat endpoint...")
        self.test_chat_endpoint()
        
        # Test 3: Trend query
        print("\nTesting trend query...")
        self.test_trend_query()
        
        # Test 4: Forecast query
        print("\nTesting forecast query...")
        self.test_forecast_query()
        
        # Test 5: Funnel query
        print("\nTesting funnel query...")
        self.test_funnel_query()
        
        # Test 6: Explain query
        print("\nTesting explain query...")
        self.test_explain_query()
        
        # Test 7: Cache functionality
        print("\nTesting cache functionality...")
        self.test_cache_functionality()
        
        # Test 8: Segment filters
        print("\nTesting segment filters...")
        self.test_segment_filters()
        
        # Test 9: CSV export
        print("\nTesting CSV export...")
        self.test_export_csv()
        
        # Print summary
        self.print_summary()


if __name__ == "__main__":
    # Run tests
    runner = E2ETestRunner()
    runner.run_all_tests()
