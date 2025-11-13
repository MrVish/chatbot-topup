# Backend API Documentation

FastAPI application providing conversational analytics with Server-Sent Events (SSE) streaming.

## Overview

This API enables natural language queries over marketing data with real-time streaming responses. It orchestrates multiple AI agents to process queries and return interactive visualizations with executive insights.

## Base URL

- Development: `http://localhost:8000`
- Production: Configure via environment variables

## Endpoints

### POST /chat

Main chat endpoint with SSE streaming.

**Request:**
```json
{
  "message": "Show weekly issuance trend for the last 8 weeks",
  "filters": {
    "channel": "Email",
    "grade": "P1"
  },
  "session_id": "optional_session_id"
}
```

**Response:** Server-Sent Events stream

**Event Types:**
- `partial`: Status updates ("Planning your query...", "Crunching numbers...")
- `plan`: Query plan JSON
- `card`: Chart specification and insights
- `done`: Completion signal
- `error`: Error message

**Example SSE Stream:**
```
event: partial
data: {"text": "Planning your query..."}

event: partial
data: {"text": "Crunching numbers..."}

event: plan
data: {"intent": "trend", "table": "cps_tb", ...}

event: card
data: {"chart": {...}, "insight": {...}}

event: done
data: {}
```

### GET /chart

Retrieve cached chart specification.

**Parameters:**
- `cache_key` (string): Cache key from query result

**Response:**
```json
{
  "chart": { /* Plotly JSON spec */ },
  "insight": { /* Insight object */ },
  "data_preview": [ /* First 10 rows */ ]
}
```

**Status Codes:**
- 200: Success
- 404: Chart not found or expired
- 500: Internal server error

### POST /suggest

Generate follow-up question suggestions.

**Request:**
```json
{
  "context": "Show weekly issuance trend",
  "last_intent": "trend"
}
```

**Response:**
```json
{
  "suggestions": [
    "How does this compare to last month?",
    "Show me the breakdown by channel",
    "What's driving the change?"
  ]
}
```

**Intent-Based Suggestions:**
- **trend**: Comparison, breakdown, drivers
- **variance**: Trend, segment performance, forecast
- **forecast_vs_actual**: Actual trend, variance by segment, accuracy
- **funnel**: Stage trends, comparison, conversion by segment
- **distribution**: Trend, comparison, breakdown
- **relationship**: Trend, distribution, comparison

### GET /export

Export query results as CSV or PNG files.

**Parameters:**
- `cache_key` (string): Cache key from query result
- `format` (string): "csv" or "png"

**CSV Export Response:**
- Content-Type: text/csv
- Downloads file: `topup_export_{cache_key[:8]}.csv`

**PNG Export Response:**
```json
{
  "message": "PNG export requires client-side rendering...",
  "chart_spec": { /* Plotly JSON specification */ },
  "filename": "topup_chart_{cache_key[:8]}.png"
}
```

**Status Codes:**
- 200: Success
- 400: Invalid format or no data available
- 404: Data not found or expired
- 500: Internal server error

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1699999999.999,
  "cache_size": 42,
  "service": "topup-cxo-assistant",
  "version": "1.0.0"
}
```

## Running the Server

### Development Mode

```bash
# From topup-backend directory
uvicorn app.main:app --reload --port 8000
```

Or use the provided script:

```bash
# Windows
run.bat

# Linux/Mac
./run.sh
```

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Environment Variables

Create a `.env` file in the `topup-backend` directory:

```env
# Database
DATABASE_URL=./data/topup.db

# OpenAI
OPENAI_API_KEY=sk-...

# Cache
CACHE_TYPE=memory
CACHE_TTL=600

# Logging
LOG_LEVEL=INFO
```

## SSE Client Examples

### JavaScript/TypeScript

```typescript
const eventSource = new EventSource('http://localhost:8000/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: 'Show weekly issuance trend',
  }),
});

eventSource.addEventListener('partial', (event) => {
  const data = JSON.parse(event.data);
  console.log('Status:', data.text);
});

eventSource.addEventListener('card', (event) => {
  const data = JSON.parse(event.data);
  console.log('Chart:', data.chart);
  console.log('Insight:', data.insight);
});

eventSource.addEventListener('done', () => {
  eventSource.close();
});

eventSource.addEventListener('error', (event) => {
  const data = JSON.parse(event.data);
  console.error('Error:', data.message);
  eventSource.close();
});
```

### Python

```python
import requests
import json

url = 'http://localhost:8000/chat'
data = {
    'message': 'Show weekly issuance trend',
}

with requests.post(url, json=data, stream=True) as response:
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('event:'):
                event_type = line.split(':', 1)[1].strip()
            elif line.startswith('data:'):
                event_data = json.loads(line.split(':', 1)[1].strip())
                print(f'{event_type}: {event_data}')
```

## Performance

### Latency Targets

- **P50**: < 2.5 seconds (with cache)
- **P50**: < 3.5 seconds (without cache)
- **P95**: < 6 seconds

### Caching

- **TTL**: 10 minutes (600 seconds)
- **Max Size**: 100 entries (LRU eviction)
- **Cache Hit Rate Target**: > 60%

## Error Handling

All errors are streamed as SSE events:

```
event: error
data: {"message": "Query execution failed: ..."}

event: done
data: {}
```

Common error scenarios:
- Invalid query syntax
- Database connection failure
- Timeout (> 60 seconds)
- Invalid segment filters
- Cache unavailable

## Structured Logging

All requests are logged with:

```json
{
  "timestamp": "2025-11-10T14:32:15Z",
  "event_type": "query_start|query_complete|query_error|...",
  "session_id": "uuid-v4",
  "user_text": "User query text",
  "plan": { /* Query plan object */ },
  "sql": "SELECT ...",
  "row_count": 1234,
  "latency_ms": 1850.5,
  "cache_hit": true,
  "error": "Error message if any"
}
```

### Event Types

- query_start, query_complete, query_error
- streaming_error
- chart_request, chart_retrieved, chart_not_found, chart_error
- suggest_request, suggest_complete, suggest_error
- export_request, export_complete, export_not_found, export_error
- health_check, health_check_error
- service_startup, service_shutdown

## CORS Configuration

The API allows requests from:
- `http://localhost:3000` (Next.js dev server)
- `http://127.0.0.1:3000`

To add more origins, update the `allow_origins` list in `main.py`.

## Testing

Run the test suite:

```bash
# From topup-backend directory
pytest tests/app/ -v

# With coverage
pytest tests/app/ --cov=app --cov-report=html
```

## Security

- **CORS**: Restricted to localhost origins
- **Input Validation**: Pydantic models validate all inputs
- **Error Messages**: Generic errors to prevent information leakage
- **SQL Safety**: Handled by guardrail agent (read-only, parameterized)
