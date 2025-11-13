# Implementation Plan

- [x] 1. Set up project structure and core dependencies





  - Create backend directory structure (app/, agents/, tools/, templates/, models/)
  - Create frontend directory structure (app/, components/, hooks/, lib/)
  - Initialize Python virtual environment and install FastAPI, LangChain, LangGraph, Chroma, Pydantic, SQLite-utils, Plotly
  - Initialize Next.js project with TypeScript, TailwindCSS, and shadcn/ui
  - Install frontend dependencies: TanStack Query, Zustand, react-hook-form, zod, react-plotly.js, Framer Motion
  - Create .env files for backend and frontend with placeholder values
  - _Requirements: 1.1, 2.1_

- [x] 2. Implement data models and Pydantic schemas





  - Create Plan schema with intent, table, metric, date_col, window, granularity, segments, and chart fields
  - Create SegmentFilters schema with channel, grade, prod_type, repeat_type, term, cr_fico_band fields
  - Create Insight schema with title, summary, bullets, and drivers fields
  - Create Driver schema with segment, value, delta, delta_pct fields
  - Implement cache_key() method on Plan model using SHA256 hash
  - _Requirements: 1.3, 5.1_

- [x] 3. Create SQLite database setup and SQL templates







  - Create sample cps_tb table with app_submit_d, app_submit_amt, apps_approved_d, approval_amt, issued_d, issued_amt, channel, grade, prod_type, repeat_type, term, cr_fico, cr_fico_band, cr_appr_flag, offered_flag, issued_flag, offer_apr columns
  - Create sample forecast_df table with date, channel, grade, forecast_issuance, actual_issuance columns
  - Populate tables with sample data for testing
  - Create trend_weekly.sql template with parameterized date filters and segment filters
  - Create funnel_last_full_month.sql template for submission→approval→issuance funnel
  - Create forecast_vs_actual_weekly.sql template with delta and accuracy calculations
  - Create mom_delta.sql template for month-over-month comparison
  - Create wow_delta.sql template for week-over-week comparison
  - Create distribution.sql template for segment composition analysis
  - Ensure all templates use NULLIF for division guards and proper SQLite date functions
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 12.1, 12.2, 12.3_

- [x] 4. Implement SQL Tool with read-only execution





  - Create sql_tool.py with run(plan: Plan) -> DataFrame function
  - Implement template selection logic based on plan.intent
  - Implement parameter binding from plan.segments using SQLite parameter substitution
  - Open SQLite connection with read-only flag
  - Execute query and return pandas DataFrame
  - Apply 10,000 row limit
  - Log query text, parameters, row count, and execution latency
  - _Requirements: 1.4, 7.1-7.9, 12.1, 12.2, 12.3, 13.3, 13.4, 16.3, 16.4_

- [x] 5. Implement Cache Tool with in-memory LRU cache





  - Create cache_tool.py with get(key: str) and set(key: str, value: dict, ex: int) functions
  - Implement in-memory dict with timestamp-based TTL expiration
  - Implement LRU eviction when cache size exceeds limit (e.g., 100 entries)
  - Store serialized DataFrames, Plotly specs, and Insights
  - Return None for expired or missing entries
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 6. Implement Chart Tool for Plotly spec generation





  - Create chart_tool.py with build(plan: Plan, df: DataFrame) -> dict function
  - Implement line chart generation for trend intent
  - Implement grouped bar chart generation for forecast_vs_actual intent
  - Implement funnel chart generation for funnel intent
  - Implement pie chart generation for distribution intent
  - Implement scatter chart generation for relationship intent
  - Apply FICO band sort order (<640, 640-699, 700-759, 760+) for categorical axes
  - Add annotations for last two periods in trend charts
  - Generate theme-aware colors (light/dark mode support)
  - Return Plotly JSON specification
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 17.1, 17.2, 17.3, 17.4, 17.5_

- [x] 7. Implement Insights Agent for narrative generation




  - Create insights_agent.py with summarize(plan: Plan, df: DataFrame) -> Insight function
  - Calculate MoM percentage deltas for variance intent
  - Calculate WoW percentage deltas for variance intent
  - Identify top 3 positive segment drivers by delta
  - Identify top 3 negative segment drivers by delta
  - Calculate forecast accuracy metrics for forecast_vs_actual intent
  - Calculate conversion rates for funnel intent
  - Generate one-line executive summary
  - Generate 2-3 bullet points highlighting key findings
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 8.6, 9.6_
-

- [x] 8. Implement Router Agent for intent classification



  - Create router.py with classify(user_query: str) -> str function
  - Use OpenAI function calling with enum constraint for 7 intents: trend, variance, forecast_vs_actual, funnel, distribution, relationship, explain
  - Create system prompt with few-shot examples for each intent type
  - Recognize business-friendly terms: "app submits", "app approvals", "issuances"
  - Return classified intent string
  - _Requirements: 1.2_

- [x] 9. Implement Planner Agent with structured outputs




  - Create planner.py with make_plan(user_query: str, intent: str) -> Plan function
  - Use OpenAI structured outputs to generate Plan JSON
  - Apply default rules: 30-day window if not specified, weekly granularity for ≤3 months
  - Interpret "app submits", "app approvals", "issuances" as amounts by default
  - Only use count metrics when user explicitly requests "number of" or "count of"
  - Select appropriate table (cps_tb or forecast_df) based on intent
  - Select appropriate date column based on metric (app_submit_d for submits, apps_approved_d for approvals, issued_d for issuances)
  - Select appropriate chart type based on intent
  - Parse and validate segment filters from user query
  - Return validated Plan object
  - _Requirements: 1.3, 5.2, 6.1, 6.6, 6.7_

- [x] 10. Implement Guardrail Agent for validation





  - Create guardrail.py with validate(plan: Plan, sql: str) -> bool function
  - Check SQL for INSERT, UPDATE, DELETE, DROP, ALTER keywords and reject if found
  - Check SQL for semicolons or multiple statements and reject if found
  - Validate segment filter values against allowed distinct values from database
  - Enforce maximum time window of 1 year unless explicitly requested
  - Log security events for rejected queries
  - Return validation result with error message if rejected
  - _Requirements: 5.4, 5.5, 12.4, 12.5, 13.1, 13.2, 13.5_


- [x] 11. Initialize Chroma RAG Tool for glossary retrieval







  - Create rag_tool.py with retrieve(query: str, k: int) -> List[str] function
  - Initialize Chroma client with persistent storage in ./data/chroma
  - Create collection for schema and KPI definitions
  - Index sample documents: KPI definitions (app submits, app approvals, issuances, approval rate, funding rate, average APR, average FICO), schema descriptions, field value profiles
  - Add 25-50 Q&A exemplars (e.g., "What is funding rate?" → definition)
  - Use OpenAI text-embedding-3-small for embeddings
  - Implement semantic search with top-k retrieval (k=3)
  - Return list of relevant document texts
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 12. Implement Memory Agent for explain queries





  - Create memory_agent.py with explain(user_query: str) -> str function
  - Call RAG Tool retrieve() with user query
  - Format retrieved definitions into readable response
  - Return explanation text
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_
-

- [x] 13. Implement LangGraph orchestration




  - Create main orchestrator in agents/__init__.py
  - Define StateGraph with nodes: router, planner, guardrail, sql, chart, insights, memory
  - Define edges: router→planner→guardrail→sql→(chart+insights in parallel)
  - Define conditional edge: router→memory for explain intent
  - Implement state management for passing data between agents
  - Add error handling and retry logic (max 2 attempts)
  - Return final result with chart spec and insights
  - _Requirements: 1.2, 1.3, 1.4_
-

- [x] 14. Create FastAPI endpoints with SSE streaming




  - Create main.py with FastAPI app and CORS middleware
  - Implement POST /chat endpoint accepting message and filters
  - Implement SSE streaming with text/event-stream content type
  - Stream partial messages: "Planning your query...", "Crunching numbers..."
  - Check cache before executing agent graph
  - Execute LangGraph orchestrator if cache miss
  - Stream plan JSON, chart spec, and insights as separate SSE events
  - Stream done signal when complete
  - Cache result with 10-minute TTL
  - Implement error handling and stream error events
  - _Requirements: 1.1, 2.1, 2.2, 2.3, 2.4, 2.5, 10.1, 10.2, 10.3, 10.4, 10.5_


- [x] 15. Create additional FastAPI endpoints




  - Implement GET /chart endpoint accepting cache_key and returning cached chart spec
  - Implement GET /suggest endpoint accepting context and returning 3 follow-up question suggestions
  - Implement GET /export endpoint accepting cache_key and format (csv/png) and returning file download
  - Add structured logging for all endpoints with timestamp, session_id, user_text, plan, sql, row_count, latency
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 15.1, 15.2, 15.3, 15.4, 15.5, 16.1, 16.2, 16.3, 16.4, 16.5_

- [x] 16. Create Next.js app structure and layout





  - Create app/layout.tsx with global shell, TailwindCSS imports, and theme provider
  - Create app/globals.css with Tailwind base styles and shadcn theme variables
  - Create app/page.tsx as main chat interface
  - Set up shadcn/ui configuration with components.json
  - Install shadcn components: Button, Input, Card, Tabs, DropdownMenu, Badge, Skeleton
  - Configure light/dark theme toggle with local storage persistence
  - _Requirements: 18.1, 18.2, 18.3_

- [x] 17. Implement Zustand chat store





  - Create hooks/useChatStore.ts with ChatStore interface
  - Implement messages array state with Message type (user/assistant, content, timestamp)
  - Implement running boolean state for loading indicator
  - Implement filters state for segment selections
  - Implement pushUser(text: string) action
  - Implement pushAssistant(content: any) action supporting text and card attachments
  - Implement setRunning(running: boolean) action
  - Implement setFilters(filters: SegmentFilters) action
  - Implement clearMessages() action
  - _Requirements: 1.1, 2.1, 5.1, 5.2, 5.3, 20.4, 20.5_
-

- [x] 18. Create useSSE hook for streaming




  - Create hooks/useSSE.ts with useSSE(url, onMessage, onDone) function
  - Initialize EventSource with provided URL
  - Set up onmessage handler to parse JSON and call onMessage callback
  - Set up onerror handler to close connection and call onDone callback
  - Return close() function for manual connection termination
  - Clean up EventSource on unmount
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 19. Implement ChatWindow component





  - Create components/chat/ChatWindow.tsx
  - Render message list with scroll container
  - Implement auto-scroll to bottom on new messages
  - Implement scroll-to-bottom button when user scrolls up
  - Display user and assistant messages using ChatMessage component
  - Show typing indicator with animated dots when running state is true
  - _Requirements: 2.1, 2.3, 19.1, 19.2, 19.3, 19.4, 19.5_

- [x] 20. Implement ChatMessage component




  - Create components/chat/ChatMessage.tsx
  - Accept message prop with role (user/assistant), content, and timestamp
  - Render user messages with right-aligned styling
  - Render assistant messages with left-aligned styling
  - Support markdown formatting in message content
  - Display timestamp in relative format (e.g., "2 minutes ago")
  - Render chart cards for messages with card attachments
  - _Requirements: 2.3, 4.5_

- [x] 21. Implement ChatInput component





  - Create components/chat/ChatInput.tsx
  - Render multiline textarea with auto-resize
  - Implement Send button with loading state
  - Implement Stop button to cancel streaming (visible when running)
  - Detect Enter key to send (Shift+Enter for new line)
  - Clear input after sending
  - Disable input when running state is true
  - _Requirements: 1.1, 2.1_


- [x] 22. Implement Toolbar component with time chips








  - Create components/chat/Toolbar.tsx
  - Render quick time period chips: "Last 7 days", "Last full week", "Last full month", "Last 3 full months"
  - Implement click handlers to append time period to query or create new query
  - Render segment filter dropdowns using SegmentFilter component
  - Render theme toggle button
  - Apply selected filters to next query

  - _Requirements: 20.1, 20.2, 20.3_


- [x] 23. Implement SegmentFilter component




  - Create components/filters/SegmentFilter.tsx
  - Use shadcn Combobox for segment selection
  - Fetch allowed values from backend API on mount
  - Support single-select for channel, grade, prod_type, repeat_type, term, cr_fico_band
  - Implement clear/reset button


  - Update Zustand store filters on selection change

  - _Requirements: 5.1, 5.2, 5.3, 5.4, 20.3, 20.4_

- [x] 24. Implement Plot component for chart rendering






  - Create components/charts/Plot.tsx
  - Wrap react-plotly.js with theme-aware configuration
  - Accept plotly prop with Plotly JSON specification
  - Apply theme colors (plot_bgcolor, paper_bgcolor) based on current theme
  - Implement responsive sizing
  - Enable hover tooltips and zoom controls
  - _Requirements: 3.7, 17.4, 18.4_


- [x] 25. Implement ChartCard component




  - Create components/charts/ChartCard.tsx
  - Render Card container with title and metadata
  - Render Plot component with chart spec
  - Implement export menu with PNG and CSV options
  - Implement "Explain" button to trigger insights for the chart
  - Call /export endpoint on export button click
  - Trigger file download for exported data
  - _Requirements: 3.7, 14.1, 14.2, 14.3_

- [x] 26. Implement main chat page with SSE integration




  - Update app/page.tsx to integrate all components
  - Implement send() function to initiate SSE connection to /chat endpoint
  - Parse SSE messages and update chat store accordingly
  - Handle partial messages by appending to last assistant message
  - Handle plan messages by logging to console (optional display)
  - Handle card messages by pushing chart card to messages
  - Handle done messages by closing SSE connection and setting running to false
  - Handle error messages by displaying error toast
  - Implement split-pane layout: left = chat thread, right = latest insight cards
  - _Requirements: 1.1, 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 27. Implement theme toggle functionality




  - Create theme context provider in app/layout.tsx
  - Implement toggle function to switch between light and dark themes
  - Persist theme preference in localStorage
  - Apply saved theme on page load
  - Update CSS variables for theme colors
  - Update Plotly chart colors dynamically on theme change
  - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

- [x] 28. Create backend requirements.txt and setup script





  - List all Python dependencies with versions: fastapi, uvicorn, langchain, langgraph, chromadb, pydantic, pandas, sqlite-utils, plotly, openai
  - Create setup.sh script to create virtual environment and install dependencies
  - Create run.sh script to start FastAPI server with uvicorn
  - _Requirements: 1.1_

- [x] 29. Create frontend package.json and setup script





  - List all npm dependencies with versions: next, react, typescript, tailwindcss, @tanstack/react-query, zustand, react-hook-form, zod, react-plotly.js, plotly.js, framer-motion
  - Create setup script to install dependencies with pnpm
  - Create dev script to start Next.js dev server
  - _Requirements: 1.1_

- [x] 30. Create sample data generation script





  - Create scripts/generate_sample_data.py
  - Generate 1000+ rows of sample cps_tb data with realistic distributions
  - Generate 100+ rows of sample forecast_df data with forecast vs actual variances
  - Ensure data covers last 6 months for testing time windows
  - Include variety of channels, grades, FICO bands, and other segments
  - Insert data into SQLite database
  - _Requirements: 1.1_

- [x] 31. Create environment configuration files




  - Create backend/.env.example with DATABASE_URL, CHROMA_PATH, OPENAI_API_KEY, CACHE_TYPE placeholders
  - Create frontend/.env.example with NEXT_PUBLIC_API placeholder
  - Create README.md with setup instructions, architecture overview, and usage examples
  - Document environment variables and their purposes
  - _Requirements: 1.1_

- [x] 32. Implement end-to-end integration and manual testing







  - Start backend server and verify /chat endpoint responds
  - Start frontend dev server and verify UI loads
  - Test trend query: "Show WoW issuance by channel last 8 weeks"
  - Test forecast query: "How did actual issuance compare to forecast last month by grade?"
  - Test funnel query: "Show the funnel for NP channel Email"
  - Test explain query: "What is funding rate?"
  - Test segment filters: Apply channel filter and verify query includes filter
  - Test time chips: Click "Last 7 days" and verify query uses correct window
  - Test chart interactions: Hover, zoom, export PNG/CSV
  - Test theme toggle: Switch between light and dark mode
  - Test cache: Repeat query and verify faster response
  - Verify all queries complete within 3.5 seconds
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1-3.7, 4.1-4.5, 5.1-5.5, 6.1-6.7, 8.1-8.6, 9.1-9.6, 10.1-10.5, 11.1-11.5, 14.1-14.5, 15.1-15.5, 17.1-17.5, 18.1-18.5, 20.1-20.5_
