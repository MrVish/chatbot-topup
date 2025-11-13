"""
Tests for Guardrail Agent.

This module tests the guardrail validation functionality including:
- SQL injection detection
- Multiple statement detection
- Segment filter validation
- Time window enforcement
- Security event logging
"""

import pytest
from models.schemas import Plan, SegmentFilters
from agents.guardrail import validate, ValidationResult


class TestSQLSafety:
    """Test SQL safety checks for dangerous keywords."""
    
    def test_valid_select_query(self):
        """Test that valid SELECT queries pass validation."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line"
        )
        sql = "SELECT date, SUM(issued_amnt) FROM cps_tb WHERE issued_d >= date('now', '-30 days') GROUP BY date"
        
        result = validate(plan, sql)
        assert result.is_valid
        assert result.error_message is None
        assert not result.security_event
    
    def test_reject_insert_statement(self):
        """Test that INSERT statements are rejected."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line"
        )
        sql = "INSERT INTO cps_tb (issued_amnt) VALUES (1000)"
        
        result = validate(plan, sql)
        assert not result.is_valid
        assert "INSERT" in result.error_message
        assert result.security_event
    
    def test_reject_update_statement(self):
        """Test that UPDATE statements are rejected."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line"
        )
        sql = "UPDATE cps_tb SET issued_amnt = 1000 WHERE channel = 'Email'"
        
        result = validate(plan, sql)
        assert not result.is_valid
        assert "UPDATE" in result.error_message
        assert result.security_event
    
    def test_reject_delete_statement(self):
        """Test that DELETE statements are rejected."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line"
        )
        sql = "DELETE FROM cps_tb WHERE channel = 'Email'"
        
        result = validate(plan, sql)
        assert not result.is_valid
        assert "DELETE" in result.error_message
        assert result.security_event
    
    def test_reject_drop_statement(self):
        """Test that DROP statements are rejected."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line"
        )
        sql = "DROP TABLE cps_tb"
        
        result = validate(plan, sql)
        assert not result.is_valid
        assert "DROP" in result.error_message
        assert result.security_event
    
    def test_reject_alter_statement(self):
        """Test that ALTER statements are rejected."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line"
        )
        sql = "ALTER TABLE cps_tb ADD COLUMN new_col TEXT"
        
        result = validate(plan, sql)
        assert not result.is_valid
        assert "ALTER" in result.error_message
        assert result.security_event
    
    def test_reject_create_statement(self):
        """Test that CREATE statements are rejected."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line"
        )
        sql = "CREATE TABLE malicious (id INTEGER)"
        
        result = validate(plan, sql)
        assert not result.is_valid
        assert "CREATE" in result.error_message
        assert result.security_event
    
    def test_allow_column_with_keyword_substring(self):
        """Test that columns containing keywords as substrings are allowed."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line"
        )
        # "inserted_date" contains "INSERT" but should be allowed
        sql = "SELECT inserted_date, SUM(issued_amnt) FROM cps_tb GROUP BY inserted_date"
        
        result = validate(plan, sql)
        assert result.is_valid


class TestMultipleStatements:
    """Test detection of multiple SQL statements."""
    
    def test_reject_semicolon_in_middle(self):
        """Test that semicolons in the middle of SQL are rejected."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line"
        )
        # Use a benign second statement to test semicolon detection specifically
        sql = "SELECT * FROM cps_tb; SELECT * FROM forecast_df"
        
        result = validate(plan, sql)
        assert not result.is_valid
        assert "multiple statements" in result.error_message.lower()
        assert result.security_event
    
    def test_allow_trailing_semicolon(self):
        """Test that trailing semicolons are allowed."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line"
        )
        sql = "SELECT * FROM cps_tb WHERE issued_d >= date('now', '-30 days');"
        
        result = validate(plan, sql)
        assert result.is_valid
    
    def test_allow_no_semicolon(self):
        """Test that queries without semicolons are allowed."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line"
        )
        sql = "SELECT * FROM cps_tb WHERE issued_d >= date('now', '-30 days')"
        
        result = validate(plan, sql)
        assert result.is_valid


class TestSegmentValidation:
    """Test segment filter value validation."""
    
    def test_valid_channel(self):
        """Test that valid channel values pass validation."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line",
            segments=SegmentFilters(channel="Email")
        )
        sql = "SELECT * FROM cps_tb WHERE channel = 'Email'"
        
        result = validate(plan, sql)
        assert result.is_valid
    
    def test_invalid_channel(self):
        """Test that invalid channel values are rejected."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line",
            segments=SegmentFilters(channel="InvalidChannel")
        )
        sql = "SELECT * FROM cps_tb WHERE channel = 'InvalidChannel'"
        
        result = validate(plan, sql)
        assert not result.is_valid
        assert "Invalid channel value" in result.error_message
        assert "Email" in result.error_message  # Should list allowed values
    
    def test_valid_grade(self):
        """Test that valid grade values pass validation."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line",
            segments=SegmentFilters(grade="P1")
        )
        sql = "SELECT * FROM cps_tb WHERE grade = 'P1'"
        
        result = validate(plan, sql)
        assert result.is_valid
    
    def test_invalid_grade(self):
        """Test that invalid grade values are rejected."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line",
            segments=SegmentFilters(grade="P7")
        )
        sql = "SELECT * FROM cps_tb WHERE grade = 'P7'"
        
        result = validate(plan, sql)
        assert not result.is_valid
        assert "Invalid grade value" in result.error_message
    
    def test_valid_term(self):
        """Test that valid term values pass validation."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line",
            segments=SegmentFilters(term=60)
        )
        sql = "SELECT * FROM cps_tb WHERE term = 60"
        
        result = validate(plan, sql)
        assert result.is_valid
    
    def test_invalid_term(self):
        """Test that invalid term values are rejected."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line",
            segments=SegmentFilters(term=99)
        )
        sql = "SELECT * FROM cps_tb WHERE term = 99"
        
        result = validate(plan, sql)
        assert not result.is_valid
        assert "Invalid term value" in result.error_message
    
    def test_valid_prod_type(self):
        """Test that valid prod_type values pass validation."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line",
            segments=SegmentFilters(prod_type="Prime")
        )
        sql = "SELECT * FROM cps_tb WHERE prod_type = 'Prime'"
        
        result = validate(plan, sql)
        assert result.is_valid
    
    def test_invalid_prod_type(self):
        """Test that invalid prod_type values are rejected."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line",
            segments=SegmentFilters(prod_type="Subprime")
        )
        sql = "SELECT * FROM cps_tb WHERE prod_type = 'Subprime'"
        
        result = validate(plan, sql)
        assert not result.is_valid
        assert "Invalid prod_type value" in result.error_message
    
    def test_valid_repeat_type(self):
        """Test that valid repeat_type values pass validation."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line",
            segments=SegmentFilters(repeat_type="New")
        )
        sql = "SELECT * FROM cps_tb WHERE repeat_type = 'New'"
        
        result = validate(plan, sql)
        assert result.is_valid
    
    def test_invalid_repeat_type(self):
        """Test that invalid repeat_type values are rejected."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line",
            segments=SegmentFilters(repeat_type="Unknown")
        )
        sql = "SELECT * FROM cps_tb WHERE repeat_type = 'Unknown'"
        
        result = validate(plan, sql)
        assert not result.is_valid
        assert "Invalid repeat_type value" in result.error_message
    
    def test_valid_fico_band(self):
        """Test that valid FICO band values pass validation."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line",
            segments=SegmentFilters(cr_fico_band="700-759")
        )
        sql = "SELECT * FROM cps_tb WHERE cr_fico_band = '700-759'"
        
        result = validate(plan, sql)
        assert result.is_valid
    
    def test_invalid_fico_band(self):
        """Test that invalid FICO band values are rejected."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line",
            segments=SegmentFilters(cr_fico_band="800-850")
        )
        sql = "SELECT * FROM cps_tb WHERE cr_fico_band = '800-850'"
        
        result = validate(plan, sql)
        assert not result.is_valid
        assert "Invalid cr_fico_band value" in result.error_message
    
    def test_valid_purpose(self):
        """Test that valid purpose values pass validation."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line",
            segments=SegmentFilters(purpose="debt_consolidation")
        )
        sql = "SELECT * FROM cps_tb WHERE purpose = 'debt_consolidation'"
        
        result = validate(plan, sql)
        assert result.is_valid
    
    def test_invalid_purpose(self):
        """Test that invalid purpose values are rejected."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line",
            segments=SegmentFilters(purpose="vacation")
        )
        sql = "SELECT * FROM cps_tb WHERE purpose = 'vacation'"
        
        result = validate(plan, sql)
        assert not result.is_valid
        assert "Invalid purpose value" in result.error_message
    
    def test_multiple_valid_segments(self):
        """Test that multiple valid segments pass validation."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line",
            segments=SegmentFilters(
                channel="Email",
                grade="P1",
                term=60,
                prod_type="Prime"
            )
        )
        sql = "SELECT * FROM cps_tb WHERE channel = 'Email' AND grade = 'P1' AND term = 60"
        
        result = validate(plan, sql)
        assert result.is_valid
    
    def test_one_invalid_segment_fails_all(self):
        """Test that one invalid segment fails the entire validation."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line",
            segments=SegmentFilters(
                channel="Email",  # Valid
                grade="P99",      # Invalid
                term=60           # Valid
            )
        )
        sql = "SELECT * FROM cps_tb WHERE channel = 'Email' AND grade = 'P99'"
        
        result = validate(plan, sql)
        assert not result.is_valid
        assert "Invalid grade value" in result.error_message


class TestTimeWindowValidation:
    """Test time window enforcement."""
    
    def test_valid_7_day_window(self):
        """Test that 7-day window passes validation."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_7d",
            granularity="daily",
            chart="line"
        )
        sql = "SELECT * FROM cps_tb WHERE issued_d >= date('now', '-7 days')"
        
        result = validate(plan, sql)
        assert result.is_valid
    
    def test_valid_30_day_window(self):
        """Test that 30-day window passes validation."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_30d",
            granularity="weekly",
            chart="line"
        )
        sql = "SELECT * FROM cps_tb WHERE issued_d >= date('now', '-30 days')"
        
        result = validate(plan, sql)
        assert result.is_valid
    
    def test_valid_3_month_window(self):
        """Test that 3-month window passes validation."""
        plan = Plan(
            intent="trend",
            table="cps_tb",
            metric="issued_amnt",
            date_col="issued_d",
            window="last_3_full_months",
            granularity="weekly",
            chart="line"
        )
        sql = "SELECT * FROM cps_tb WHERE issued_d >= date('now', '-3 months')"
        
        result = validate(plan, sql)
        assert result.is_valid


class TestValidationResult:
    """Test ValidationResult class behavior."""
    
    def test_validation_result_boolean_true(self):
        """Test that valid results evaluate to True."""
        result = ValidationResult(is_valid=True)
        assert bool(result) is True
        assert result  # Direct boolean check
    
    def test_validation_result_boolean_false(self):
        """Test that invalid results evaluate to False."""
        result = ValidationResult(is_valid=False, error_message="Test error")
        assert bool(result) is False
        assert not result  # Direct boolean check
    
    def test_validation_result_with_security_event(self):
        """Test ValidationResult with security event flag."""
        result = ValidationResult(
            is_valid=False,
            error_message="SQL injection attempt",
            security_event=True
        )
        assert not result.is_valid
        assert result.error_message == "SQL injection attempt"
        assert result.security_event


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
