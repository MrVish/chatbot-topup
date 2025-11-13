# Topup CXO Assistant

A conversational CXO marketing assistant that enables executives to query marketing data through natural language, receive fast SQL-based analytics, and view insights through interactive charts.

## Architecture Overview

Topup uses a multi-agent architecture with LangGraph orchestration to process natural language queries and generate insights.

### Technology Stack

- **Frontend**: Next.js 14 with TypeScript, TailwindCSS, and shadcn/ui
- **Backend**: FastAPI with LangChain + LangGraph for agent orchestration
- **Database**: SQLite for customer acquisition (cps_tb) and forecast data (forecast_df)
- **Vector DB**: Chroma for RAG-based glossary and schema retrieval
- **Caching**: In-memory LRU cache (Phase 1) / Redis (Phase 2)
- **Charts**: Plotly.js for interactive visualizations
- **State Management**: Zustand for frontend state
- **Streaming**: Server-Sent Events (SSE) for real-time responses

### Agent Flow

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

### Agent Responsibilities

- **Router Agent**: Classifies user intent (trend, variance, forecast_vs_actual, forecast_gap_analysis, funnel, distribution, relationship, explain)
- **Planner Agent**: Generates structured query plan with table, metric, date column, time window, granularity, segments, and chart type
- **Guardrail Agent**: Validates SQL safety (read-only, no injection), segment values, and time window limits
- **SQL Agent**: Executes parameterized queries from whitelisted templates with 10,000 row limit
- **Chart Agent**: Generates Plotly JSON specifications based on intent (line, bar, funnel, pie, scatter, waterfall)
- **Insights Agent**: Calculates MoM/WoW deltas, identifies top drivers, generates executive summaries
- **Memory Agent**: Retrieves definitions from RAG system for "explain" queries

### Performance Targets

- **P50 Latency**: < 2.5 seconds (cached queries)
- **P50 Latency**: < 3.5 seconds (uncached queries)
- **P95 Latency**: < 6 seconds
- **Cache Hit Rate**: > 60%
- **SQL Execution**: < 500ms

## Project Structure

```
topup-cxo-assistant/
├── topup-backend/          # FastAPI backend
│   ├── app/                # FastAPI application
│   ├── agents/             # LangGraph agents
│   ├── tools/              # SQL, Chart, Cache, RAG tools
│   ├── models/             # Pydantic data models
│   ├── templates/          # SQL query templates
│   ├── data/               # SQLite database and Chroma storage
│   ├── requirements.txt    # Python dependencies
│   ├── setup.sh/.bat       # Setup script
│   └── run.sh/.bat         # Run script
│
└── topup-frontend/         # Next.js frontend
    ├── app/                # Next.js app router
    ├── components/         # React components
    │   ├── chat/           # Chat UI components
    │   ├── charts/         # Chart components
    │   ├── filters/        # Filter components
    │   └── ui/             # shadcn/ui components
    ├── hooks/              # Custom React hooks
    ├── lib/                # Utility functions
    └── package.json        # npm dependencies
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd topup-backend
   ```

2. Run the setup script:
   - **Linux/Mac**: `./setup.sh`
   - **Windows**: `setup.bat`

3. Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   ```

4. Add your OpenAI API key to `.env`:
   ```
   OPENAI_API_KEY=sk-your-api-key-here
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd topup-frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   # or
   pnpm install
   # or
   yarn install
   ```

3. Copy `.env.example` to `.env.local`:
   ```bash
   cp .env.example .env.local
   ```

## Running the Application

### Start Backend Server

```bash
cd topup-backend
# Linux/Mac
./run.sh

# Windows
run.bat
```

The backend will start on `http://localhost:8000`

### Start Frontend Server

```bash
cd topup-frontend
npm run dev
# or
pnpm dev
# or
yarn dev
```

The frontend will start on `http://localhost:3000`

## Environment Variables

### Backend (.env)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | Path to SQLite database file. Can be relative or absolute path. | `./data/topup.db` | Yes |
| `CHROMA_PATH` | Path to Chroma vector database storage directory. Used for RAG-based glossary and schema retrieval. | `./data/chroma` | Yes |
| `OPENAI_API_KEY` | Your OpenAI API key for LLM calls (Router, Planner, Insights agents). Get from https://platform.openai.com/api-keys | None | Yes |
| `CACHE_TYPE` | Cache implementation type. Use `memory` for local development (in-memory LRU cache) or `redis` for production (requires Redis server). | `memory` | Yes |

**Note**: The `.env.example` file contains placeholder values. Copy it to `.env` and update with your actual values before running the backend.

### Frontend (.env.local)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL. Must be accessible from the browser. Use `http://localhost:8000` for local development. | `http://localhost:8000` | Yes |

**Note**: Next.js requires environment variables exposed to the browser to be prefixed with `NEXT_PUBLIC_`. The `.env.example` file can be copied to `.env.local` for local development.

## Key Features

- **Natural Language Queries**: Ask questions in plain English about marketing metrics
- **Real-time Streaming**: SSE-based streaming responses for perceived speed
- **Interactive Charts**: Plotly-powered visualizations with hover tooltips and zoom
- **Executive Insights**: AI-generated summaries and variance analysis with MoM/WoW deltas
- **Segment Filters**: Filter by channel, grade, FICO band, product type, repeat type, and term
- **Time Period Chips**: Quick access to common time windows (Last 7 days, Last full week, etc.)
- **Export Capabilities**: Download charts as PNG or data as CSV
- **Theme Support**: Light and dark mode with theme-aware chart colors
- **Caching**: 10-minute TTL for fast repeated queries (60%+ cache hit rate target)
- **RAG-based Glossary**: Ask "What is funding rate?" to get definitions
- **Security**: Read-only SQL, parameterized queries, input validation

## Usage Examples

### Example Queries

**Trend Analysis:**
- "Show WoW issuance by channel last 8 weeks"
- "What's the trend in app submits by grade over the last 3 months?"
- "Display weekly approval amounts for Email channel"

**Variance Analysis:**
- "How did issuances change MoM for each grade?"
- "Show me WoW delta in app approvals by FICO band"

**Forecast vs Actual:**
- "How did actual issuance compare to forecast last month by grade?"
- "Show forecast accuracy by channel for the last full month"

**Forecast Gap Analysis:**
- "Where are we seeing the largest gap between forecast and actual for issuance?"
- "Show me the forecast gap analysis for submits"
- "What's driving the forecast miss for approvals?"
- "Forecast variance decomposition for issuance this month"

**Funnel Analysis:**
- "Show the funnel for NP channel Email"
- "What's the conversion rate from submission to issuance?"

**Distribution Analysis:**
- "Show the distribution of issuances by FICO band"
- "What's the composition of app submits by grade?"

**Glossary/Definitions:**
- "What is funding rate?"
- "Explain approval rate"
- "What does FICO band mean?"

### Using Segment Filters

1. Select filters from the toolbar (channel, grade, FICO band, etc.)
2. Type your query - filters will be automatically applied
3. Clear filters by clicking the X button on each filter chip

### Using Time Period Chips

Click any time period chip to quickly filter data:
- **Last 7 days**: Rolling 7-day window
- **Last full week**: Previous Monday-Sunday
- **Last full month**: Previous calendar month
- **Last 3 full months**: Previous 3 complete months (excluding current)

## API Endpoints

### POST /chat
Accepts natural language queries and streams responses via SSE.

**Request:**
```json
{
  "message": "Show WoW issuance by channel last 8 weeks",
  "filters": {
    "channel": "Email",
    "grade": "P1"
  }
}
```

**Response:** Server-Sent Events stream with:
- `partial`: Streaming text updates
- `plan`: Query plan JSON
- `card`: Chart spec and insights
- `done`: Completion signal
- `error`: Error messages

### GET /chart
Retrieves cached chart specification.

**Query Parameters:**
- `cache_key`: Hash of query plan

**Response:**
```json
{
  "plotly": { /* Plotly JSON spec */ },
  "data": [ /* DataFrame rows */ ],
  "explanation": "Chart explanation text"
}
```

### GET /suggest
Returns follow-up question suggestions.

**Query Parameters:**
- `context`: Current query context
- `last_intent`: Previous intent classification

**Response:**
```json
{
  "suggestions": [
    "How did this compare to last month?",
    "Show me the breakdown by grade",
    "What's the trend over the last 3 months?"
  ]
}
```

### GET /export
Exports chart data or image.

**Query Parameters:**
- `cache_key`: Hash of query plan
- `format`: `csv` or `png`

**Response:** File download

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[Backend Agents](docs/backend/AGENTS.md)** - Agent system architecture and usage
- **[Backend API](docs/backend/API.md)** - API endpoints and SSE streaming
- **[Frontend Components](docs/frontend/COMPONENTS.md)** - Component library reference
- **[Project Structure](docs/PROJECT_STRUCTURE.md)** - Codebase organization guide

## Development

### Backend Development

The backend uses:
- **FastAPI** for REST API and SSE streaming
- **LangChain + LangGraph** for agent orchestration
- **Pydantic** for data validation and structured outputs
- **SQLite** for data storage with read-only connections
- **Chroma** for vector search and RAG
- **Pandas** for data manipulation
- **Plotly** for chart specification generation

**Key Directories:**
- `agents/`: LangGraph agent implementations
- `app/`: FastAPI application and endpoints
- `tools/`: SQL, Chart, Cache, and RAG tools
- `models/`: Pydantic schemas
- `templates/`: Whitelisted SQL query templates
- `tests/`: Comprehensive test suite

### Frontend Development

The frontend uses:
- **Next.js 14** with App Router and React Server Components
- **TypeScript** for type safety
- **TailwindCSS** for styling
- **shadcn/ui** for UI components
- **Zustand** for state management
- **react-plotly.js** for charts
- **EventSource API** for SSE streaming

**Key Directories:**
- `app/`: Next.js pages and layouts
- `components/`: Reusable React components
- `hooks/`: Custom React hooks
- `lib/`: Utility functions
- `tests/`: Frontend test suite

## Troubleshooting

### Backend Issues

**"Module not found" errors:**
- Ensure virtual environment is activated: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
- Reinstall dependencies: `pip install -r requirements.txt`

**"Database not found" errors:**
- Run the sample data generation script: `python scripts/generate_sample_data.py`
- Verify `DATABASE_URL` in `.env` points to correct path

**"OpenAI API key invalid" errors:**
- Check that `OPENAI_API_KEY` in `.env` is correct
- Verify API key has sufficient credits at https://platform.openai.com/usage

**"Chroma initialization failed" errors:**
- Ensure `CHROMA_PATH` directory exists: `mkdir -p data/chroma`
- Check write permissions on the data directory

### Frontend Issues

**"Failed to fetch" errors:**
- Verify backend is running on `http://localhost:8000`
- Check `NEXT_PUBLIC_API_URL` in `.env.local` matches backend URL
- Ensure CORS is enabled in FastAPI (should be by default)

**Charts not rendering:**
- Check browser console for errors
- Verify Plotly.js is installed: `npm list plotly.js`
- Try clearing browser cache

**SSE connection errors:**
- Check browser network tab for failed SSE connections
- Verify backend `/chat` endpoint is accessible
- Some corporate firewalls block SSE - try different network

### Performance Issues

**Slow query responses:**
- Check SQL query execution time in backend logs
- Verify database indexes are created
- Consider reducing time window or adding segment filters
- Check cache hit rate in logs

**High memory usage:**
- Reduce cache size limit in `cache_tool.py`
- Clear Chroma vector DB and re-index: `rm -rf data/chroma`
- Restart backend to clear in-memory cache

## Data Models

### Database Tables

**cps_tb (Customer Acquisition)**
- `app_submit_d`: Submission date
- `app_submit_amt`: Submitted loan amount
- `apps_approved_d`: Approval date
- `approval_amt`: Approved loan amount
- `issued_d`: Issuance date
- `issued_amt`: Issued loan amount
- `channel`: Marketing channel (Email, OMB, etc.)
- `grade`: Credit grade (P1, P2, P3, P4, etc.)
- `prod_type`: Product type
- `repeat_type`: New (NP) or Repeat (RP) customer
- `term`: Loan term in months
- `cr_fico`: FICO score
- `cr_fico_band`: FICO band (<640, 640-699, 700-759, 760+)
- `cr_appr_flag`: Approval flag (0/1)
- `offered_flag`: Offer flag (0/1)
- `issued_flag`: Issuance flag (0/1)
- `offer_apr`: Offered APR

**forecast_df (Forecast Data)**
- `date`: Forecast date
- `channel`: Marketing channel
- `grade`: Credit grade
- `forecast_issuance`: Forecasted issuance amount
- `actual_issuance`: Actual issuance amount

### KPI Calculations

**Important**: By default, "App Submits", "App Approvals", and "Issuances" refer to dollar amounts (sum of loan amounts), not counts. Users must explicitly request "number of" or "count of" to get transaction counts.

| KPI | Formula | Notes |
|-----|---------|-------|
| App Submits (Amount) | `SUM(app_submit_amt)` | Default for "app submits" |
| App Submits (Count) | `COUNT(app_submit_d)` | Only when explicitly requested |
| App Approvals (Amount) | `SUM(CASE WHEN cr_appr_flag = 1 THEN approval_amt ELSE 0 END)` | Default for "app approvals" |
| App Approvals (Count) | `SUM(cr_appr_flag)` | Only when explicitly requested |
| Issuances (Amount) | `SUM(CASE WHEN issued_flag = 1 THEN issued_amt ELSE 0 END)` | Default for "issuances" |
| Issuances (Count) | `SUM(issued_flag)` | Only when explicitly requested |
| Approval Rate | `SUM(cr_appr_flag) / NULLIF(SUM(offered_flag), 0)` | Percentage |
| Funding Rate | `SUM(issued_flag) / NULLIF(COUNT(app_submit_d), 0)` | Percentage |
| Average APR | `AVG(offer_apr)` | Mean APR |
| Average FICO | `AVG(cr_fico)` | Mean FICO score |
| Forecast Delta | `actual_issuance - forecast_issuance` | Variance |
| Forecast Accuracy | `actual_issuance / NULLIF(forecast_issuance, 0)` | Ratio |
| MoM Delta | `(current_month - prior_month) / NULLIF(prior_month, 0)` | Percentage change |
| WoW Delta | `(current_week - prior_week) / NULLIF(prior_week, 0)` | Percentage change |

## Security

### SQL Safety
- **Read-only connections**: Database opened with read-only flag
- **Whitelisted templates**: Only predefined SQL templates can be executed
- **Parameterized queries**: All user inputs bound via SQLite parameter substitution
- **Keyword blacklist**: Rejects INSERT, UPDATE, DELETE, DROP, ALTER
- **Multi-statement prevention**: Rejects queries with semicolons

### Input Validation
- **Segment validation**: Values checked against allowed distinct values from database
- **Time window limits**: Maximum 1 year unless explicitly requested
- **Row limits**: 10,000 row maximum per query
- **Query timeout**: 30 seconds for SQL, 60 seconds total

### Data Privacy
- **No PII in logs**: Sensitive data scrubbed from logs
- **Session isolation**: Each session has isolated state
- **CORS restrictions**: Only allowed origins can access API
- **Rate limiting**: Per-user/IP rate limits (Phase 2)

## Testing

### Running Tests

**Backend Tests:**
```bash
cd topup-backend
pytest tests/ -v
```

**Frontend Tests:**
```bash
cd topup-frontend
npm test
# or
pnpm test
```

### Test Coverage

- **Unit Tests**: Agent logic, tool functions, data models
- **Integration Tests**: End-to-end query flows, SSE streaming, cache behavior
- **Performance Tests**: Latency benchmarks, load testing, cache hit rates
- **Security Tests**: SQL injection attempts, input validation, rate limiting

## Contributing

### Development Workflow

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Run tests: `pytest` (backend) or `npm test` (frontend)
4. Commit with descriptive message: `git commit -m "Add feature X"`
5. Push and create pull request

### Code Style

- **Backend**: Follow PEP 8, use Black for formatting
- **Frontend**: Follow Airbnb style guide, use Prettier for formatting
- **Commits**: Use conventional commits (feat:, fix:, docs:, etc.)

### Adding New Intents

1. Update Router Agent with new intent classification
2. Add SQL template in `templates/` directory
3. Update Planner Agent to handle new intent
4. Add chart generation logic in Chart Agent
5. Update Insights Agent for new metrics
6. Add tests for new intent flow

### Adding New Metrics

1. Define calculation in SQL template
2. Update KPI documentation in README
3. Add to Planner Agent metric options
4. Test with sample queries

## Roadmap

### Phase 1 (Current - MVP)
- ✅ Natural language query processing
- ✅ 7 intent types (trend, variance, forecast, funnel, distribution, relationship, explain)
- ✅ Interactive Plotly charts
- ✅ Executive insights with MoM/WoW analysis
- ✅ Segment filters and time period chips
- ✅ In-memory caching
- ✅ Light/dark theme support
- ✅ Export to CSV/PNG

### Phase 2 (Production Ready)
- [ ] Docker deployment with Docker Compose
- [ ] Redis cache for multi-instance support
- [ ] Multi-turn conversations with context retention
- [ ] Saved queries and bookmarks
- [ ] User authentication and authorization
- [ ] Scheduled reports via email
- [ ] Custom metric definitions
- [ ] Drill-down interactions (click to filter)
- [ ] Annotations on data points
- [ ] Alert system for threshold breaches

### Phase 3 (Advanced Features)
- [ ] Horizontal scaling with load balancer
- [ ] Database sharding by date range
- [ ] CDN caching for static assets
- [ ] Query queue with prioritization
- [ ] Materialized views for common aggregations
- [ ] Real-time data updates
- [ ] Mobile app (React Native)
- [ ] Voice input support
- [ ] Collaborative features (share insights)

## Support

For issues, questions, or feature requests, please contact the development team or create an issue in the project repository.

## License

Proprietary - All rights reserved
