# Tools Module

This directory contains the core tools used by the Topup CXO Assistant agents.

## Available Tools

### 1. SQL Tool (`sql_tool.py`)

Executes read-only SQL queries against the SQLite database using whitelisted templates.

**Key Features:**
- Template-based query execution
- Parameterized queries for security
- Read-only database access
- 10,000 row limit enforcement
- Query logging with latency tracking

**Usage:**
```python
from tools.sql_tool import run
from models.schemas import Plan

result_df = run(plan)
```

### 2. Cache Tool (`cache_tool.py`)

In-memory LRU cache with TTL expiration for storing query results.

**Key Features:**
- LRU (Least Recently Used) eviction policy
- TTL (Time To Live) expiration (default: 10 minutes)
- Thread-safe operations
- DataFrame serialization support
- Configurable cache size (default: 100 entries)

**Usage:**
```python
from tools.cache_tool import get, set

# Store result
set(cache_key, {
    'df': dataframe,
    'chart': plotly_spec,
    'insight': insight_obj
}, ex=600)

# Retrieve result
result = get(cache_key)
if result:
    df = result['df']
    chart = result['chart']
    insight = result['insight']
```

**Cache Configuration:**
- `max_size`: Maximum number of entries (default: 100)
- `default_ttl`: Default TTL in seconds (default: 600 = 10 minutes)

**Cache Behavior:**
- When cache is full, least recently used entry is evicted
- Expired entries are automatically removed on access
- DataFrames are serialized using pickle for efficient storage
- Thread-safe for concurrent access

## Testing

Each tool has a corresponding test file:

- `test_sql_tool.py` - Tests for SQL Tool
- `test_cache_tool.py` - Tests for Cache Tool
- `test_chart_tool.py` - Tests for Chart Tool

Run tests:
```bash
# Test SQL Tool
python tools/test_sql_tool.py

# Test Cache Tool
python tools/test_cache_tool.py

# Test Chart Tool
python -m pytest tools/test_chart_tool.py -v
```

### 3. Chart Tool (`chart_tool.py`)

Generates Plotly JSON specifications for various chart types based on query plans and data.

**Key Features:**
- Multiple chart types: line, area, bar, grouped bar, funnel, pie, scatter
- Theme-aware colors (light/dark mode)
- FICO band sorting for categorical axes
- Annotations for trend charts (last two periods)
- Responsive layouts with hover tooltips

**Supported Chart Types:**
- **Line/Area Charts** - Trend analysis with time series data
- **Grouped Bar Charts** - Forecast vs actual comparisons
- **Funnel Charts** - Conversion analysis
- **Pie Charts** - Distribution analysis
- **Scatter Charts** - Relationship analysis with optional grouping

**Usage:**
```python
from tools.chart_tool import build
from models.schemas import Plan

# Generate chart specification
plotly_spec = build(plan, dataframe, theme="light")

# Returns Plotly JSON with data and layout
# {
#   "data": [...],  # Plotly traces
#   "layout": {...}  # Layout configuration
# }
```

**Theme Support:**
- `light` - Light mode with bright colors
- `dark` - Dark mode with muted colors

**Special Features:**
- FICO bands automatically sorted: <640, 640-699, 700-759, 760+
- Trend charts include annotations for last two data points
- Multi-series support for grouped data
- Empty data handling with placeholder message

## Future Tools

The following tools will be implemented in future tasks:

- **RAG Tool** - Retrieval-augmented generation for glossary queries
- **Narrative Tool** - Generates executive insights and variance analysis
