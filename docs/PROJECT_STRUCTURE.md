# Project Structure

This document describes the organization of the Topup CXO Assistant codebase.

## Root Directory

```
topup-cxo-assistant/
├── docs/                    # Consolidated documentation
│   ├── backend/            # Backend documentation
│   │   ├── AGENTS.md       # Agent system documentation
│   │   └── API.md          # API endpoint documentation
│   ├── frontend/           # Frontend documentation
│   │   └── COMPONENTS.md   # Component documentation
│   └── PROJECT_STRUCTURE.md # This file
│
├── topup-backend/          # FastAPI backend
│   ├── agents/             # LangGraph agents
│   │   ├── router.py       # Intent classification
│   │   ├── planner.py      # Query plan generation
│   │   ├── guardrail.py    # Security validation
│   │   ├── insights_agent.py # Narrative insights
│   │   ├── memory_agent.py # RAG-based explanations
│   │   └── __init__.py     # LangGraph orchestration
│   │
│   ├── app/                # FastAPI application
│   │   ├── main.py         # Main app with SSE streaming
│   │   ├── demo_sse.py     # SSE demo script
│   │   └── README.md       # App documentation
│   │
│   ├── data/               # Database and setup
│   │   ├── topup.db        # SQLite database
│   │   ├── setup_database.py # Database initialization
│   │   ├── verify_database.py # Database verification
│   │   └── verify_segments.py # Segment validation
│   │
│   ├── models/             # Pydantic data models
│   │   └── schemas.py      # Plan, Insight, SegmentFilters
│   │
│   ├── scripts/            # Utility scripts
│   │   ├── generate_sample_data.py # Sample data generator
│   │   └── verify_data.py  # Data verification
│   │
│   ├── templates/          # SQL query templates
│   │   ├── trend_weekly.sql
│   │   ├── wow_delta.sql
│   │   ├── mom_delta.sql
│   │   ├── forecast_vs_actual_weekly.sql
│   │   ├── funnel_last_full_month.sql
│   │   └── distribution.sql
│   │
│   ├── tests/              # Test suite
│   │   ├── agents/         # Agent tests
│   │   ├── app/            # API tests
│   │   ├── data/           # Database tests
│   │   └── tools/          # Tool tests
│   │
│   ├── tools/              # Agent tools
│   │   ├── sql_tool.py     # SQL execution
│   │   ├── chart_tool.py   # Plotly chart generation
│   │   ├── cache_tool.py   # LRU caching
│   │   ├── rag_tool.py     # RAG retrieval
│   │   ├── demo_rag_tool.py # RAG demo
│   │   ├── verify_rag_tool.py # RAG verification
│   │   └── check_api_access.py # API access checker
│   │
│   ├── .env                # Environment variables (not in git)
│   ├── .env.example        # Environment template
│   ├── requirements.txt    # Python dependencies
│   ├── setup.sh/.bat       # Setup scripts
│   └── run.sh/.bat         # Run scripts
│
└── topup-frontend/         # Next.js frontend
    ├── app/                # Next.js app router
    │   ├── page.tsx        # Main chat page
    │   ├── layout.tsx      # Root layout with theme provider
    │   └── globals.css     # Global styles and CSS variables
    │
    ├── components/         # React components
    │   ├── chat/           # Chat UI components
    │   │   ├── ChatWindow.tsx
    │   │   ├── ChatInput.tsx
    │   │   ├── ChatMessage.tsx
    │   │   └── Toolbar.tsx
    │   │
    │   ├── charts/         # Chart components
    │   │   ├── Plot.tsx    # Plotly wrapper
    │   │   ├── ChartCard.tsx # Card with export
    │   │   ├── ChartCard.example.tsx # Usage examples
    │   │   └── index.ts    # Barrel exports
    │   │
    │   ├── filters/        # Filter components
    │   │   ├── SegmentFilter.tsx
    │   │   └── index.ts
    │   │
    │   ├── ui/             # shadcn/ui components
    │   │   ├── badge.tsx
    │   │   ├── button.tsx
    │   │   ├── card.tsx
    │   │   ├── dropdown-menu.tsx
    │   │   ├── input.tsx
    │   │   ├── select.tsx
    │   │   ├── skeleton.tsx
    │   │   ├── tabs.tsx
    │   │   └── textarea.tsx
    │   │
    │   ├── theme-provider.tsx # Theme context
    │   └── theme-toggle.tsx   # Theme switcher
    │
    ├── hooks/              # Custom React hooks
    │   ├── useChatStore.ts # Zustand store
    │   └── useSSE.ts       # SSE streaming hook
    │
    ├── lib/                # Utility functions
    │   ├── utils.ts        # General utilities
    │   └── date-utils.ts   # Date formatting
    │
    ├── tests/              # Frontend tests
    │
    ├── .env                # Environment variables (not in git)
    ├── .env.example        # Environment template
    ├── package.json        # npm dependencies
    ├── tsconfig.json       # TypeScript config
    ├── tailwind.config.ts  # Tailwind config
    ├── next.config.js      # Next.js config
    ├── components.json     # shadcn/ui config
    ├── setup.sh/.bat       # Setup scripts
    └── README.md           # Frontend documentation
```

## Key Directories

### Backend

- **agents/**: Multi-agent system for query processing
- **app/**: FastAPI application with SSE streaming
- **data/**: SQLite database and initialization scripts
- **models/**: Pydantic schemas for data validation
- **templates/**: Whitelisted SQL query templates
- **tests/**: Comprehensive test suite
- **tools/**: Reusable tools for agents (SQL, Chart, Cache, RAG)

### Frontend

- **app/**: Next.js 14 app router pages
- **components/**: Reusable React components organized by feature
- **hooks/**: Custom React hooks for state and SSE
- **lib/**: Utility functions
- **tests/**: Frontend test suite

### Documentation

- **docs/backend/**: Backend documentation (agents, API)
- **docs/frontend/**: Frontend documentation (components)
- **docs/PROJECT_STRUCTURE.md**: This file

## File Naming Conventions

### Backend (Python)
- **snake_case** for files: `insights_agent.py`, `sql_tool.py`
- **PascalCase** for classes: `RAGTool`, `InsightsAgent`
- **snake_case** for functions: `make_plan()`, `validate()`
- **Test files**: `test_*.py` in `tests/` directory

### Frontend (TypeScript/React)
- **PascalCase** for components: `ChatWindow.tsx`, `SegmentFilter.tsx`
- **camelCase** for hooks: `useChatStore.ts`, `useSSE.ts`
- **kebab-case** for utilities: `date-utils.ts`
- **Test files**: `*.test.tsx` in `tests/` directory

## Configuration Files

### Backend
- `.env` - Environment variables (DATABASE_URL, OPENAI_API_KEY, etc.)
- `requirements.txt` - Python dependencies
- `.gitignore` - Git ignore patterns

### Frontend
- `.env.local` - Environment variables (NEXT_PUBLIC_API_URL)
- `package.json` - npm dependencies and scripts
- `tsconfig.json` - TypeScript compiler options
- `tailwind.config.ts` - Tailwind CSS configuration
- `next.config.js` - Next.js configuration
- `components.json` - shadcn/ui configuration

## Data Flow

```
User Input (Frontend)
    ↓
ChatInput Component
    ↓
SSE Connection (useSSE hook)
    ↓
POST /chat (FastAPI)
    ↓
LangGraph Orchestration
    ↓
Router → Planner → Guardrail → SQL → Chart + Insights
    ↓
Cache Storage
    ↓
SSE Stream (partial, plan, card, done)
    ↓
ChatWindow Component
    ↓
ChartCard Component (with Plot)
```

## Testing Structure

### Backend Tests (`topup-backend/tests/`)
```
tests/
├── agents/
│   ├── test_router.py
│   ├── test_planner.py
│   ├── test_guardrail.py
│   ├── test_insights_agent.py
│   ├── test_memory_agent.py
│   └── test_orchestration.py
├── app/
│   ├── test_main.py
│   └── test_endpoints.py
├── data/
│   ├── test_accuracy.py
│   ├── test_templates.py
│   └── test_new_columns.py
└── tools/
    ├── test_sql_tool.py
    ├── test_chart_tool.py
    ├── test_cache_tool.py
    └── test_rag_tool.py
```

### Frontend Tests (`topup-frontend/tests/`)
```
tests/
├── components/
│   ├── chat/
│   ├── charts/
│   └── filters/
└── hooks/
```

## Build Artifacts

### Backend
- `__pycache__/` - Python bytecode cache
- `.pytest_cache/` - pytest cache
- `data/chroma/` - ChromaDB vector database
- `data/topup.db` - SQLite database

### Frontend
- `.next/` - Next.js build output
- `node_modules/` - npm dependencies
- `.next/cache/` - Next.js cache

## Environment Variables

### Backend (`.env`)
```
DATABASE_URL=./data/topup.db
CHROMA_PATH=./data/chroma
OPENAI_API_KEY=sk-...
CACHE_TYPE=memory
```

### Frontend (`.env.local`)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Scripts

### Backend
- `setup.sh/.bat` - Install dependencies and initialize database
- `run.sh/.bat` - Start FastAPI server
- `scripts/generate_sample_data.py` - Generate sample data
- `scripts/verify_data.py` - Verify database integrity

### Frontend
- `npm install` - Install dependencies
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm test` - Run tests

## Documentation References

- **Backend Agents**: [docs/backend/AGENTS.md](./backend/AGENTS.md)
- **Backend API**: [docs/backend/API.md](./backend/API.md)
- **Frontend Components**: [docs/frontend/COMPONENTS.md](./frontend/COMPONENTS.md)
- **Main README**: [../README.md](../README.md)
