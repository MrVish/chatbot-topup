"""
Quick test to verify conversation enhancement features.
Tests Phase 1, 2, and 3 implementations.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.router import classify
from agents.planner import make_plan
from agents.sql_generator import generate_sql, create_plan_from_sql, _validate_sql
from agents.explanation_agent import generate_explanation, create_explanation_plan
from models.schemas import Plan

def test_phase1_conversation_memory():
    """Test Phase 1: Conversation memory in router and planner."""
    print("\n=== PHASE 1: CONVERSATION MEMORY ===")
    
    # Test 1: Router with conversation history
    print("\n1. Testing Router with conversation history...")
    conversation_history = [
        {"role": "user", "content": "Show me issuances last month"},
        {"role": "assistant", "content": "Here are the issuances for last month"}
    ]
    
    try:
        intent = classify("What about last quarter?", conversation_history)
        print(f"   ✓ Router classified intent: {intent}")
    except Exception as e:
        print(f"   ✗ Router failed: {str(e)}")
        return False
    
    # Test 2: Planner with conversation history
    print("\n2. Testing Planner with conversation history...")
    try:
        plan = make_plan("What about last quarter?", "trend", conversation_history)
        print(f"   ✓ Planner created plan: metric={plan.metric}, window={plan.window}")
    except Exception as e:
        print(f"   ✗ Planner failed: {str(e)}")
        return False
    
    print("\n✅ Phase 1 tests passed!")
    return True

def test_phase2_llm_sql_generation():
    """Test Phase 2: LLM SQL generation for custom queries."""
    print("\n=== PHASE 2: LLM SQL GENERATION ===")
    
    # Test 1: Generate SQL from natural language
    print("\n1. Testing SQL generation...")
    try:
        sql_result = generate_sql(
            "Show me the top 5 channels by revenue last month"
        )
        print(f"   ✓ Generated SQL: {sql_result['sql'][:80]}...")
        print(f"   ✓ Chart type: {sql_result['chart_type']}")
        print(f"   ✓ Metric: {sql_result['metric']}")
    except Exception as e:
        print(f"   ✗ SQL generation failed: {str(e)}")
        return False
    
    # Test 2: Create plan from SQL result
    print("\n2. Testing plan creation from SQL...")
    try:
        plan = create_plan_from_sql(sql_result, "test query")
        print(f"   ✓ Created plan: intent={plan.intent}, chart={plan.chart}")
        print(f"   ✓ Custom SQL stored: {bool(plan.custom_sql)}")
    except Exception as e:
        print(f"   ✗ Plan creation failed: {str(e)}")
        return False
    
    # Test 3: SQL validation
    print("\n3. Testing SQL validation...")
    safe_sql = "SELECT channel, SUM(issued_amnt) FROM cps_tb GROUP BY channel"
    dangerous_sql = "DROP TABLE cps_tb"
    
    if _validate_sql(safe_sql):
        print(f"   ✓ Safe SQL validated correctly")
    else:
        print(f"   ✗ Safe SQL rejected incorrectly")
        return False
    
    if not _validate_sql(dangerous_sql):
        print(f"   ✓ Dangerous SQL blocked correctly")
    else:
        print(f"   ✗ Dangerous SQL allowed incorrectly")
        return False
    
    print("\n✅ Phase 2 tests passed!")
    return True

def test_phase3_explanations():
    """Test Phase 3: Explanation agent for follow-up questions."""
    print("\n=== PHASE 3: CONVERSATIONAL EXPLANATIONS ===")
    
    # Test 1: Generate explanation
    print("\n1. Testing explanation generation...")
    conversation_history = [
        {"role": "user", "content": "Show me issuances over time"},
        {"role": "assistant", "content": "Issuances dropped 25% in March"}
    ]
    
    try:
        insight = generate_explanation(
            "Why did issuances drop in March?",
            conversation_history
        )
        print(f"   ✓ Generated explanation: {insight.summary}")
        print(f"   ✓ Number of bullets: {len(insight.bullets)}")
    except Exception as e:
        print(f"   ✗ Explanation generation failed: {str(e)}")
        return False
    
    # Test 2: Create explanation plan
    print("\n2. Testing explanation plan creation...")
    try:
        plan = create_explanation_plan("Why did this happen?")
        print(f"   ✓ Created plan: intent={plan['intent']}, chart={plan['chart']}")
    except Exception as e:
        print(f"   ✗ Plan creation failed: {str(e)}")
        return False
    
    print("\n✅ Phase 3 tests passed!")
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("CONVERSATION ENHANCEMENT FEATURES - VERIFICATION TEST")
    print("=" * 60)
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  WARNING: OPENAI_API_KEY not set")
        print("   Some tests will fail without API access")
        print("   Set the key in .env file or environment")
        return
    
    results = []
    
    # Run Phase 1 tests
    results.append(("Phase 1: Conversation Memory", test_phase1_conversation_memory()))
    
    # Run Phase 2 tests
    results.append(("Phase 2: LLM SQL Generation", test_phase2_llm_sql_generation()))
    
    # Run Phase 3 tests
    results.append(("Phase 3: Explanations", test_phase3_explanations()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nNext steps:")
        print("1. Start the backend: cd topup-backend && uvicorn app.main:app --reload")
        print("2. Start the frontend: cd topup-frontend && npm run dev")
        print("3. Test conversation features in the UI")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("Review the errors above and fix issues before proceeding")

if __name__ == "__main__":
    main()
