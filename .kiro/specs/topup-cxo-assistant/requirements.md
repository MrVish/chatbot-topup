# Requirements Document

## Introduction

Topup is a conversational CXO marketing assistant that enables executives to query marketing data through natural language, receive fast SQL-based analytics, and view insights through interactive charts. The system analyzes customer acquisition data (cps_tb) and forecast data (forecast_df) to provide trend analysis, variance reporting, forecast accuracy, and funnel metrics with minimal latency.

## Glossary

- **Topup System**: The conversational CXO assistant application comprising frontend chat interface and backend orchestration
- **Chat UI**: Next.js-based web interface for user interaction
- **API Layer**: FastAPI backend service handling chat requests
- **Orchestrator**: LangChain + LangGraph agent system coordinating tool execution
- **SQL Tool**: Read-only SQLite query executor with templated queries
- **Chart Tool**: Plotly JSON specification generator for data visualization
- **Narrative Tool**: Insight generator producing executive summaries and variance analysis
- **Cache Tool**: Redis-based query result caching mechanism
- **RAG Tool**: Retrieval-augmented generation system using Chroma for schema and KPI definitions
- **Router Agent**: Intent classification component
- **Planner Agent**: Query plan generator with structured outputs
- **SQL Agent**: Template-based SQL executor
- **Chart Agent**: Plotly specification builder
- **Insights Agent**: Narrative and variance analyzer
- **Memory Agent**: RAG-based glossary and schema retrieval
- **Guardrail Agent**: Security and validation enforcement
- **cps_tb**: Customer acquisition table containing submission, approval, and issuance data
- **forecast_df**: Forecast table containing predicted vs actual issuance metrics
- **SSE**: Server-Sent Events streaming protocol
- **MoM**: Month-over-Month comparison
- **WoW**: Week-over-Week comparison

## Requirements

### Requirement 1

**User Story:** As a CXO, I want to ask questions in natural language about marketing metrics, so that I can quickly understand business performance without writing SQL queries

#### Acceptance Criteria

1. WHEN a user submits a natural language question, THE Chat UI SHALL transmit the message to the API Layer via HTTP POST
2. THE Orchestrator SHALL classify the user intent into one of seven categories: trend, variance, forecast-vs-actual, funnel, distribution, relationship, or explain metric
3. THE Orchestrator SHALL generate a structured query plan containing table selection, metric, date column, time window, granularity, segments, and chart type
4. THE Orchestrator SHALL execute the query plan through the SQL Tool and return results within 2.5 seconds at P50 latency
5. THE Chat UI SHALL display the assistant response with streaming text updates

### Requirement 2

**User Story:** As a CXO, I want to see real-time streaming responses as the system processes my query, so that I perceive the system as fast and responsive

#### Acceptance Criteria

1. WHEN the API Layer begins processing a chat request, THE API Layer SHALL establish an SSE connection with the Chat UI
2. THE API Layer SHALL stream partial messages indicating processing status before query completion
3. THE Chat UI SHALL display streaming tokens as they arrive without waiting for complete response
4. THE API Layer SHALL stream the final chart specification and insights when query execution completes
5. THE Chat UI SHALL render the complete response including chart within 2.5 seconds at P50 latency

### Requirement 3

**User Story:** As a CXO, I want to view interactive charts visualizing my data queries, so that I can quickly identify trends and patterns

#### Acceptance Criteria

1. WHEN the Chart Agent receives query results, THE Chart Agent SHALL generate a Plotly JSON specification matching the query intent
2. THE Chart Agent SHALL select line or area charts for trend queries
3. THE Chart Agent SHALL select grouped bar charts for forecast-vs-actual queries
4. THE Chart Agent SHALL select funnel charts for conversion analysis queries
5. THE Chart Agent SHALL select pie charts for composition queries
6. THE Chart Agent SHALL select scatter charts for relationship queries
7. THE Chat UI SHALL render the Plotly specification as an interactive chart with hover tooltips and zoom capabilities

### Requirement 4

**User Story:** As a CXO, I want to receive executive summaries with key insights and variance metrics, so that I can understand the business implications without analyzing raw data

#### Acceptance Criteria

1. WHEN the Insights Agent receives query results, THE Insights Agent SHALL calculate percentage deltas for MoM or WoW comparisons
2. THE Insights Agent SHALL identify top three positive and negative segment drivers
3. THE Insights Agent SHALL generate a one-line executive takeaway
4. THE Insights Agent SHALL generate two to three bullet points highlighting key findings
5. THE Chat UI SHALL display the narrative insights alongside the chart visualization

### Requirement 5

**User Story:** As a CXO, I want to filter data by business segments like channel, grade, product type, and FICO band, so that I can analyze specific customer cohorts

#### Acceptance Criteria

1. WHEN a user selects segment filters in the Chat UI, THE Chat UI SHALL include segment parameters in the query request
2. THE Planner Agent SHALL incorporate segment filters into the query plan
3. THE SQL Agent SHALL apply segment filters using parameterized WHERE clauses
4. THE Guardrail Agent SHALL validate segment values against allowed distinct values from the database
5. THE SQL Agent SHALL reject queries containing segment values not in the allowed list

### Requirement 6

**User Story:** As a CXO, I want to query data using predefined time windows like "last 7 days" or "last full month", so that I can quickly analyze recent performance

#### Acceptance Criteria

1. WHEN a user requests data without specifying a time window, THE Planner Agent SHALL default to the last 30 days
2. WHEN a user requests "last 7 days", THE SQL Agent SHALL filter data using SQLite date function with '-7 day' offset
3. WHEN a user requests "last full week", THE SQL Agent SHALL filter data from Monday to Sunday of the previous complete week
4. WHEN a user requests "last full month", THE SQL Agent SHALL filter data from the first to last day of the previous complete month
5. WHEN a user requests "last 3 months", THE SQL Agent SHALL filter data excluding the current incomplete month
6. THE Planner Agent SHALL select weekly granularity for time windows of 3 months or less
7. THE Planner Agent SHALL select monthly granularity for time windows exceeding 3 months

### Requirement 7

**User Story:** As a CXO, I want the system to calculate standard marketing KPIs correctly, so that I can trust the metrics presented

#### Acceptance Criteria

1. WHEN calculating submission count, THE SQL Agent SHALL count non-null app_submit_d values
2. WHEN calculating approval count, THE SQL Agent SHALL sum cr_appr_flag values
3. WHEN calculating issuance count, THE SQL Agent SHALL sum issued_flag values
4. WHEN calculating approval rate, THE SQL Agent SHALL divide sum of cr_appr_flag by sum of offered_flag using NULLIF to prevent division by zero
5. WHEN calculating funding rate, THE SQL Agent SHALL divide sum of issued_flag by count of non-null app_submit_d using NULLIF to prevent division by zero
6. WHEN calculating average APR, THE SQL Agent SHALL compute mean of offer_apr values
7. WHEN calculating average FICO, THE SQL Agent SHALL compute mean of cr_fico values
8. WHEN calculating forecast delta, THE SQL Agent SHALL subtract forecast_issuance from actual_issuance
9. WHEN calculating forecast accuracy, THE SQL Agent SHALL divide actual_issuance by forecast_issuance using NULLIF to prevent division by zero

### Requirement 8

**User Story:** As a CXO, I want to compare forecast predictions against actual results, so that I can assess forecast accuracy and adjust planning

#### Acceptance Criteria

1. WHEN a user requests forecast-vs-actual analysis, THE Planner Agent SHALL select the forecast_df table
2. THE SQL Agent SHALL retrieve both forecast_issuance and actual_issuance columns
3. THE SQL Agent SHALL calculate delta as actual minus forecast
4. THE SQL Agent SHALL calculate accuracy as actual divided by forecast using NULLIF
5. THE Chart Agent SHALL generate a grouped bar chart with forecast and actual series
6. THE Insights Agent SHALL highlight segments with largest positive and negative forecast variances

### Requirement 9

**User Story:** As a CXO, I want to view conversion funnels showing submission to approval to issuance, so that I can identify bottlenecks in the customer journey

#### Acceptance Criteria

1. WHEN a user requests funnel analysis, THE Planner Agent SHALL identify submitted, approved, and issued as the three funnel stages
2. THE SQL Agent SHALL count submissions using app_submit_d date filter
3. THE SQL Agent SHALL count approvals using apps_approved_d date filter
4. THE SQL Agent SHALL count issuances using issued_d date filter
5. THE Chart Agent SHALL generate a funnel chart with three stages in descending order
6. THE Insights Agent SHALL calculate conversion rates between each funnel stage

### Requirement 10

**User Story:** As a CXO, I want the system to cache recent query results, so that repeated questions return instantly

#### Acceptance Criteria

1. WHEN the Planner Agent generates a query plan, THE Cache Tool SHALL compute a hash key from the plan JSON
2. THE Cache Tool SHALL check for cached results matching the hash key
3. WHEN cached results exist and are less than 10 minutes old, THE API Layer SHALL return cached results without executing SQL
4. WHEN cached results do not exist or are expired, THE SQL Agent SHALL execute the query
5. THE Cache Tool SHALL store query results with a 10-minute TTL after successful execution

### Requirement 11

**User Story:** As a CXO, I want to ask questions about metric definitions and schema, so that I can understand what data means without consulting documentation

#### Acceptance Criteria

1. WHEN a user asks "what is funding rate", THE Router Agent SHALL classify the intent as explain metric
2. THE Memory Agent SHALL retrieve the definition from the RAG Tool using semantic search
3. THE RAG Tool SHALL query the Chroma vector database with the user question
4. THE RAG Tool SHALL return the top matching definition from the indexed glossary
5. THE Chat UI SHALL display the definition as a text response without chart visualization

### Requirement 12

**User Story:** As a system administrator, I want all database queries to be read-only and parameterized, so that the system is protected from SQL injection and data modification

#### Acceptance Criteria

1. THE SQL Tool SHALL open SQLite database connections with read-only flag enabled
2. THE SQL Agent SHALL select queries from a whitelist of predefined templates
3. THE SQL Agent SHALL bind user parameters using SQLite parameter substitution
4. THE Guardrail Agent SHALL reject any query containing semicolons or multiple SQL statements
5. THE Guardrail Agent SHALL reject any query containing INSERT, UPDATE, DELETE, DROP, or ALTER keywords

### Requirement 13

**User Story:** As a system administrator, I want to limit query time windows to prevent performance degradation, so that the system remains responsive

#### Acceptance Criteria

1. WHEN a user requests data without specifying a time limit, THE Guardrail Agent SHALL enforce a maximum window of 1 year
2. WHEN a user explicitly requests data exceeding 1 year, THE Guardrail Agent SHALL allow the query
3. THE Guardrail Agent SHALL enforce a maximum result row limit of 10,000 rows
4. WHEN query results exceed the row limit, THE SQL Agent SHALL return the first 10,000 rows with a warning message
5. THE Guardrail Agent SHALL log all queries exceeding performance thresholds for monitoring

### Requirement 14

**User Story:** As a CXO, I want to export chart data as CSV or PNG files, so that I can include insights in presentations and reports

#### Acceptance Criteria

1. WHEN a user clicks the export CSV button, THE Chat UI SHALL download the query result dataframe as a CSV file
2. WHEN a user clicks the export PNG button, THE Chat UI SHALL render the Plotly chart as a PNG image and download it
3. THE API Layer SHALL provide an /export endpoint accepting the query plan hash
4. THE API Layer SHALL retrieve the cached dataframe for the query plan
5. THE API Layer SHALL return the dataframe in CSV format with appropriate headers

### Requirement 15

**User Story:** As a CXO, I want the system to suggest follow-up questions based on my current query, so that I can explore related insights efficiently

#### Acceptance Criteria

1. WHEN the API Layer completes a query response, THE API Layer SHALL generate three follow-up question suggestions
2. THE suggestions SHALL relate to the current query intent and results
3. THE Chat UI SHALL display follow-up suggestions as clickable chips below the response
4. WHEN a user clicks a suggestion chip, THE Chat UI SHALL submit the suggested question as a new query
5. THE API Layer SHALL provide a /suggest endpoint returning contextual follow-up questions

### Requirement 16

**User Story:** As a developer, I want structured logging of all query executions, so that I can monitor system performance and debug issues

#### Acceptance Criteria

1. WHEN the API Layer receives a chat request, THE API Layer SHALL log the user text with timestamp and session ID
2. WHEN the Planner Agent generates a query plan, THE API Layer SHALL log the plan JSON
3. WHEN the SQL Agent executes a query, THE API Layer SHALL log the SQL text and parameter values
4. WHEN the SQL Agent completes execution, THE API Layer SHALL log the row count and execution latency
5. THE API Layer SHALL log all errors with stack traces and context information

### Requirement 17

**User Story:** As a CXO, I want the system to sort FICO bands in logical order, so that charts display credit score ranges from lowest to highest

#### Acceptance Criteria

1. WHEN the Chart Agent generates a chart with cr_fico_band on an axis, THE Chart Agent SHALL sort categories in the order: <640, 640-699, 700-759, 760+
2. THE Planner Agent SHALL define the FICO band sort order in the query plan
3. THE SQL Agent SHALL apply ORDER BY clause using CASE statement to enforce FICO band ordering
4. THE Chart Agent SHALL apply categorical axis ordering in the Plotly specification
5. THE Chat UI SHALL render charts with FICO bands in the specified order

### Requirement 18

**User Story:** As a CXO, I want to toggle between light and dark themes, so that I can use the interface comfortably in different lighting conditions

#### Acceptance Criteria

1. WHEN a user clicks the theme toggle button, THE Chat UI SHALL switch between light and dark color schemes
2. THE Chat UI SHALL persist the theme preference in browser local storage
3. THE Chat UI SHALL apply the saved theme preference on page load
4. THE Chart Agent SHALL generate Plotly specifications with theme-aware background colors
5. THE Chat UI SHALL update chart colors dynamically when theme changes

### Requirement 19

**User Story:** As a CXO, I want to see typing indicators while the system processes my query, so that I know the system is working

#### Acceptance Criteria

1. WHEN the API Layer begins processing a query, THE Chat UI SHALL display an animated typing indicator
2. THE typing indicator SHALL show three animated dots in the assistant message area
3. WHEN the API Layer streams the first response token, THE Chat UI SHALL replace the typing indicator with the response text
4. THE Chat UI SHALL maintain the typing indicator for a maximum of 5 seconds before showing a timeout message
5. WHEN the query completes, THE Chat UI SHALL remove the typing indicator

### Requirement 20

**User Story:** As a CXO, I want quick access to common time period filters, so that I can analyze standard reporting periods with one click

#### Acceptance Criteria

1. THE Chat UI SHALL display filter chips for "Last 7 days", "Last full week", "Last full month", and "Last 3 full months"
2. WHEN a user clicks a time period chip, THE Chat UI SHALL append the time period to the current query or create a new query
3. THE Chat UI SHALL display segment filter dropdowns for channel, grade, prod_type, repeat_type, term, and cr_fico_band
4. WHEN a user selects a segment filter, THE Chat UI SHALL include the segment in the next query
5. THE Chat UI SHALL persist selected filters across multiple queries until explicitly cleared
