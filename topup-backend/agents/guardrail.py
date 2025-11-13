"""
Guardrail Agent for query validation and security enforcement.

This module provides the Guardrail Agent that validates query plans and
SQL queries before execution to ensure:
- Read-only SQL (no INSERT, UPDATE, DELETE, DROP, ALTER)
- No SQL injection attempts (semicolons, multiple statements)
- Valid segment filter values against database allowed values
- Reasonable time windows (max 1 year unless explicit)
- Security event logging for rejected queries
"""

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from models.schemas import Plan

# Configure logging
logger = logging.getLogger(__name__)

# Allowed segment values (from SEGMENT_VALUES.md)
ALLOWED_SEGMENTS = {
    "channel": [
        "OMB", "Email", "Search", "D2LC", "DM", "LT", 
        "Experian", "Karma", "Small Partners"
    ],
    "grade": ["P1", "P2", "P3", "P4", "P5", "P6"],
    "prod_type": ["Prime", "NP", "D2P"],
    "repeat_type": ["Repeat", "New"],
    "term": [36, 48, 60, 72, 84],
    "cr_fico_band": ["<640", "640-699", "700-759", "760+"],
    "purpose": [
        "debt_consolidation", "home_improvement", "major_purchase",
        "medical", "car", "other"
    ]
}

# Dangerous SQL keywords that indicate write operations
DANGEROUS_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
    "CREATE", "TRUNCATE", "REPLACE", "MERGE"
]

# Maximum time window in days (1 year)
MAX_TIME_WINDOW_DAYS = 365


class ValidationResult:
    """
    Result of guardrail validation.
    
    Attributes:
        is_valid: Whether the validation passed
        error_message: Error message if validation failed
        security_event: Whether this was a security violation
    """
    
    def __init__(
        self,
        is_valid: bool,
        error_message: Optional[str] = None,
        security_event: bool = False
    ):
        self.is_valid = is_valid
        self.error_message = error_message
        self.security_event = security_event
    
    def __bool__(self) -> bool:
        """Allow using ValidationResult in boolean context."""
        return self.is_valid


def validate(plan: Plan, sql: str) -> ValidationResult:
    """
    Validate query plan and SQL for security and correctness.
    
    Performs comprehensive validation including:
    1. SQL injection checks (dangerous keywords, semicolons)
    2. Segment filter value validation
    3. Time window enforcement
    4. Security event logging
    
    Args:
        plan: Structured query plan to validate
        sql: Generated SQL query to validate
        
    Returns:
        ValidationResult: Validation result with error message if rejected
        
    Examples:
        >>> result = validate(plan, "SELECT * FROM cps_tb")
        >>> if result:
        ...     # Validation passed
        ...     execute_query(sql)
        >>> else:
        ...     # Validation failed
        ...     print(result.error_message)
    """
    logger.info(
        "Validating query plan and SQL",
        extra={
            "intent": plan.intent,
            "table": plan.table,
            "metric": plan.metric,
            "window": plan.window
        }
    )
    
    # 1. Check for dangerous SQL keywords
    sql_check = _check_sql_safety(sql)
    if not sql_check.is_valid:
        _log_security_event(plan, sql, sql_check.error_message)
        return sql_check
    
    # 2. Check for multiple statements (semicolons)
    semicolon_check = _check_multiple_statements(sql)
    if not semicolon_check.is_valid:
        _log_security_event(plan, sql, semicolon_check.error_message)
        return semicolon_check
    
    # 3. Validate segment filter values
    segment_check = _validate_segment_filters(plan)
    if not segment_check.is_valid:
        return segment_check
    
    # 4. Enforce time window limits
    window_check = _validate_time_window(plan)
    if not window_check.is_valid:
        return window_check
    
    logger.info(
        "Query validation passed",
        extra={
            "intent": plan.intent,
            "table": plan.table,
            "segments": plan.segments.model_dump(exclude_none=True)
        }
    )
    
    return ValidationResult(is_valid=True)


def _check_sql_safety(sql: str) -> ValidationResult:
    """
    Check SQL for dangerous keywords that indicate write operations.
    
    Args:
        sql: SQL query to check
        
    Returns:
        ValidationResult: Validation result
    """
    sql_upper = sql.upper()
    
    for keyword in DANGEROUS_KEYWORDS:
        # Use word boundaries to avoid false positives
        # (e.g., "INSERTED_DATE" should not trigger "INSERT")
        pattern = r'\b' + keyword + r'\b'
        if re.search(pattern, sql_upper):
            return ValidationResult(
                is_valid=False,
                error_message=f"SQL query contains forbidden keyword: {keyword}",
                security_event=True
            )
    
    return ValidationResult(is_valid=True)


def _check_multiple_statements(sql: str) -> ValidationResult:
    """
    Check for semicolons or multiple SQL statements.
    
    Args:
        sql: SQL query to check
        
    Returns:
        ValidationResult: Validation result
    """
    # Check for semicolons (except at the very end)
    sql_stripped = sql.strip()
    
    # Remove trailing semicolon if present
    if sql_stripped.endswith(';'):
        sql_stripped = sql_stripped[:-1]
    
    # Now check if there are any remaining semicolons
    if ';' in sql_stripped:
        return ValidationResult(
            is_valid=False,
            error_message="SQL query contains multiple statements (semicolons not allowed)",
            security_event=True
        )
    
    return ValidationResult(is_valid=True)


def _validate_segment_filters(plan: Plan) -> ValidationResult:
    """
    Validate segment filter values against allowed values.
    
    Args:
        plan: Query plan with segment filters
        
    Returns:
        ValidationResult: Validation result with specific error message
    """
    segments = plan.segments
    
    # Check channel ("ALL" is a special value meaning "group by all channels")
    if segments.channel and segments.channel != "ALL" and segments.channel not in ALLOWED_SEGMENTS["channel"]:
        return ValidationResult(
            is_valid=False,
            error_message=(
                f"Invalid channel value: '{segments.channel}'. "
                f"Allowed values: {', '.join(ALLOWED_SEGMENTS['channel'])} or 'ALL' for grouping"
            )
        )
    
    # Check grade ("ALL" is a special value meaning "group by all grades")
    if segments.grade and segments.grade != "ALL" and segments.grade not in ALLOWED_SEGMENTS["grade"]:
        return ValidationResult(
            is_valid=False,
            error_message=(
                f"Invalid grade value: '{segments.grade}'. "
                f"Allowed values: {', '.join(ALLOWED_SEGMENTS['grade'])} or 'ALL' for grouping"
            )
        )
    
    # Check prod_type ("ALL" is a special value meaning "group by all product types")
    if segments.prod_type and segments.prod_type != "ALL" and segments.prod_type not in ALLOWED_SEGMENTS["prod_type"]:
        return ValidationResult(
            is_valid=False,
            error_message=(
                f"Invalid prod_type value: '{segments.prod_type}'. "
                f"Allowed values: {', '.join(ALLOWED_SEGMENTS['prod_type'])} or 'ALL' for grouping"
            )
        )
    
    # Check repeat_type
    if segments.repeat_type and segments.repeat_type not in ALLOWED_SEGMENTS["repeat_type"]:
        return ValidationResult(
            is_valid=False,
            error_message=(
                f"Invalid repeat_type value: '{segments.repeat_type}'. "
                f"Allowed values: {', '.join(ALLOWED_SEGMENTS['repeat_type'])}"
            )
        )
    
    # Check term
    if segments.term and segments.term not in ALLOWED_SEGMENTS["term"]:
        return ValidationResult(
            is_valid=False,
            error_message=(
                f"Invalid term value: {segments.term}. "
                f"Allowed values: {', '.join(map(str, ALLOWED_SEGMENTS['term']))}"
            )
        )
    
    # Check cr_fico_band
    if segments.cr_fico_band and segments.cr_fico_band not in ALLOWED_SEGMENTS["cr_fico_band"]:
        return ValidationResult(
            is_valid=False,
            error_message=(
                f"Invalid cr_fico_band value: '{segments.cr_fico_band}'. "
                f"Allowed values: {', '.join(ALLOWED_SEGMENTS['cr_fico_band'])}"
            )
        )
    
    # Check purpose
    if segments.purpose and segments.purpose not in ALLOWED_SEGMENTS["purpose"]:
        return ValidationResult(
            is_valid=False,
            error_message=(
                f"Invalid purpose value: '{segments.purpose}'. "
                f"Allowed values: {', '.join(ALLOWED_SEGMENTS['purpose'])}"
            )
        )
    
    return ValidationResult(is_valid=True)


def _validate_time_window(plan: Plan) -> ValidationResult:
    """
    Enforce maximum time window of 1 year unless explicitly requested.
    
    Note: This is a soft limit. The function currently allows all predefined
    windows since they are all under 1 year. For custom date ranges in future
    versions, this would enforce the 365-day limit.
    
    Args:
        plan: Query plan with time window
        
    Returns:
        ValidationResult: Validation result
    """
    # Map time windows to approximate days
    window_days = {
        "last_7d": 7,
        "last_full_week": 7,
        "last_30d": 30,
        "last_full_month": 31,
        "last_3_full_months": 93,
    }
    
    days = window_days.get(plan.window, 30)  # Default to 30 if unknown
    
    if days > MAX_TIME_WINDOW_DAYS:
        return ValidationResult(
            is_valid=False,
            error_message=(
                f"Time window exceeds maximum allowed ({MAX_TIME_WINDOW_DAYS} days). "
                f"Requested window: {plan.window} (~{days} days). "
                f"Please use a shorter time window or explicitly request a longer period."
            )
        )
    
    return ValidationResult(is_valid=True)


def _log_security_event(plan: Plan, sql: str, reason: str) -> None:
    """
    Log security events for rejected queries.
    
    Args:
        plan: Query plan that was rejected
        sql: SQL query that was rejected
        reason: Reason for rejection
    """
    logger.warning(
        "SECURITY EVENT: Query rejected",
        extra={
            "event_type": "query_rejected",
            "reason": reason,
            "intent": plan.intent,
            "table": plan.table,
            "metric": plan.metric,
            "segments": plan.segments.model_dump(exclude_none=True),
            "sql_preview": sql[:200] if len(sql) > 200 else sql,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
