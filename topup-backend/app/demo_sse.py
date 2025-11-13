"""
Demo script to test SSE streaming from the chat endpoint.

This script demonstrates how to consume Server-Sent Events from the
/chat endpoint and display the streaming results.

Usage:
    python app/demo_sse.py
"""

import json
import requests
import sys


def test_sse_streaming():
    """
    Test SSE streaming with a sample query.
    """
    url = "http://localhost:8000/chat"
    
    # Sample query
    data = {
        "message": "Show weekly issuance trend for the last 8 weeks",
        "session_id": "demo_session_001"
    }
    
    print("="*80)
    print("Testing SSE Streaming")
    print("="*80)
    print(f"Query: {data['message']}")
    print("-"*80)
    
    try:
        # Make streaming request
        with requests.post(url, json=data, stream=True, timeout=30) as response:
            if response.status_code != 200:
                print(f"Error: HTTP {response.status_code}")
                print(response.text)
                return
            
            print("Streaming events:")
            print("-"*80)
            
            event_type = None
            event_count = 0
            
            for line in response.iter_lines():
                if not line:
                    continue
                
                line = line.decode('utf-8')
                
                if line.startswith('event:'):
                    event_type = line.split(':', 1)[1].strip()
                    event_count += 1
                    
                elif line.startswith('data:'):
                    data_str = line.split(':', 1)[1].strip()
                    
                    try:
                        event_data = json.loads(data_str)
                        
                        # Pretty print based on event type
                        if event_type == "partial":
                            print(f"📝 Status: {event_data.get('text', '')}")
                        
                        elif event_type == "plan":
                            print(f"📋 Plan Generated:")
                            print(f"   Intent: {event_data.get('intent', 'N/A')}")
                            print(f"   Table: {event_data.get('table', 'N/A')}")
                            print(f"   Metric: {event_data.get('metric', 'N/A')}")
                            print(f"   Window: {event_data.get('window', 'N/A')}")
                        
                        elif event_type == "card":
                            print(f"📊 Results:")
                            if event_data.get('chart'):
                                print(f"   Chart: Generated ({event_data['chart'].get('data', [{}])[0].get('type', 'unknown')} chart)")
                            if event_data.get('insight'):
                                insight = event_data['insight']
                                print(f"   Insight: {insight.get('title', 'N/A')}")
                                print(f"   Summary: {insight.get('summary', 'N/A')}")
                        
                        elif event_type == "done":
                            print(f"✅ Complete!")
                        
                        elif event_type == "error":
                            print(f"❌ Error: {event_data.get('message', 'Unknown error')}")
                    
                    except json.JSONDecodeError:
                        print(f"⚠️  Invalid JSON: {data_str}")
            
            print("-"*80)
            print(f"Total events received: {event_count}")
            print("="*80)
    
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server")
        print("   Make sure the server is running: uvicorn app.main:app --reload")
        sys.exit(1)
    
    except requests.exceptions.Timeout:
        print("❌ Error: Request timed out")
        sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


def test_health_check():
    """
    Test the health check endpoint.
    """
    url = "http://localhost:8000/health"
    
    print("\nTesting Health Check:")
    print("-"*80)
    
    try:
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server is healthy")
            print(f"   Cache size: {data.get('cache_size', 0)}")
        else:
            print(f"⚠️  Server returned status {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running")
        return False
    
    return True


def main():
    """
    Main function to run all tests.
    """
    print("\n" + "="*80)
    print("Topup CXO Assistant API - SSE Demo")
    print("="*80 + "\n")
    
    # Check if server is running
    if not test_health_check():
        print("\n⚠️  Please start the server first:")
        print("   cd topup-backend")
        print("   uvicorn app.main:app --reload")
        sys.exit(1)
    
    print()
    
    # Test SSE streaming
    test_sse_streaming()
    
    print("\n✅ Demo completed successfully!\n")


if __name__ == "__main__":
    main()
