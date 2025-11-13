"""
LangGraph orchestration for Topup CXO Assistant.

This module provides the main orchestrator that coordinates all agents
and tools to process user queries. It uses LangGraph to define a state
machine that routes queries through the appropriate agents based on intent.

The orchestration flow:
1. Router Agent: Classify user intent
2. Conditional routing:
   - If intent is "explain" → Memory Agent → Return
   - Otherwise → Continue to Planner
3. Planner Agent: Generate structured query plan
4. Cache Check: Check if result is cached
5. Guardrail Agent: Validate plan and SQL
6. SQL Agent: Execute query
7. Chart Agent: Generate Plotly spec
8. Insights Agent: Generate narrative
9. Cache Store: Store result for future queries
10. Return combined result
"""

import logging
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph

from agents import router, planner, guardrail, insights_agent
from agents import sql_generator, explanation_agent
from tools import sql_tool, chart_tool, cache_tool
from models.schemas import Plan, Insight

# Configure logging first
logger = logging.getLogger(__name__)

# Try to import memory_agent, but make it optional if RAG tool is not available
try:
    from agents import memory_agent
    MEMORY_AGENT_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    logger.warning(f"Memory agent not available: {str(e)}")
    MEMORY_AGENT_AVAILABLE = False
    memory_agent = None


class GraphState(TypedDict):
    """
    State object passed between nodes in the LangGraph.
    
    Attributes:
        user_query: Original user query text
        conversation_history: List of previous messages for context
        intent: Classified intent from Router Agent
        plan: Structured query plan from Planner Agent
        sql: Generated SQL query (for logging/debugging)
        df_dict: Query results as dict (DataFrame serialized)
        chart_spec: Plotly JSON specification
        insight: Narrative insights object
        error: Error message if any step fails
        cache_key: Cache key for result storage
        cache_hit: Whether result was retrieved from cache
    """
    user_query: str
    conversation_history: Optional[List[Dict]]
    intent: Optional[str]
    plan: Optional[Plan]
    sql: Optional[str]
    df_dict: Optional[Dict[str, Any]]
    chart_spec: Optional[Dict[str, Any]]
    insight: Optional[Insight]
    error: Optional[str]
    cache_key: Optional[str]
    cache_hit: bool


# Node functions for the graph

def router_node(state: GraphState) -> GraphState:
    """
    Router node: Classify user intent.
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with intent classification
    """
    logger.info("Router node: Classifying intent")
    
    try:
        intent = router.classify(state["user_query"], state.get("conversation_history"))
        state["intent"] = intent
        logger.info(f"Intent classified: {intent}")
    except Exception as e:
        logger.error(f"Router node failed: {str(e)}")
        state["error"] = f"Intent classification failed: {str(e)}"
        state["intent"] = "trend"  # Fallback to trend
    
    return state


def memory_node(state: GraphState) -> GraphState:
    """
    Memory node: Handle explain queries using RAG.
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with explanation text
    """
    logger.info("Memory node: Retrieving explanation")
    
    # Check if memory agent is available
    if not MEMORY_AGENT_AVAILABLE or memory_agent is None:
        logger.warning("Memory agent not available, returning fallback response")
        state["insight"] = Insight(
            title="Explanation",
            summary="The explanation feature is not yet configured. Please ensure the RAG tool is initialized.",
            bullets=[],
            drivers=[]
        )
        return state
    
    try:
        explanation = memory_agent.explain(state["user_query"])
        
        # Store explanation as an insight for consistent response format
        state["insight"] = Insight(
            title="Explanation",
            summary=explanation,
            bullets=[],
            drivers=[]
        )
        
        logger.info("Explanation retrieved successfully")
    except Exception as e:
        logger.error(f"Memory node failed: {str(e)}")
        state["error"] = f"Explanation retrieval failed: {str(e)}"
        state["insight"] = Insight(
            title="Explanation",
            summary="Unable to retrieve explanation. Please try rephrasing your question.",
            bullets=[],
            drivers=[]
        )
    
    return state


def planner_node(state: GraphState) -> GraphState:
    """
    Planner node: Generate structured query plan.
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with query plan
    """
    logger.info("Planner node: Generating query plan")
    
    try:
        plan = planner.make_plan(state["user_query"], state["intent"], state.get("conversation_history"))
        state["plan"] = plan
        state["cache_key"] = plan.cache_key()
        logger.info(f"Query plan generated: {plan.model_dump()}")
    except Exception as e:
        logger.error(f"Planner node failed: {str(e)}")
        state["error"] = f"Query planning failed: {str(e)}"
    
    return state


def cache_check_node(state: GraphState) -> GraphState:
    """
    Cache check node: Check if result is cached.
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with cached result if available
    """
    logger.info("Cache check node: Checking cache")
    
    if not state.get("cache_key"):
        logger.warning("No cache key available")
        state["cache_hit"] = False
        return state
    
    try:
        cached_result = cache_tool.get(state["cache_key"])
        
        if cached_result:
            logger.info("Cache hit!")
            state["cache_hit"] = True
            state["df_dict"] = cached_result.get("df_dict")
            state["chart_spec"] = cached_result.get("chart_spec")
            # Keep insight as dict - will be handled in response building
            state["insight"] = cached_result.get("insight")
        else:
            logger.info("Cache miss")
            state["cache_hit"] = False
    except Exception as e:
        logger.error(f"Cache check failed: {str(e)}")
        state["cache_hit"] = False
    
    return state


def guardrail_node(state: GraphState) -> GraphState:
    """
    Guardrail node: Validate plan and SQL.
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with validation result
    """
    logger.info("Guardrail node: Validating plan")
    
    if not state.get("plan"):
        state["error"] = "No plan to validate"
        return state
    
    try:
        # Generate a preview SQL for validation (we'll generate the real one in SQL node)
        # For now, just validate the plan structure
        validation_result = guardrail.validate(state["plan"], "")
        
        if not validation_result.is_valid:
            logger.warning(f"Validation failed: {validation_result.error_message}")
            state["error"] = validation_result.error_message
        else:
            logger.info("Validation passed")
    except Exception as e:
        logger.error(f"Guardrail node failed: {str(e)}")
        state["error"] = f"Validation failed: {str(e)}"
    
    return state


def sql_executor_node(state: GraphState) -> GraphState:
    """
    SQL executor node: Execute query and return results.
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with query results
    """
    logger.info("SQL executor node: Executing query")
    
    if not state.get("plan"):
        state["error"] = "No plan to execute"
        return state
    
    try:
        df = sql_tool.run(state["plan"])
        
        # Convert DataFrame to dict for serialization
        state["df_dict"] = df.to_dict(orient="records")
        
        logger.info(f"Query executed successfully, {len(df)} rows returned")
    except Exception as e:
        logger.error(f"SQL node failed: {str(e)}")
        state["error"] = f"Query execution failed: {str(e)}"
    
    return state


def chart_node(state: GraphState) -> GraphState:
    """
    Chart node: Generate Plotly specification.
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with chart spec
    """
    logger.info("Chart node: Generating chart")
    
    if not state.get("plan") or not state.get("df_dict"):
        logger.warning("Missing plan or data for chart generation")
        return state
    
    try:
        # Convert dict back to DataFrame
        import pandas as pd
        df = pd.DataFrame(state["df_dict"])
        
        chart_spec = chart_tool.build(state["plan"], df, theme="light")
        state["chart_spec"] = chart_spec
        
        logger.info("Chart generated successfully")
    except Exception as e:
        logger.error(f"Chart node failed: {str(e)}")
        # Don't set error - chart is optional
        logger.warning(f"Continuing without chart: {str(e)}")
    
    return state


def insights_node(state: GraphState) -> GraphState:
    """
    Insights node: Generate narrative insights.
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with insights
    """
    logger.info("Insights node: Generating insights")
    
    if not state.get("plan") or not state.get("df_dict"):
        logger.warning("Missing plan or data for insights generation")
        return state
    
    try:
        # Convert dict back to DataFrame
        import pandas as pd
        df = pd.DataFrame(state["df_dict"])
        
        insight = insights_agent.summarize(state["plan"], df)
        state["insight"] = insight
        
        logger.info("Insights generated successfully")
    except Exception as e:
        logger.error(f"Insights node failed: {str(e)}")
        # Don't set error - insights are optional
        logger.warning(f"Continuing without insights: {str(e)}")
    
    return state


def cache_store_node(state: GraphState) -> GraphState:
    """
    Cache store node: Store result in cache.
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state (unchanged)
    """
    logger.info("Cache store node: Storing result")
    
    if not state.get("cache_key"):
        logger.warning("No cache key available")
        return state
    
    # Don't cache failed queries or empty results
    if state.get("error"):
        logger.info("Skipping cache - query has error")
        return state
    
    if not state.get("df_dict") or len(state.get("df_dict", [])) == 0:
        logger.info("Skipping cache - no data returned")
        return state
    
    if not state.get("chart_spec") and not state.get("insight"):
        logger.info("Skipping cache - no chart or insight generated")
        return state
    
    try:
        cache_value = {
            "df_dict": state.get("df_dict"),
            "chart_spec": state.get("chart_spec"),
            "insight": state["insight"].model_dump() if state.get("insight") else None
        }
        
        cache_tool.set(state["cache_key"], cache_value, ex=600)  # 10 minutes TTL
        logger.info("Result cached successfully")
    except Exception as e:
        logger.error(f"Cache store failed: {str(e)}")
        # Don't set error - caching is optional
    
    return state


# Conditional edge functions

def should_use_memory(state: GraphState) -> str:
    """
    Determine if query should use memory/RAG (explain intent).
    
    Args:
        state: Current graph state
        
    Returns:
        "memory" if intent is explain, "planner" otherwise
    """
    if state.get("intent") == "explain":
        return "memory"
    return "planner"


def should_skip_execution(state: GraphState) -> str:
    """
    Determine if execution should be skipped due to cache hit or error.
    
    Args:
        state: Current graph state
        
    Returns:
        "end" if cache hit or error, "guardrail" otherwise
    """
    if state.get("cache_hit"):
        return "end"
    if state.get("error"):
        return "end"
    return "guardrail"


def should_continue_after_guardrail(state: GraphState) -> str:
    """
    Determine if execution should continue after guardrail validation.
    
    Args:
        state: Current graph state
        
    Returns:
        "end" if error, "sql" otherwise
    """
    if state.get("error"):
        return "end"
    return "sql"


def should_continue_after_sql_executor(state: GraphState) -> str:
    """
    Determine if execution should continue after SQL execution.
    
    Args:
        state: Current graph state
        
    Returns:
        "end" if error, "chart" otherwise
    """
    if state.get("error"):
        return "end"
    return "chart"


# Build the graph

def create_graph() -> StateGraph:
    """
    Create the LangGraph orchestration graph.
    
    Returns:
        StateGraph: Configured graph ready for execution
    """
    # Initialize graph
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("memory", memory_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("cache_check", cache_check_node)
    workflow.add_node("guardrail", guardrail_node)
    workflow.add_node("sql_executor", sql_executor_node)
    workflow.add_node("chart", chart_node)
    workflow.add_node("insights", insights_node)
    workflow.add_node("cache_store", cache_store_node)
    
    # Set entry point
    workflow.set_entry_point("router")
    
    # Add edges
    # Router → Memory or Planner (conditional)
    workflow.add_conditional_edges(
        "router",
        should_use_memory,
        {
            "memory": "memory",
            "planner": "planner"
        }
    )
    
    # Memory → END
    workflow.add_edge("memory", END)
    
    # Planner → Cache Check
    workflow.add_edge("planner", "cache_check")
    
    # Cache Check → Guardrail or END (conditional)
    workflow.add_conditional_edges(
        "cache_check",
        should_skip_execution,
        {
            "guardrail": "guardrail",
            "end": END
        }
    )
    
    # Guardrail → SQL Executor or END (conditional)
    workflow.add_conditional_edges(
        "guardrail",
        should_continue_after_guardrail,
        {
            "sql": "sql_executor",
            "end": END
        }
    )
    
    # SQL Executor → Chart
    workflow.add_edge("sql_executor", "chart")
    
    # Chart → Insights (sequential to avoid parallel state updates)
    workflow.add_edge("chart", "insights")
    
    # Insights → Cache Store
    workflow.add_edge("insights", "cache_store")
    
    # Cache Store → END
    workflow.add_edge("cache_store", END)
    
    return workflow


# Main execution function

def run_query(
    user_query: str,
    conversation_history: Optional[List[Dict]] = None,
    max_retries: int = 2
) -> Dict[str, Any]:
    """
    Execute a user query through the LangGraph orchestration.
    
    This is the main entry point for query execution. It:
    1. Creates the graph
    2. Initializes state with user query and conversation history
    3. Executes the graph with retry logic
    4. Returns the final result
    
    Args:
        user_query: Natural language query from user
        conversation_history: List of previous messages for context
        max_retries: Maximum number of retry attempts on failure
        
    Returns:
        Dict containing:
            - plan: Query plan (if generated)
            - chart_spec: Plotly specification (if generated)
            - insight: Narrative insights (if generated)
            - error: Error message (if failed)
            - cache_hit: Whether result was from cache
    """
    logger.info(f"Running query: {user_query}")
    
    # Create graph
    workflow = create_graph()
    app = workflow.compile()
    
    # Initialize state
    initial_state: GraphState = {
        "user_query": user_query,
        "conversation_history": conversation_history or [],
        "intent": None,
        "plan": None,
        "sql": None,
        "df_dict": None,
        "chart_spec": None,
        "insight": None,
        "error": None,
        "cache_key": None,
        "cache_hit": False
    }
    
    # Execute with retry logic
    attempt = 0
    final_state = None
    
    while attempt < max_retries:
        try:
            # Run the graph
            final_state = app.invoke(initial_state)
            
            # Check if execution was successful
            if not final_state.get("error"):
                logger.info("Query executed successfully")
                break
            else:
                logger.warning(f"Attempt {attempt + 1} failed: {final_state['error']}")
                attempt += 1
                
                # Reset error for retry
                if attempt < max_retries:
                    initial_state["error"] = None
        
        except Exception as e:
            logger.error(f"Graph execution failed on attempt {attempt + 1}: {str(e)}")
            attempt += 1
            
            if attempt >= max_retries:
                final_state = initial_state.copy()
                final_state["error"] = f"Query execution failed after {max_retries} attempts: {str(e)}"
    
    # Build response
    # Handle insight - it might be an Insight object or already a dict (from cache)
    insight_data = None
    if final_state.get("insight"):
        insight = final_state.get("insight")
        if isinstance(insight, dict):
            # Already serialized (from cache)
            insight_data = insight
        else:
            # Insight object - serialize it
            insight_data = insight.model_dump()
    
    response = {
        "plan": final_state.get("plan").model_dump() if final_state.get("plan") else None,
        "chart_spec": final_state.get("chart_spec"),
        "insight": insight_data,
        "error": final_state.get("error"),
        "cache_hit": final_state.get("cache_hit", False)
    }
    
    logger.info(f"Query completed. Cache hit: {response['cache_hit']}, Error: {response['error']}")
    
    return response


# Example usage
if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Test queries
    test_queries = [
        "Show weekly issuance trend for the last 8 weeks",
        "What is funding rate?",
        "How did actual issuance compare to forecast last month?",
        "Show the funnel for Email channel"
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}")
        
        result = run_query(query)
        
        print(f"\nResult:")
        print(f"  Cache Hit: {result['cache_hit']}")
        print(f"  Error: {result['error']}")
        print(f"  Plan: {result['plan']}")
        print(f"  Chart: {'Generated' if result['chart_spec'] else 'None'}")
        print(f"  Insight: {result['insight']}")
