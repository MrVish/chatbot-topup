# Conversation Enhancement Implementation Plan

## Overview
Transform the TopUp CXO Assistant from a stateless Q&A system into a conversational, context-aware analytics assistant.

## Phase 1: Conversation Memory ✅ (Start Here)

### 1.1 Update Chat Endpoint
- **File**: `topup-backend/app/main.py`
- **Changes**:
  - Accept conversation history in request
  - Store last N messages in session
  - Pass history to router and planner

### 1.2 Update Router Agent
- **File**: `topup-backend/agents/router.py`
- **Changes**:
  - Accept conversation history parameter
  - Use history to understand context (e.g., "show me last month" after "what about approvals?")
  - Resolve pronouns and references

### 1.3 Update Planner Agent
- **File**: `topup-backend/agents/planner.py`
- **Changes**:
  - Use conversation history to infer missing parameters
  - Example: "What about last quarter?" → infer metric from previous query

### 1.4 Frontend Changes
- **File**: `topup-frontend/app/page.tsx`
- **Changes**:
  - Send last 3-5 messages with each request
  - Format: `[{role: "user", content: "..."}, {role: "assistant", content: "..."}]`

## Phase 2: LLM SQL Generation Fallback 🔄 (Next)

### 2.1 Create SQL Generator Agent
- **File**: `topup-backend/agents/sql_generator.py` (NEW)
- **Purpose**: Generate SQL when no template matches
- **Features**:
  - Text-to-SQL using GPT-4
  - Schema-aware generation
  - Safety validation (read-only, no dangerous operations)
  - Automatic chart type inference

### 2.2 Update Orchestrator
- **File**: `topup-backend/agents/__init__.py`
- **Changes**:
  - Add fallback path: router → sql_generator → guardrail → execute
  - New intent: "custom_query" for non-template queries

### 2.3 Safety Layer
- **File**: `topup-backend/agents/guardrail.py`
- **Changes**:
  - Enhanced SQL validation for LLM-generated queries
  - Whitelist allowed tables and columns
  - Detect and block dangerous patterns

## Phase 3: Conversational Follow-ups 🎯 (Advanced)

### 3.1 Intent: "explain"
- **Purpose**: Answer "why" questions about previous insights
- **Examples**:
  - "Why did issuances drop?"
  - "What caused the spike in October?"
  - "Explain the approval bottleneck"

### 3.2 Create Explanation Agent
- **File**: `topup-backend/agents/explanation_agent.py` (NEW)
- **Features**:
  - Access to previous query results
  - Drill-down queries (segment analysis)
  - Root cause analysis using LLM
  - Reference specific data points from charts

### 3.3 Intent: "drill_down"
- **Purpose**: Explore specific segments or periods
- **Examples**:
  - "Show me Email channel specifically"
  - "Break down by grade"
  - "What happened in October?"

## Implementation Priority

### Week 1: Conversation Memory
1. ✅ Update chat endpoint to accept history
2. ✅ Modify router to use context
3. ✅ Update planner with history awareness
4. ✅ Frontend: Send conversation history

### Week 2: LLM SQL Fallback
1. Create SQL generator agent
2. Add schema documentation for LLM
3. Implement safety validation
4. Test with edge cases

### Week 3: Conversational Follow-ups
1. Add "explain" intent
2. Create explanation agent
3. Implement drill-down queries
4. Add conversation state management

## Technical Considerations

### Conversation State
```python
# Store in session or cache
conversation_state = {
    "session_id": "uuid",
    "messages": [
        {"role": "user", "content": "Show issuances last month"},
        {"role": "assistant", "content": "...", "plan": {...}, "data": {...}}
    ],
    "last_query": {
        "plan": Plan(...),
        "results": DataFrame(...),
        "insights": Insight(...)
    }
}
```

### LLM SQL Generation Prompt
```python
SYSTEM_PROMPT = """You are a SQL expert for a marketing analytics database.

Schema:
- cps_tb: Customer acquisition data (app_submit_d, apps_approved_d, issued_d, ...)
- forecast_df: Forecast vs actual data

Generate SAFE, READ-ONLY SQL queries. Use:
- SELECT only (no INSERT/UPDATE/DELETE)
- Proper date filtering
- Aggregations when appropriate
- SQLite syntax

Return JSON: {"sql": "SELECT ...", "chart_type": "line", "metric": "..."}
"""
```

### Safety Validation
```python
def validate_llm_sql(sql: str) -> bool:
    # Check for dangerous keywords
    dangerous = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE"]
    if any(word in sql.upper() for word in dangerous):
        return False
    
    # Check for allowed tables only
    allowed_tables = ["cps_tb", "forecast_df"]
    # ... validation logic
    
    return True
```

## Benefits

### Conversation Awareness
- ✅ Natural follow-up questions
- ✅ Context retention across queries
- ✅ Pronoun resolution ("show me that by channel")
- ✅ Better UX - feels like talking to an analyst

### LLM SQL Fallback
- ✅ Handle any question, not just templates
- ✅ Explore data freely
- ✅ Ad-hoc analysis
- ✅ Future-proof (no need to add templates)

### Conversational Follow-ups
- ✅ Deep dive into insights
- ✅ Root cause analysis
- ✅ Interactive exploration
- ✅ Executive-friendly explanations

## Risks & Mitigations

### Risk: LLM generates bad SQL
**Mitigation**: 
- Strict validation layer
- Test suite with edge cases
- Fallback to error message
- Log all generated SQL for review

### Risk: Performance with conversation history
**Mitigation**:
- Limit history to last 5 messages
- Summarize old messages
- Cache conversation state

### Risk: Context confusion
**Mitigation**:
- Clear conversation reset button
- Show what context is being used
- Allow manual parameter override

## Next Steps

1. **Start with Phase 1** - Conversation memory (lowest risk, high value)
2. **Prototype Phase 2** - Test LLM SQL generation in sandbox
3. **Design Phase 3** - Plan conversation state management

Would you like me to start implementing Phase 1 now?
