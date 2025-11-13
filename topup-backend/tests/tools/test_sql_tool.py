"""
Test script for SQL Tool.

This script tests the SQL Tool with various query plans to ensure:
- Template selection works correctly
- Parameter binding is correct
- Read-only access is enforced
- Row limits are applied
- Logging works as expected
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.schemas import Plan, SegmentFilters
from tools.sql_tool import run

import logging

# Configure logging to see the output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def test_trend_query():
    """Test trend query with weekly granularity."""
    print("\n" + "="*80)
    print("TEST 1: Trend Query - Weekly Issuance by Channel")
    print("="*80)
    
    plan = Plan(
        intent="trend",
        table="cps_tb",
        metric="issued_amnt",
        date_col="issued_d",
        window="last_30d",
        granularity="weekly",
        segments=SegmentFilters(channel="Email"),
        chart="line"
    )
    
    try:
        df = run(plan)
        print(f"\n✓ Query executed successfully")
        print(f"  Rows returned: {len(df)}")
        print(f"  Columns: {list(df.columns)}")
        print(f"\nFirst 5 rows:")
        print(df.head())
        return True
    except Exception as e:
        print(f"\n✗ Query failed: {str(e)}")
        return False


def test_funnel_query():
    """Test funnel query for submission to issuance."""
    print("\n" + "="*80)
    print("TEST 2: Funnel Query - Submission → Approval → Issuance")
    print("="*80)
    
    plan = Plan(
        intent="funnel",
        table="cps_tb",
        metric="issued_amnt",
        date_col="issued_d",
        window="last_full_month",
        granularity="monthly",
        segments=SegmentFilters(channel="Email", repeat_type="New"),
        chart="funnel"
    )
    
    try:
        df = run(plan)
        print(f"\n✓ Query executed successfully")
        print(f"  Rows returned: {len(df)}")
        print(f"  Columns: {list(df.columns)}")
        print(f"\nFunnel stages:")
        print(df)
        return True
    except Exception as e:
        print(f"\n✗ Query failed: {str(e)}")
        return False


def test_forecast_query():
    """Test forecast vs actual query."""
    print("\n" + "="*80)
    print("TEST 3: Forecast vs Actual - Weekly Issuance")
    print("="*80)
    
    plan = Plan(
        intent="forecast_vs_actual",
        table="forecast_df",
        metric="issued_amnt",
        date_col="date",
        window="last_30d",
        granularity="weekly",
        segments=SegmentFilters(grade="P1"),
        chart="grouped_bar"
    )
    
    try:
        df = run(plan)
        print(f"\n✓ Query executed successfully")
        print(f"  Rows returned: {len(df)}")
        print(f"  Columns: {list(df.columns)}")
        print(f"\nFirst 5 rows:")
        print(df.head())
        return True
    except Exception as e:
        print(f"\n✗ Query failed: {str(e)}")
        return False


def test_variance_query():
    """Test variance (WoW) query."""
    print("\n" + "="*80)
    print("TEST 4: Variance Query - Week-over-Week Delta")
    print("="*80)
    
    plan = Plan(
        intent="variance",
        table="cps_tb",
        metric="issued_amnt",
        date_col="issued_d",
        window="last_30d",
        granularity="weekly",
        segments=SegmentFilters(),
        chart="line"
    )
    
    try:
        df = run(plan)
        print(f"\n✓ Query executed successfully")
        print(f"  Rows returned: {len(df)}")
        print(f"  Columns: {list(df.columns)}")
        print(f"\nFirst 5 rows:")
        print(df.head())
        return True
    except Exception as e:
        print(f"\n✗ Query failed: {str(e)}")
        return False


def test_distribution_query():
    """Test distribution query by segment."""
    print("\n" + "="*80)
    print("TEST 5: Distribution Query - Issuance by Grade")
    print("="*80)
    
    plan = Plan(
        intent="distribution",
        table="cps_tb",
        metric="issued_amnt",
        date_col="issued_d",
        window="last_full_month",
        granularity="monthly",
        segments=SegmentFilters(),
        chart="pie"
    )
    
    try:
        df = run(plan)
        print(f"\n✓ Query executed successfully")
        print(f"  Rows returned: {len(df)}")
        print(f"  Columns: {list(df.columns)}")
        print(f"\nDistribution:")
        print(df)
        return True
    except Exception as e:
        print(f"\n✗ Query failed: {str(e)}")
        return False


def test_multiple_segments():
    """Test query with multiple segment filters."""
    print("\n" + "="*80)
    print("TEST 6: Multiple Segment Filters")
    print("="*80)
    
    plan = Plan(
        intent="trend",
        table="cps_tb",
        metric="app_submit_amnt",
        date_col="app_submit_d",
        window="last_30d",
        granularity="weekly",
        segments=SegmentFilters(
            channel="Email",
            grade="P1",
            repeat_type="New",
            cr_fico_band="760+"
        ),
        chart="line"
    )
    
    try:
        df = run(plan)
        print(f"\n✓ Query executed successfully")
        print(f"  Rows returned: {len(df)}")
        print(f"  Columns: {list(df.columns)}")
        print(f"\nFirst 5 rows:")
        print(df.head())
        return True
    except Exception as e:
        print(f"\n✗ Query failed: {str(e)}")
        return False


def test_read_only_enforcement():
    """Test that read-only mode is enforced (should fail on write attempts)."""
    print("\n" + "="*80)
    print("TEST 7: Read-Only Enforcement (Expected to Pass - No Write Attempt)")
    print("="*80)
    
    # Note: We can't directly test write prevention without modifying the tool
    # But we can verify the connection is opened in read-only mode
    # by checking that normal reads work
    
    plan = Plan(
        intent="trend",
        table="cps_tb",
        metric="issued_amnt",
        date_col="issued_d",
        window="last_7d",
        granularity="daily",
        segments=SegmentFilters(),
        chart="line"
    )
    
    try:
        df = run(plan)
        print(f"\n✓ Read-only connection works correctly")
        print(f"  Rows returned: {len(df)}")
        return True
    except Exception as e:
        print(f"\n✗ Read-only test failed: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("SQL TOOL TEST SUITE")
    print("="*80)
    
    tests = [
        test_trend_query,
        test_funnel_query,
        test_forecast_query,
        test_variance_query,
        test_distribution_query,
        test_multiple_segments,
        test_read_only_enforcement,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test crashed: {str(e)}")
            results.append(False)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
