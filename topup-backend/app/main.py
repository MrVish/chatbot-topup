"""
FastAPI main application for Topup CXO Assistant.

This module implements the REST API endpoints with Server-Sent Events (SSE)
streaming for real-time query processing. It provides:
- POST /chat: Main chat endpoint with SSE streaming
- GET /chart: Retrieve cached chart specifications
- GET /suggest: Generate follow-up question suggestions
- GET /export: Export query results as CSV or PNG

Requirements: 1.1, 2.1, 2.2, 2.3, 2.4, 2.5, 10.1-10.5, 14.1-14.5, 15.1-15.5, 16.1-16.5
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv()

# Import agents and tools
from agents import run_query
from tools import cache_tool
from models.schemas import Plan, SegmentFilters, Insight

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Structured logging helper
def log_structured(
    event_type: str,
    session_id: str,
    user_text: Optional[str] = None,
    plan: Optional[Dict] = None,
    sql: Optional[str] = None,
    row_count: Optional[int] = None,
    latency_ms: Optional[float] = None,
    cache_hit: bool = False,
    error: Optional[str] = None,
    **kwargs
):
    """
    Log structured event with consistent format.
    
    Args:
        event_type: Type of event (query_start, query_complete, error, etc.)
        session_id: Session identifier
        user_text: User query text
        plan: Query plan dict
        sql: SQL query text
        row_count: Number of rows returned
        latency_ms: Query latency in milliseconds
        cache_hit: Whether result was from cache
        error: Error message if any
        **kwargs: Additional fields to log
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "session_id": session_id,
    }
    
    if user_text:
        log_entry["user_text"] = user_text
    if plan:
        log_entry["plan"] = plan
    if sql:
        log_entry["sql"] = sql
    if row_count is not None:
        log_entry["row_count"] = row_count
    if latency_ms is not None:
        log_entry["latency_ms"] = latency_ms
    if cache_hit:
        log_entry["cache_hit"] = cache_hit
    if error:
        log_entry["error"] = error
    
    # Add any additional fields
    log_entry.update(kwargs)
    
    # Log as JSON for easy parsing
    logger.info(json.dumps(log_entry))
    
    return log_entry

# Create FastAPI app
app = FastAPI(
    title="Topup CXO Assistant API",
    description="Conversational analytics API with SSE streaming",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models

class ChatRequest(BaseModel):
    """
    Request model for /chat endpoint.
    
    Attributes:
        message: User's natural language query
        filters: Optional segment filters to apply
        session_id: Optional session identifier for logging
    """
    message: str = Field(..., description="User's natural language query")
    filters: Optional[SegmentFilters] = Field(
        default=None,
        description="Optional segment filters"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session identifier"
    )


class ChartRequest(BaseModel):
    """
    Request model for /chart endpoint.
    
    Attributes:
        cache_key: Cache key for the query result
    """
    cache_key: str = Field(..., description="Cache key for the query result")


class SuggestRequest(BaseModel):
    """
    Request model for /suggest endpoint.
    
    Attributes:
        context: Current query context
        last_intent: Last classified intent
    """
    context: str = Field(..., description="Current query context")
    last_intent: Optional[str] = Field(
        default=None,
        description="Last classified intent"
    )


class ExportRequest(BaseModel):
    """
    Request model for /export endpoint.
    
    Attributes:
        cache_key: Cache key for the query result
        format: Export format (csv or png)
    """
    cache_key: str = Field(..., description="Cache key for the query result")
    format: str = Field(..., description="Export format: csv or png")


# SSE Event Formatting

def format_sse_event(data: Any) -> str:
    """
    Format data as Server-Sent Event.
    
    Args:
        data: Event data (will be JSON serialized)
    
    Returns:
        str: Formatted SSE message
    """
    json_data = json.dumps(data)
    return f"data: {json_data}\n\n"


# Endpoints

@app.get("/")
async def root():
    """
    Root endpoint - health check.
    
    Returns:
        dict: API status and version
    """
    return {
        "status": "ok",
        "service": "Topup CXO Assistant API",
        "version": "1.0.0"
    }


@app.get("/chat")
async def chat_sse(
    message: str,
    channel: Optional[str] = None,
    grade: Optional[str] = None,
    prod_type: Optional[str] = None,
    repeat_type: Optional[str] = None,
    term: Optional[int] = None,
    cr_fico_band: Optional[str] = None,
    purpose: Optional[str] = None,
    session_id: Optional[str] = None,
    history: Optional[str] = None
):
    """
    Main chat endpoint with SSE streaming (GET for EventSource compatibility).
    
    This endpoint:
    1. Accepts a natural language query via query parameters
    2. Checks cache for existing results
    3. Executes the query through LangGraph orchestration if cache miss
    4. Streams partial messages, plan, chart, and insights as SSE events
    5. Caches the result for future queries
    
    Args:
        message: User's natural language query
        channel: Optional channel filter
        grade: Optional grade filter
        prod_type: Optional product type filter
        repeat_type: Optional repeat type filter
        term: Optional term filter
        cr_fico_band: Optional FICO band filter
        purpose: Optional purpose filter
        session_id: Optional session identifier for logging
        history: Optional conversation history as JSON string
    
    Returns:
        StreamingResponse: SSE stream with query results
    
    Requirements: 1.1, 2.1, 2.2, 2.3, 2.4, 2.5, 10.1-10.5, 16.1-16.5
    """
    # Build filters from query parameters
    filters = None
    if any([channel, grade, prod_type, repeat_type, term, cr_fico_band, purpose]):
        filters = SegmentFilters(
            channel=channel,
            grade=grade,
            prod_type=prod_type,
            repeat_type=repeat_type,
            term=term,
            cr_fico_band=cr_fico_band,
            purpose=purpose
        )
    
    # Parse conversation history if provided
    conversation_history = []
    if history:
        try:
            conversation_history = json.loads(history)
            logger.info(f"Received conversation history with {len(conversation_history)} messages")
        except json.JSONDecodeError:
            logger.warning(f"Invalid history JSON: {history}")
            conversation_history = []
    
    session_id = session_id or str(uuid.uuid4())
    start_time = time.time()
    
    # Structured logging: Query start
    log_structured(
        event_type="query_start",
        session_id=session_id,
        user_text=message,
        filters=filters.model_dump() if filters else None
    )
    
    async def event_generator():
        """
        Generate SSE events for the chat response.
        
        Yields:
            str: Formatted SSE events
        """
        result = None
        try:
            # Stream initial status
            yield format_sse_event({"partial": "Planning your query..."})
            await asyncio.sleep(0.1)  # Small delay for UX
            
            # Execute query through orchestration
            # Note: run_query is synchronous, so we run it in executor
            query_start = time.time()
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: run_query(message, conversation_history))
            query_latency = (time.time() - query_start) * 1000  # Convert to ms
            
            # Check for errors
            if result.get("error"):
                # Structured logging: Query error
                log_structured(
                    event_type="query_error",
                    session_id=session_id,
                    user_text=message,
                    error=result["error"],
                    latency_ms=query_latency
                )
                
                yield format_sse_event({"error": result["error"]})
                yield format_sse_event({"done": True})
                return
            
            # Stream cache hit status
            if result.get("cache_hit"):
                yield format_sse_event({"partial": "Retrieved from cache..."})
            else:
                yield format_sse_event({"partial": "Crunching numbers..."})
            
            await asyncio.sleep(0.1)
            
            # Stream plan (if available)
            if result.get("plan"):
                yield format_sse_event({"plan": result["plan"]})
                await asyncio.sleep(0.05)
            
            # Stream chart and insights as a card
            if result.get("chart_spec") or result.get("insight"):
                card_data = {
                    "plotly": result.get("chart_spec"),
                    "insight": result.get("insight")
                }
                yield format_sse_event({"card": card_data})
                await asyncio.sleep(0.05)
            
            # Structured logging: Query complete
            total_latency = (time.time() - start_time) * 1000
            log_structured(
                event_type="query_complete",
                session_id=session_id,
                user_text=message,
                plan=result.get("plan"),
                sql=result.get("sql"),
                row_count=len(result.get("df_dict", [])) if result.get("df_dict") else 0,
                latency_ms=total_latency,
                cache_hit=result.get("cache_hit", False)
            )
            
            # Stream completion
            yield format_sse_event({"done": True})
            
        except Exception as e:
            # Structured logging: Streaming error
            log_structured(
                event_type="streaming_error",
                session_id=session_id,
                user_text=message,
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000
            )
            
            yield format_sse_event({"error": f"Streaming error: {str(e)}"})
            yield format_sse_event({"done": True})
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@app.get("/chart")
async def get_chart(cache_key: str):
    """
    Retrieve cached chart specification.
    
    This endpoint retrieves a previously generated chart and its associated
    data from the cache. Useful for re-displaying charts without re-executing queries.
    
    Args:
        cache_key: Cache key for the query result (SHA256 hash of plan)
    
    Returns:
        dict: Chart specification, insight, and data preview
    
    Requirements: 14.1, 14.2, 16.1-16.5
    """
    session_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Structured logging: Chart request
    log_structured(
        event_type="chart_request",
        session_id=session_id,
        cache_key=cache_key
    )
    
    try:
        # Retrieve from cache
        cached_result = cache_tool.get(cache_key)
        
        if not cached_result:
            # Structured logging: Chart not found
            log_structured(
                event_type="chart_not_found",
                session_id=session_id,
                cache_key=cache_key,
                latency_ms=(time.time() - start_time) * 1000
            )
            
            raise HTTPException(status_code=404, detail="Chart not found or expired")
        
        # Structured logging: Chart retrieved
        log_structured(
            event_type="chart_retrieved",
            session_id=session_id,
            cache_key=cache_key,
            latency_ms=(time.time() - start_time) * 1000
        )
        
        return {
            "chart": cached_result.get("chart_spec"),
            "insight": cached_result.get("insight"),
            "data_preview": cached_result.get("df_dict", [])[:10] if cached_result.get("df_dict") else []
        }
    
    except HTTPException:
        raise
    except Exception as e:
        # Structured logging: Chart retrieval error
        log_structured(
            event_type="chart_error",
            session_id=session_id,
            cache_key=cache_key,
            error=str(e),
            latency_ms=(time.time() - start_time) * 1000
        )
        
        raise HTTPException(status_code=500, detail=f"Error retrieving chart: {str(e)}")


@app.post("/suggest")
async def suggest_followup(request: SuggestRequest):
    """
    Generate follow-up question suggestions.
    
    Based on the current query context and intent, this endpoint
    generates 3 relevant follow-up questions the user might ask.
    This helps guide users to explore related insights efficiently.
    
    Args:
        request: SuggestRequest with context and last intent
    
    Returns:
        dict: List of 3 suggested follow-up questions
    
    Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 16.1-16.5
    """
    session_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Structured logging: Suggest request
    log_structured(
        event_type="suggest_request",
        session_id=session_id,
        context=request.context[:100],  # Truncate for logging
        last_intent=request.last_intent
    )
    
    try:
        # Generate contextual suggestions based on intent
        suggestions = []
        
        intent = request.last_intent or "trend"
        
        if intent == "trend":
            suggestions = [
                "How does this compare to last month?",
                "Show me the breakdown by channel",
                "What's driving the change?"
            ]
        elif intent == "variance":
            suggestions = [
                "Show me the trend over time",
                "Which segments are performing best?",
                "What's the forecast for next month?"
            ]
        elif intent == "forecast_vs_actual":
            suggestions = [
                "Show me the trend for actual issuance",
                "Which channels had the biggest variance?",
                "What's the accuracy by grade?"
            ]
        elif intent == "funnel":
            suggestions = [
                "Show me the trend for each stage",
                "Compare this to last month's funnel",
                "Which channel has the best conversion?"
            ]
        elif intent == "distribution":
            suggestions = [
                "Show me the trend over time",
                "How does this compare to last month?",
                "What's the breakdown by grade?"
            ]
        elif intent == "relationship":
            suggestions = [
                "Show me the trend for this metric",
                "What's the distribution by segment?",
                "How does this compare to last month?"
            ]
        else:
            suggestions = [
                "Show me weekly issuance trend",
                "How did we perform vs forecast?",
                "What's the funnel for Email channel?"
            ]
        
        # Structured logging: Suggestions generated
        log_structured(
            event_type="suggest_complete",
            session_id=session_id,
            intent=intent,
            suggestion_count=len(suggestions),
            latency_ms=(time.time() - start_time) * 1000
        )
        
        return {"suggestions": suggestions}
    
    except Exception as e:
        # Structured logging: Suggest error
        log_structured(
            event_type="suggest_error",
            session_id=session_id,
            error=str(e),
            latency_ms=(time.time() - start_time) * 1000
        )
        
        raise HTTPException(status_code=500, detail=f"Error generating suggestions: {str(e)}")


@app.get("/export")
async def export_data(cache_key: str, format: str = "csv"):
    """
    Export query results as CSV or PNG.
    
    This endpoint allows users to download query results for use in
    presentations, reports, or further analysis. Supports CSV for data
    and PNG for chart images.
    
    Args:
        cache_key: Cache key for the query result (SHA256 hash of plan)
        format: Export format - "csv" for data or "png" for chart image
    
    Returns:
        FileResponse: Downloaded file (CSV or PNG)
        JSONResponse: For PNG, returns chart spec for client-side rendering
    
    Requirements: 14.1, 14.2, 14.3, 16.1-16.5
    """
    session_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Structured logging: Export request
    log_structured(
        event_type="export_request",
        session_id=session_id,
        cache_key=cache_key,
        format=format
    )
    
    try:
        # Retrieve from cache
        cached_result = cache_tool.get(cache_key)
        
        if not cached_result:
            # Structured logging: Export data not found
            log_structured(
                event_type="export_not_found",
                session_id=session_id,
                cache_key=cache_key,
                format=format,
                latency_ms=(time.time() - start_time) * 1000
            )
            
            raise HTTPException(status_code=404, detail="Data not found or expired")
        
        if format == "csv":
            # Export as CSV
            import pandas as pd
            import tempfile
            import os
            
            df_dict = cached_result.get("df_dict")
            if not df_dict:
                raise HTTPException(status_code=400, detail="No data available for export")
            
            df = pd.DataFrame(df_dict)
            row_count = len(df)
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as f:
                df.to_csv(f, index=False)
                temp_path = f.name
            
            # Structured logging: CSV export complete
            log_structured(
                event_type="export_complete",
                session_id=session_id,
                cache_key=cache_key,
                format=format,
                row_count=row_count,
                latency_ms=(time.time() - start_time) * 1000
            )
            
            return FileResponse(
                temp_path,
                media_type="text/csv",
                filename=f"topup_export_{cache_key[:8]}.csv",
                background=None  # File will be cleaned up by OS
            )
        
        elif format == "png":
            # Export chart as PNG
            # Note: This requires kaleido package for Plotly static export
            # For MVP, we'll return the chart spec for client-side rendering
            
            chart_spec = cached_result.get("chart_spec")
            if not chart_spec:
                raise HTTPException(status_code=400, detail="No chart available for export")
            
            # Structured logging: PNG export (client-side)
            log_structured(
                event_type="export_complete",
                session_id=session_id,
                cache_key=cache_key,
                format=format,
                client_side=True,
                latency_ms=(time.time() - start_time) * 1000
            )
            
            return JSONResponse({
                "message": "PNG export requires client-side rendering. Use Plotly.downloadImage() with the provided chart spec.",
                "chart_spec": chart_spec,
                "filename": f"topup_chart_{cache_key[:8]}.png"
            })
        
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'csv' or 'png'")
    
    except HTTPException:
        raise
    except Exception as e:
        # Structured logging: Export error
        log_structured(
            event_type="export_error",
            session_id=session_id,
            cache_key=cache_key,
            format=format,
            error=str(e),
            latency_ms=(time.time() - start_time) * 1000
        )
        
        raise HTTPException(status_code=500, detail=f"Error exporting data: {str(e)}")


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Provides service health status and metrics for monitoring.
    
    Returns:
        dict: Service health status, timestamp, and cache metrics
    """
    session_id = str(uuid.uuid4())
    
    try:
        cache_size = cache_tool.get_cache().size()
        
        # Structured logging: Health check
        log_structured(
            event_type="health_check",
            session_id=session_id,
            cache_size=cache_size
        )
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "cache_size": cache_size,
            "service": "Topup CXO Assistant API",
            "version": "1.0.0"
        }
    except Exception as e:
        # Structured logging: Health check error
        log_structured(
            event_type="health_check_error",
            session_id=session_id,
            error=str(e)
        )
        
        return {
            "status": "degraded",
            "timestamp": time.time(),
            "error": str(e)
        }


# Startup and shutdown events

@app.on_event("startup")
async def startup_event():
    """
    Application startup event.
    
    Initializes services and logs startup information.
    """
    logger.info("="*80)
    logger.info("Topup CXO Assistant API starting up...")
    logger.info("="*80)
    
    # Structured logging: Startup
    log_structured(
        event_type="service_startup",
        session_id="system",
        cache_max_size=100,
        cache_ttl=600,
        version="1.0.0"
    )
    
    logger.info("Ready to accept requests")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event.
    
    Cleans up resources and logs shutdown information.
    """
    logger.info("="*80)
    logger.info("Topup CXO Assistant API shutting down...")
    logger.info("="*80)
    
    # Cleanup cache
    cache_size = cache_tool.get_cache().size()
    cache_tool.clear()
    
    # Structured logging: Shutdown
    log_structured(
        event_type="service_shutdown",
        session_id="system",
        cache_entries_cleared=cache_size
    )
    
    logger.info("Cache cleared")


# Error handlers

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    
    Args:
        request: The request that caused the error
        exc: The exception that was raised
    
    Returns:
        JSONResponse: Error response
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "type": type(exc).__name__
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
