# FastAPI Application

FastAPI application providing conversational analytics with Server-Sent Events (SSE) streaming.

## Overview

This API enables natural language queries over marketing data with real-time streaming responses.

## Quick Start

```bash
# Development mode
uvicorn app.main:app --reload --port 8000

# Or use the provided script
./run.sh  # Linux/Mac
run.bat   # Windows
```

## Main Endpoints

- **POST /chat** - Main chat endpoint with SSE streaming
- **GET /chart** - Retrieve cached chart specification
- **POST /suggest** - Generate follow-up question suggestions
- **GET /export** - Export query results as CSV or PNG
- **GET /health** - Health check endpoint

## Documentation

For comprehensive API documentation, see:
- **[docs/backend/API.md](../../docs/backend/API.md)** - Complete API reference

## Testing

All app tests are located in `tests/app/`:

```bash
pytest tests/app/ -v
```

## Configuration

Create a `.env` file:

```env
DATABASE_URL=./data/topup.db
OPENAI_API_KEY=sk-...
CACHE_TYPE=memory
```
