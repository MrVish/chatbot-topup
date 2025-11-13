"""
Simple test for Memory Agent without pytest.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from agents.memory_agent import explain
    
    print("Testing Memory Agent...")
    print("=" * 80)
    
    # Test 1: Funding rate
    print("\nTest 1: What is funding rate?")
    response = explain("What is funding rate?")
    print(f"Response: {response}")
    assert "funding rate" in response.lower()
    print("✓ PASSED")
    
    # Test 2: Approval rate
    print("\nTest 2: What is approval rate?")
    response = explain("What is approval rate?")
    print(f"Response: {response}")
    assert "approval rate" in response.lower()
    print("✓ PASSED")
    
    # Test 3: Channels
    print("\nTest 3: What are the different channels?")
    response = explain("What are the different channels?")
    print(f"Response: {response}")
    assert "channel" in response.lower()
    print("✓ PASSED")
    
    # Test 4: FICO
    print("\nTest 4: What is FICO?")
    response = explain("What is FICO?")
    print(f"Response: {response}")
    assert "fico" in response.lower()
    print("✓ PASSED")
    
    # Test 5: Unknown term
    print("\nTest 5: What is xyzabc123?")
    response = explain("What is xyzabc123?")
    print(f"Response: {response}")
    assert "don't have" in response.lower() or "try rephrasing" in response.lower()
    print("✓ PASSED")
    
    print("\n" + "=" * 80)
    print("All tests passed!")
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
