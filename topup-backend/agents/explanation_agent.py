import json
import logging
import os
from typing import Dict, List, Optional

import pandas as pd
from openai import OpenAI

from models.schemas import Insight

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

SYSTEM_PROMPT = """
You are an expert business analyst providing explanations for data insights and trends. Your role is to help executives understand the "why" behind the numbers.

When asked to explain trends, anomalies, or patterns, you should:

1. **Analyze the data context** - Look at the specific metrics, time periods, and segments involved
2. **Identify potential causes** - Consider business factors that could drive the observed patterns
3. **Provide actionable insights** - Suggest what actions could be taken based on the analysis
4. **Use executive language** - Communicate in business terms, not technical jargon

Common business factors to consider:
- **Seasonal patterns** - Holiday seasons, end of quarter/year effects
- **Marketing campaigns** - Channel performance, campaign launches
- **Economic factors** - Market conditions, interest rates, competition
- **Operational changes** - Process improvements, policy changes, staffing
- **Product factors** - New products, pricing changes, feature updates
- **Customer behavior** - Changing preferences, demographics, satisfaction

Format your response as JSON:
{
    "summary": "One-sentence executive summary of the explanation",
    "bullets": [
        "Primary reason or factor (most likely cause)",
        "Secondary contributing factor",
        "Recommended action or investigation"
    ],
    "confidence": "high|medium|low",
    "next_steps": "Suggested follow-up analysis or actions"
}

Keep explanations:
- **Specific** - Reference actual data points and time periods
- **Actionable** - Include what can be done about it
- **Balanced** - Acknowledge uncertainty where appropriate
- **Executive-focused** - Emphasize business impact and decisions
"""

def generate_explanation(
    user_query: str, 
    conversation_history: List[Dict],
    current_data: Optional[pd.DataFrame] = None
) -> Insight:
    """
    Generate explanations for trends, anomalies, or patterns.
    
    Args:
        user_query: User's explanation request ("why did X happen?")
        conversation_history: Previous conversation for context
        current_data: Current query results if available
        
    Returns:
        Insight: Explanation insight object
    """
    logger.info(f"Generating explanation for: {user_query}")
    
    try:
        client = _get_client()
        
        # Extract context from conversation history
        context = _extract_context_for_explanation(conversation_history, current_data)
        
        # Build explanation prompt
        prompt = f"""
User Question: {user_query}

Context from Previous Analysis:
{context}

Provide a business explanation for the observed pattern or trend. Focus on actionable insights and potential causes.
"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,  # Slightly higher for more creative explanations
            max_tokens=400
        )
        
        content = response.choices[0].message.content
        result = json.loads(content)
        
        # Create Insight object
        insight = Insight(
            title="Explanation Analysis",
            summary=result.get("summary", "Analysis complete"),
            bullets=result.get("bullets", ["No specific insights available"]),
            drivers=[]  # Explanations don't typically have numeric drivers
        )
        
        logger.info("Explanation generated successfully")
        return insight
        
    except Exception as e:
        logger.error(f"Failed to generate explanation: {str(e)}")
        # Return fallback explanation
        return Insight(
            title="Explanation Analysis",
            summary="Unable to generate detailed explanation at this time",
            bullets=[
                "Multiple factors could contribute to this pattern",
                "Consider reviewing historical data for similar trends",
                "Recommend deeper analysis of specific segments or time periods"
            ],
            drivers=[]
        )

def _extract_context_for_explanation(
    conversation_history: List[Dict], 
    current_data: Optional[pd.DataFrame]
) -> str:
    """
    Extract relevant context from conversation history for explanation.
    
    Args:
        conversation_history: Previous messages
        current_data: Current query results
        
    Returns:
        str: Formatted context for explanation
    """
    context_parts = []
    
    # Extract insights from recent assistant messages
    for msg in reversed(conversation_history[-6:]):  # Last 3 exchanges
        if msg.get('role') == 'assistant':
            content = msg.get('content', '')
            
            # Look for key patterns in assistant responses
            if any(keyword in content.lower() for keyword in ['drop', 'spike', 'increase', 'decrease', 'trend']):
                # Truncate long content
                if len(content) > 300:
                    content = content[:300] + "..."
                context_parts.append(f"Previous insight: {content}")
                break  # Only need the most recent relevant insight
    
    # Add data summary if available
    if current_data is not None and not current_data.empty:
        data_summary = f"""
Current Data Summary:
- Time period: {len(current_data)} data points
- Columns: {', '.join(current_data.columns[:5])}{'...' if len(current_data.columns) > 5 else ''}
"""
        
        # Add basic statistics for numeric columns
        numeric_cols = current_data.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            first_numeric = numeric_cols[0]
            if len(current_data) > 1:
                first_val = current_data[first_numeric].iloc[0]
                last_val = current_data[first_numeric].iloc[-1]
                change = ((last_val - first_val) / first_val * 100) if first_val != 0 else 0
                data_summary += f"- {first_numeric}: {first_val:.0f} → {last_val:.0f} ({change:+.1f}%)"
        
        context_parts.append(data_summary)
    
    return "\n\n".join(context_parts) if context_parts else "No specific context available from previous analysis."

def create_explanation_plan(user_query: str) -> Dict:
    """
    Create a simple plan for explanation queries.
    
    Args:
        user_query: User's explanation request
        
    Returns:
        Dict: Simple plan for explanation processing
    """
    return {
        "intent": "explain",
        "table": "cps_tb",  # Default table
        "metric": "explanation",
        "date_col": "period",
        "window": "context",  # Use context from conversation
        "granularity": "daily",
        "segments": {},
        "chart": "none",  # Explanations don't need charts
        "explanation": True
    }
