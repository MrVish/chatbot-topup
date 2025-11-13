# Agents

This directory contains the LangGraph agent components for the Topup CXO Assistant.

## Overview

The backend uses a multi-agent architecture orchestrated by LangGraph to process natural language queries and generate insights.

## Agents

- **Router Agent** (`router.py`): Classifies user queries into 7 intent categories
- **Planner Agent** (`planner.py`): Generates structured query plans
- **Guardrail Agent** (`guardrail.py`): Validates queries for security and correctness
- **Insights Agent** (`insights_agent.py`): Generates executive-level narrative insights
- **Memory Agent** (`memory_agent.py`): Handles "explain" queries using RAG
- **Orchestration** (`__init__.py`): Coordinates all agents via LangGraph

## Quick Start

```python
from agents import run_query

# Execute a query
result = run_query("Show weekly issuance trend")
```

## Documentation

For comprehensive documentation, see:
- **[docs/backend/AGENTS.md](../../docs/backend/AGENTS.md)** - Detailed agent documentation
- **[docs/backend/API.md](../../docs/backend/API.md)** - API endpoint documentation

## Testing

All agent tests are located in `tests/agents/`:

```bash
pytest tests/agents/ -v
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
