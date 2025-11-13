"""
Router Agent for intent classification.

This module provides the Router Agent that classifies user queries into
one of seven intent categories using OpenAI function calling. It handles:
- Intent classification: trend, variance, forecast_vs_actual, funnel, 
  distribution, relationship, explain
- Business-friendly term recognition (app submits, app approvals, issuances)
- Few-shot learning with example queries
"""

import logging
import os
from typing import Dict, List, Literal, Optional

from openai import OpenAI

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client (lazy initialization to avoid errors during import)
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

# Intent type definition
IntentType = Literal[
    "trend",
    "variance", 
    "forecast_vs_actual",
    "forecast_gap_analysis",
    "funnel",
    "distribution",
    "relationship",
    "multi_metric",
    "explain"
]

# System prompt with few-shot examples
ROUTER_SYSTEM_PROMPT = """You are an intent classification expert for a CXO marketing analytics assistant.

Your task is to classify user queries into one of seven intent categories:

1. **trend**: User wants to see how a metric changes over time
   - Examples: "Show weekly issuance trend", "How have app submits changed over the last 3 months?"
   - Keywords: trend, over time, weekly, monthly, last X weeks/months, historical

2. **variance**: User wants to compare current vs prior period (MoM/WoW)
   - Examples: "What's the WoW change in approvals?", "Compare this month to last month"
   - Keywords: WoW, MoM, week-over-week, month-over-month, compare, change, vs last

3. **forecast_vs_actual**: User wants to compare forecast predictions to actual results
   - Examples: "How did we do vs forecast?", "Compare actual issuance to forecast"
   - Keywords: forecast, predicted, expected, vs actual, accuracy, outlook

4. **forecast_gap_analysis**: User wants to understand WHERE the forecast gap is coming from (decomposition)
   - Examples: "Where are we seeing the largest gap between forecast and actual?", "What's driving the forecast variance?", "Which segments are missing forecast?"
   - Keywords: gap, variance, driving, contributing to, where, which segments, decomposition, breakdown of gap

5. **funnel**: User wants to see conversion funnel (submission → approval → issuance)
   - Examples: "Show the funnel", "What's our conversion rate?", "Submission to issuance"
   - Keywords: funnel, conversion, submission to approval, approval to issuance

6. **distribution**: User wants to see composition or breakdown by segment
   - Examples: "What's the channel mix?", "Breakdown by grade", "Distribution of FICO bands"
   - Keywords: distribution, breakdown, composition, mix, by channel/grade/segment

7. **relationship**: User wants to see correlation between two metrics
   - Examples: "How does FICO relate to approval rate?", "APR vs issuance"
   - Keywords: relationship, correlation, vs, compared to, impact of

8. **multi_metric**: User wants to compare multiple metrics on the same chart
   - Examples: "Show app submits vs approvals vs issuances", "Compare submissions, approvals, and issuances", "App submit $ vs #"
   - Keywords: vs, versus, compare [metric1] and [metric2], [metric1] vs [metric2] vs [metric3]
   - NOTE: Use this when user explicitly wants to see 2+ metrics together on one chart

9. **explain**: User wants ONLY definition or explanation of a metric/term (NO data requested)
   - Examples: "What is funding rate?", "Define approval rate", "Explain FICO band", "Why did X happen?", "What caused the drop?"
   - Keywords: what is, define, explain, meaning of, tell me about, why did, what caused, reason for
   - NOTE: If query asks for data/metrics along with explanation, use analytical intent instead
   - Counter-examples (NOT explain): 
     * "Show me funding rate" → use trend
     * "What is the current approval rate?" → use trend/distribution
     * "What about last quarter?" → use trend (conversational follow-up)
     * "Break that down by channel" → use distribution (conversational follow-up)
   - IMPORTANT: Conversational follow-ups like "what about...", "show me that...", "break it down..." are NOT explain queries

**Business-Friendly Terms:**
- "app submits" or "submissions" = application submission amounts or counts
- "app approvals" or "approvals" = application approval amounts or counts  
- "issuances" or "funded" = issued loan amounts or counts
- "funding rate" = percentage of submissions that result in issuance
- "approval rate" = percentage of offers that result in approval

**Classification Rules:**
- If query mentions "by channel", "by grade", "by segment" → distribution (even if WoW/MoM mentioned)
- If query mentions "WoW", "MoM", "week-over-week", "month-over-month" WITHOUT segmentation → variance
- If query mentions "forecast", "predicted", "expected", "outlook" → forecast_vs_actual
- If query mentions "funnel", "conversion" → funnel
- If query mentions "breakdown", "distribution", "mix", "composition" → distribution
- If query mentions "correlation", "relationship", "impact" → relationship
- If query asks for data about metrics (show, display, get, give me) → trend or distribution
- If query is a conversational follow-up (what about, show that, break it down) → use appropriate analytical intent based on context
- If query asks "why did", "what caused", "reason for" about a specific event/trend → explain
- If query asks "what is", "define", "explain" WITHOUT asking for data → explain
- Default to "trend" for time-series queries

**IMPORTANT**: "by X" indicates segmentation, which means distribution intent, NOT variance.

**IMPORTANT**: Only use "explain" intent for:
1. Pure definition queries: "What is funding rate?" (no data requested)
2. Causal explanation queries: "Why did issuances drop?" (asking for reasons)

Do NOT use "explain" for:
- Conversational follow-ups: "What about last quarter?" → trend
- Data requests: "Show me funding rate" → trend
- Breakdowns: "Break that down by channel" → distribution

Classify the user query into exactly one intent category."""

# Function definition for OpenAI function calling
INTENT_FUNCTION = {
    "name": "classify_intent",
    "description": "Classify the user query into one of seven intent categories",
    "parameters": {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "enum": [
                    "trend",
                    "variance",
                    "forecast_vs_actual",
                    "funnel",
                    "distribution",
                    "relationship",
                    "multi_metric",
                    "explain"
                ],
                "description": "The classified intent category"
            },
            "reasoning": {
                "type": "string",
                "description": "Brief explanation of why this intent was chosen"
            }
        },
        "required": ["intent", "reasoning"]
    }
}


def classify(user_query: str, conversation_history: Optional[List[Dict]] = None) -> str:
    """
    Classify user query into one of seven intent categories with conversation context.
    
    Uses OpenAI function calling with enum constraint to ensure valid
    intent classification. The function analyzes the user's natural
    language query and determines the most appropriate intent category.
    
    Args:
        user_query: Natural language query from the user
        conversation_history: List of previous messages for context
        
    Returns:
        Intent string (one of: trend, variance, forecast_vs_actual, 
        funnel, distribution, relationship, explain)
        
    Raises:
        ValueError: If OpenAI API call fails or returns invalid intent
        
    Examples:
        >>> classify("Show weekly issuance trend")
        'trend'
        
        >>> classify("What's the WoW change in approvals?")
        'variance'
        
        >>> classify("How did we do vs forecast?")
        'forecast_vs_actual'
        
        >>> classify("What is funding rate?")
        'explain'
    """
    logger.info(
        "Classifying user query",
        extra={"user_query": user_query}
    )
    
    try:
        # Get OpenAI client
        client = _get_client()
        
        # Build context-aware prompt
        context_prompt = ""
        if conversation_history:
            # Get last 4 messages for context (2 exchanges)
            recent = conversation_history[-4:]
            if recent:
                context_prompt = "\n\nConversation History:\n"
                for msg in recent:
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    # Truncate long content
                    if len(content) > 200:
                        content = content[:200] + "..."
                    context_prompt += f"{role}: {content}\n"
                context_prompt += "\nConsider this context when classifying the current query."
        
        user_message = f"{user_query}{context_prompt}"
        
        # Call OpenAI with function calling
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            functions=[INTENT_FUNCTION],
            function_call={"name": "classify_intent"},
            temperature=0.0  # Deterministic classification
        )
        
        # Extract function call result
        function_call = response.choices[0].message.function_call
        
        if not function_call:
            logger.error("No function call in OpenAI response")
            raise ValueError("OpenAI did not return a function call")
        
        # Parse the function arguments
        import json
        args = json.loads(function_call.arguments)
        intent = args.get("intent")
        reasoning = args.get("reasoning", "")
        
        if not intent:
            logger.error("No intent in function call arguments")
            raise ValueError("Function call did not include intent")
        
        # Validate intent is one of the allowed values
        valid_intents = [
            "trend", "variance", "forecast_vs_actual", 
            "funnel", "distribution", "relationship", "multi_metric", "explain"
        ]
        
        if intent not in valid_intents:
            logger.error(
                f"Invalid intent returned: {intent}",
                extra={"intent": intent, "valid_intents": valid_intents}
            )
            raise ValueError(f"Invalid intent: {intent}")
        
        logger.info(
            "Intent classified successfully",
            extra={
                "user_query": user_query,
                "intent": intent,
                "reasoning": reasoning
            }
        )
        
        return intent
        
    except Exception as e:
        logger.error(
            f"Failed to classify intent: {str(e)}",
            extra={
                "user_query": user_query,
                "error": str(e)
            }
        )
        
        # Fallback to trend intent on error
        logger.warning("Falling back to 'trend' intent due to classification error")
        return "trend"
