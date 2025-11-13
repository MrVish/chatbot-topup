# Backend Agents Documentation

This document provides comprehensive documentation for all agents in the Topup CXO Assistant backend.

## Overview

The backend uses a multi-agent architecture orchestrated by LangGraph to process natural language queries and generate insights.

## Agent Flow

```
User Query → Router Agent (Intent Classification)
           ↓
    Planner Agent (Generate Query Plan)
           ↓
    Guardrail Agent (Validate & Secure)
           ↓
    SQL Agent (Execute Read-Only Query)
           ↓
    ┌──────┴──────┐
    ↓             ↓
Chart Agent   Insights Agent (Parallel Execution)
    ↓             ↓
    └──────┬──────┘
           ↓
    Combined Response → Cache → Stream to Client
```

## Router Agent

**File**: `agents/router.py`

**Purpose**: Classifies user queries into one of seven intent categories using OpenAI function calling.

### Supported Intents

1. **trend**: Time-series analysis queries
   - Examples: "Show weekly issuance trend", "How have app submits changed?"
   - Keywords: trend, over time, weekly, monthly, historical

2. **variance**: Period-over-period comparisons
   - Examples: "What's the WoW change?", "Compare this month to last month"
   - Keywords: WoW, MoM, week-over-week, month-over-month, compare

3. **forecast_vs_actual**: Forecast accuracy analysis
   - Examples: "How did we do vs forecast?", "Compare actual to forecast"
   - Keywords: forecast, predicted, expected, vs actual, accuracy

4. **funnel**: Conversion funnel analysis
   - Examples: "Show the funnel", "What's our conversion rate?"
   - Keywords: funnel, conversion, submission to approval

5. **distribution**: Composition or breakdown by segment
   - Examples: "What's the channel mix?", "Breakdown by grade"
   - Keywords: distribution, breakdown, composition, mix

6. **relationship**: Correlation between metrics
   - Examples: "How does FICO relate to approval rate?", "APR vs issuance"
   - Keywords: relationship, correlation, vs, compared to

7. **explain**: Metric or term definitions
   - Examples: "What is funding rate?", "Define approval rate"
   - Keywords: what is, define, explain, meaning of

### Usage

```python
from agents.router import classify

intent = classify("Show weekly issuance trend")
# Returns: "trend"
```

## Planner Agent

**File**: `agents/planner.py`

**Purpose**: Converts user queries and classified intents into structured query plans using OpenAI structured outputs.

### Key Features

- Structured Outputs using OpenAI's structured output feature
- Metric Interpretation: Defaults to amounts (not counts)
- Smart Defaults: 30-day window, weekly granularity
- Table Selection: Automatically selects cps_tb or forecast_df
- Date Column Selection: Chooses appropriate date column
- Chart Type Mapping: Selects chart type based on intent
- Segment Parsing: Extracts segment filters from queries

### Metric Interpretation Rules

**Default to AMOUNTS (not counts):**
- "app submits" → `app_submit_amnt` (sum of loan amounts)
- "app approvals" → `apps_approved_amnt` (sum of approved amounts)
- "issuances" → `issued_amnt` (sum of issued amounts)

**Use COUNTS only when explicitly requested:**
- "number of app submits" → `COUNT(app_submit_d)`
- "count of approvals" → `SUM(cr_appr_flag)`

### Usage

```python
from agents.planner import make_plan

plan = make_plan("Show weekly issuance by channel last 8 weeks", "trend")
```

## Guardrail Agent

**File**: `agents/guardrail.py`

**Purpose**: Validates query plans and SQL queries before execution to ensure security and correctness.

### Validation Checks

1. **SQL Safety**: Blocks dangerous keywords (INSERT, UPDATE, DELETE, DROP, ALTER, CREATE)
2. **Multiple Statement Detection**: Prevents SQL injection via semicolons
3. **Segment Filter Validation**: Validates all segment values against allowed values
4. **Time Window Enforcement**: Enforces maximum 1-year time window

### Usage

```python
from agents.guardrail import validate

result = validate(plan, sql)
if result:
    # Validation passed
    execute_query(sql)
else:
    # Validation failed
    print(result.error_message)
```

## Insights Agent

**File**: `agents/insights_agent.py`

**Purpose**: Generates executive-level narrative insights from query results.

### Features

- Variance Analysis: Calculates MoM and WoW percentage deltas
- Forecast Accuracy: Compares actual vs forecast with error metrics
- Funnel Conversion: Analyzes conversion rates
- Trend Analysis: Identifies growth patterns
- Smart Formatting: Automatically formats currency, percentages, numbers
- Executive Summaries: Generates one-line takeaways and key bullet points

### Usage

```python
from agents.insights_agent import summarize

insight = summarize(plan, df)
print(insight.summary)
```

## Memory Agent

**File**: `agents/memory_agent.py`

**Purpose**: Handles "explain" intent queries by retrieving relevant definitions from the RAG tool.

### Features

- RAG Integration: Calls retrieve() from tools.rag_tool
- Intelligent Formatting: Combines multiple documents coherently
- Q&A Cleaning: Removes "Q: ... A: " prefixes
- Fallback Handling: Provides helpful message when no information found

### Usage

```python
from agents.memory_agent import explain

response = explain("What is funding rate?")
```

## LangGraph Orchestration

**File**: `agents/__init__.py`

**Purpose**: Coordinates all agents and tools to process user queries.

### State Management

The `GraphState` TypedDict maintains state as it flows through the graph:

```python
{
    "user_query": str,
    "intent": str,
    "plan": Plan,
    "sql": str,
    "df_dict": dict,
    "chart_spec": dict,
    "insight": Insight,
    "error": str,
    "cache_key": str,
    "cache_hit": bool
}
```

### Main Entry Point

```python
from agents import run_query

result = run_query("Show weekly issuance trend")
```

## Testing

All agent tests are located in `tests/agents/`:

```bash
# Run all agent tests
pytest tests/agents/ -v

# Run specific agent tests
pytest tests/agents/test_router.py -v
pytest tests/agents/test_planner.py -v
pytest tests/agents/test_guardrail.py -v
pytest tests/agents/test_insights_agent.py -v
pytest tests/agents/test_memory_agent.py -v
pytest tests/agents/test_orchestration.py -v
```

## Configuration

Set the OpenAI API key in your environment:

```bash
export OPENAI_API_KEY=sk-...
```

Or in `.env` file:
```
OPENAI_API_KEY=sk-...
```

## Performance Targets

- Router: ~200ms
- Planner: ~300ms
- Guardrail: ~50ms
- SQL: ~500ms
- Chart: ~100ms
- Insights: ~200ms
- **Total (cache miss)**: ~1.4s
- **Total (cache hit)**: ~0.5s

## Error Handling

- Node-level: Individual nodes catch and log errors
- Conditional edges: Check for errors and route to END
- Graph-level: Retry logic (max 2 attempts) for transient failures
- Graceful degradation: Chart/Insights failures don't block each other
