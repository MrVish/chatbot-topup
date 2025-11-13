import json
import logging
import os
import re
from typing import Dict, List, Optional

from openai import OpenAI

from models.schemas import Plan

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client (lazy initialization)
_client = None

def _get_client():
    """Get or create OpenAI client."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        _client = OpenAI(api_key=api_key)
    return _client

# Database schema for LLM
SCHEMA_PROMPT = """
Database Schema (SQLite):

Table: cps_tb (Customer acquisition pipeline data)
Columns:
- period: TEXT (date in YYYY-MM-DD format)
- app_create_d: DATE (application creation date)
- app_submit_d: DATE (application submission date)
- app_submit_amnt: FLOAT (submitted loan amount in dollars)
- app_submit_count: INTEGER (number of applications submitted)
- apps_approved_d: DATE (approval date)
- apps_approved_amnt: FLOAT (approved loan amount in dollars)
- apps_approved_count: INTEGER (number of applications approved)
- issued_d: DATE (issuance/funding date)
- issued_amnt: FLOAT (issued loan amount in dollars)
- issued_count: INTEGER (number of loans issued)
- channel: TEXT (marketing channel: Email, Social, Direct, Referral)
- grade: TEXT (credit grade: A, B, C, D, E)
- prod_type: TEXT (product type: Prime, NP, D2P)
- repeat_type: TEXT (customer type: New, Repeat)
- term: INTEGER (loan term in months)
- cr_fico_band: TEXT (FICO score band: 300-579, 580-669, 670-739, 740-799, 800+)
- purpose: TEXT (loan purpose: debt_consolidation, home_improvement, etc.)

Table: forecast_df (Forecast vs actual data)
Columns:
- period: TEXT (date in YYYY-MM-DD format)
- metric: TEXT (metric name)
- forecast: FLOAT (forecasted value)
- actual: FLOAT (actual value)
- variance: FLOAT (actual - forecast)
- variance_pct: FLOAT (variance percentage)

Important Notes:
- Use SQLite syntax
- All amounts are in dollars (no need to convert)
- Dates are in YYYY-MM-DD format
- Use proper date filtering with DATE() function
- Always include period column for time-based analysis
- Use appropriate aggregations (SUM for amounts, COUNT for counts)
"""

SYSTEM_PROMPT = f"""
You are an expert SQL analyst for a marketing analytics database. Generate SAFE, READ-ONLY SQL queries based on natural language requests.

{SCHEMA_PROMPT}

Rules:
1. ONLY generate SELECT statements (no INSERT, UPDATE, DELETE, DROP, ALTER, CREATE)
2. Use proper SQLite syntax
3. Always include a period/date column for time-based analysis
4. Use appropriate WHERE clauses for date filtering
5. Use proper aggregations (SUM for amounts, COUNT for counts)
6. Include ORDER BY for time series data
7. Limit results to reasonable numbers (use LIMIT if needed)
8. Infer appropriate chart type based on query structure

Chart Type Guidelines:
- line: Time series data with dates
- bar: Categorical comparisons
- pie: Distribution/breakdown by category
- funnel: Conversion metrics (submit -> approve -> issue)
- scatter: Relationship between two metrics

Return JSON format:
{{
    "sql": "SELECT ...",
    "chart_type": "line|bar|pie|funnel|scatter",
    "metric": "primary_metric_name",
    "explanation": "Brief explanation of what the query does"
}}

Examples:

User: "Show me revenue by channel last month"
Response:
{{
    "sql": "SELECT channel, SUM(issued_amnt) as revenue FROM cps_tb WHERE DATE(issued_d) >= DATE('now', '-1 month') GROUP BY channel ORDER BY revenue DESC",
    "chart_type": "bar",
    "metric": "revenue",
    "explanation": "Revenue breakdown by marketing channel for the last month"
}}

User: "What's the trend of applications over time?"
Response:
{{
    "sql": "SELECT DATE(app_submit_d) as period, SUM(app_submit_count) as applications FROM cps_tb WHERE DATE(app_submit_d) >= DATE('now', '-3 months') GROUP BY DATE(app_submit_d) ORDER BY period",
    "chart_type": "line",
    "metric": "applications",
    "explanation": "Daily application submission trend over the last 3 months"
}}
"""

def generate_sql(user_query: str, conversation_history: Optional[List[Dict]] = None) -> Dict:
    """
    Generate SQL query from natural language using LLM.
    
    Args:
        user_query: Natural language query
        conversation_history: Previous conversation for context
        
    Returns:
        Dict with sql, chart_type, metric, and explanation
    """
    logger.info(f"Generating SQL for query: {user_query}")
    
    try:
        client = _get_client()
        
        # Build context from conversation history
        context = ""
        if conversation_history:
            recent = conversation_history[-4:]  # Last 2 exchanges
            if recent:
                context = "\n\nConversation Context:\n"
                for msg in recent:
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')[:200]  # Truncate
                    context += f"{role}: {content}\n"
        
        user_message = f"{user_query}{context}"
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        result = json.loads(content)
        
        # Validate the generated SQL
        if not _validate_sql(result.get('sql', '')):
            raise ValueError("Generated SQL failed safety validation")
        
        logger.info(f"Generated SQL successfully: {result.get('sql', '')[:100]}...")
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate SQL: {str(e)}")
        raise ValueError(f"Could not generate SQL query: {str(e)}")

def _validate_sql(sql: str) -> bool:
    """
    Validate that the generated SQL is safe to execute.
    
    Args:
        sql: SQL query to validate
        
    Returns:
        bool: True if safe, False otherwise
    """
    if not sql or not isinstance(sql, str):
        return False
    
    sql_upper = sql.upper().strip()
    
    # Must start with SELECT
    if not sql_upper.startswith('SELECT'):
        return False
    
    # Check for dangerous keywords
    dangerous_keywords = [
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 
        'TRUNCATE', 'REPLACE', 'MERGE', 'EXEC', 'EXECUTE',
        'PRAGMA', 'ATTACH', 'DETACH'
    ]
    
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            logger.warning(f"Dangerous keyword '{keyword}' found in SQL")
            return False
    
    # Check for allowed tables only
    allowed_tables = ['cps_tb', 'forecast_df']
    
    # Simple table name extraction (could be improved with proper SQL parsing)
    from_match = re.search(r'FROM\s+(\w+)', sql_upper)
    if from_match:
        table_name = from_match.group(1).lower()
        if table_name not in [t.lower() for t in allowed_tables]:
            logger.warning(f"Unauthorized table '{table_name}' in SQL")
            return False
    
    # Check for suspicious patterns
    suspicious_patterns = [
        r'--',  # SQL comments
        r'/\*',  # Multi-line comments
        r';.*SELECT',  # Multiple statements
        r'UNION.*SELECT',  # Union with potentially dangerous SELECT
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, sql_upper):
            logger.warning(f"Suspicious pattern '{pattern}' found in SQL")
            return False
    
    return True

def create_plan_from_sql(sql_result: Dict, user_query: str) -> Plan:
    """
    Create a Plan object from LLM-generated SQL result.
    
    Args:
        sql_result: Result from generate_sql()
        user_query: Original user query
        
    Returns:
        Plan: Plan object for the pipeline
    """
    return Plan(
        intent="custom_query",  # New intent for LLM-generated queries
        table="cps_tb",  # Default table
        metric=sql_result.get('metric', 'custom_metric'),
        date_col="period",  # Use period column from SQL
        window="custom",  # Custom time window
        granularity="daily",  # Default granularity
        segments={
            "channel": None,
            "grade": None,
            "prod_type": None,
            "repeat_type": None,
            "term": None,
            "cr_fico_band": None,
            "purpose": None
        },
        chart=sql_result.get('chart_type', 'line'),
        custom_sql=sql_result.get('sql'),  # Store the custom SQL
        explanation=sql_result.get('explanation', '')
    )
