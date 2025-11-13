"""
Example usage of the Guardrail Agent.

This script demonstrates how to use the guardrail agent to validate
query plans and SQL queries before execution.
"""

from models.schemas import Plan, SegmentFilters
from agents.guardrail import validate


def example_valid_query():
    """Example of a valid query that passes all guardrail checks."""
    print("\n=== Example 1: Valid Query ===")
    
    plan = Plan(
        intent="trend",
        table="cps_tb",
        metric="issued_amnt",
        date_col="issued_d",
        window="last_30d",
        granularity="weekly",
        segments=SegmentFilters(channel="Email", grade="P1"),
        chart="line"
    )
    
    sql = """
    SELECT 
        strftime('%Y-%W', issued_d) AS week,
        SUM(CASE WHEN issued_flag = 1 THEN issued_amnt ELSE 0 END) AS issued_amnt
    FROM cps_tb
    WHERE issued_d >= date('now', '-30 days')
      AND channel = 'Email'
      AND grade = 'P1'
    GROUP BY week
    ORDER BY week
    """
    
    result = validate(plan, sql)
    
    if result:
        print("✓ Query validation PASSED")
        print(f"  Intent: {plan.intent}")
        print(f"  Segments: channel={plan.segments.channel}, grade={plan.segments.grade}")
        print("  Query is safe to execute")
    else:
        print(f"✗ Query validation FAILED: {result.error_message}")


def example_sql_injection_attempt():
    """Example of SQL injection attempt that gets blocked."""
    print("\n=== Example 2: SQL Injection Attempt (Blocked) ===")
    
    plan = Plan(
        intent="trend",
        table="cps_tb",
        metric="issued_amnt",
        date_col="issued_d",
        window="last_30d",
        granularity="weekly",
        chart="line"
    )
    
    # Malicious SQL with DROP statement
    sql = "SELECT * FROM cps_tb; DROP TABLE cps_tb"
    
    result = validate(plan, sql)
    
    if result:
        print("✓ Query validation PASSED")
    else:
        print(f"✗ Query validation FAILED: {result.error_message}")
        if result.security_event:
            print("  ⚠️  SECURITY EVENT DETECTED - Query logged for review")


def example_invalid_segment():
    """Example of invalid segment value that gets rejected."""
    print("\n=== Example 3: Invalid Segment Value (Rejected) ===")
    
    plan = Plan(
        intent="trend",
        table="cps_tb",
        metric="issued_amnt",
        date_col="issued_d",
        window="last_30d",
        granularity="weekly",
        segments=SegmentFilters(channel="InvalidChannel"),  # Invalid channel
        chart="line"
    )
    
    sql = "SELECT * FROM cps_tb WHERE channel = 'InvalidChannel'"
    
    result = validate(plan, sql)
    
    if result:
        print("✓ Query validation PASSED")
    else:
        print(f"✗ Query validation FAILED")
        print(f"  Error: {result.error_message}")


def example_multiple_statements():
    """Example of multiple SQL statements that get blocked."""
    print("\n=== Example 4: Multiple Statements (Blocked) ===")
    
    plan = Plan(
        intent="trend",
        table="cps_tb",
        metric="issued_amnt",
        date_col="issued_d",
        window="last_30d",
        granularity="weekly",
        chart="line"
    )
    
    # Multiple statements separated by semicolon
    sql = "SELECT * FROM cps_tb; SELECT * FROM forecast_df"
    
    result = validate(plan, sql)
    
    if result:
        print("✓ Query validation PASSED")
    else:
        print(f"✗ Query validation FAILED: {result.error_message}")
        if result.security_event:
            print("  ⚠️  SECURITY EVENT DETECTED - Query logged for review")


def example_valid_multiple_segments():
    """Example of valid query with multiple segment filters."""
    print("\n=== Example 5: Multiple Valid Segments ===")
    
    plan = Plan(
        intent="trend",
        table="cps_tb",
        metric="issued_amnt",
        date_col="issued_d",
        window="last_30d",
        granularity="weekly",
        segments=SegmentFilters(
            channel="Email",
            grade="P1",
            term=60,
            prod_type="Prime",
            cr_fico_band="700-759"
        ),
        chart="line"
    )
    
    sql = """
    SELECT * FROM cps_tb 
    WHERE channel = 'Email' 
      AND grade = 'P1'
      AND term = 60
      AND prod_type = 'Prime'
      AND cr_fico_band = '700-759'
    """
    
    result = validate(plan, sql)
    
    if result:
        print("✓ Query validation PASSED")
        print(f"  All {len([s for s in [plan.segments.channel, plan.segments.grade, plan.segments.term, plan.segments.prod_type, plan.segments.cr_fico_band] if s])} segment filters are valid")
    else:
        print(f"✗ Query validation FAILED: {result.error_message}")


def main():
    """Run all examples."""
    print("=" * 60)
    print("Guardrail Agent Usage Examples")
    print("=" * 60)
    
    example_valid_query()
    example_sql_injection_attempt()
    example_invalid_segment()
    example_multiple_statements()
    example_valid_multiple_segments()
    
    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
