# Conversation Routing Fix

## Issue Fixed

**Problem**: The explanation agent was interfering with conversational follow-ups. When users asked follow-up questions like "What about last quarter?", the router was classifying them as "explain" intent, which routed them to the explanation agent instead of using conversation context in the normal pipeline.

**Impact**:
- Follow-up questions didn't use conversation context
- No charts were generated for follow-ups
- Users got explanations instead of data visualizations
- Conversation memory wasn't being utilized

---

## Root Causes

### 1. Missing Conversation History in Orchestrator

The conversation_history parameter was never added to the orchestrator's GraphState or passed through the pipeline.

**Files Affected**:
- `topup-backend/agents/__init__.py` - GraphState, router_node, planner_node, run_query
- `topup-backend/app/main.py` - chat endpoint

### 2. Overly Broad "Explain" Intent Classification

The router was classifying conversational follow-ups as "explain" because they contained words like "what" or "about".

**File Affected**:
- `topup-backend/agents/router.py` - System prompt

---

## Solutions Implemented

### 1. ✅ Added Conversation History to Pipeline

**GraphState Update** (`agents/__init__.py`):
```python
class GraphState(TypedDict):
    user_query: str
    conversation_history: Optional[List[Dict]]  # NEW
    intent: Optional[str]
    plan: Optional[Plan]
    # ... other fields
```

**Router Node Update**:
```python
def router_node(state: GraphState) -> GraphState:
    intent = router.classify(
        state["user_query"], 
        state.get("conversation_history")  # Pass history
    )
    state["intent"] = intent
    return state
```

**Planner Node Update**:
```python
def planner_node(state: GraphState) -> GraphState:
    plan = planner.make_plan(
        state["user_query"], 
        state["intent"],
        state.get("conversation_history")  # Pass history
    )
    state["plan"] = plan
    return state
```

**run_query Function Update**:
```python
def run_query(
    user_query: str,
    conversation_history: Optional[List[Dict]] = None,  # NEW parameter
    max_retries: int = 2
) -> Dict[str, Any]:
    initial_state: GraphState = {
        "user_query": user_query,
        "conversation_history": conversation_history or [],  # Include in state
        # ... other fields
    }
```

**API Endpoint Update** (`app/main.py`):
```python
@app.get("/chat")
async def chat_sse(
    message: str,
    history: Optional[str] = None,  # NEW parameter
    # ... other parameters
):
    # Parse conversation history
    conversation_history = []
    if history:
        try:
            conversation_history = json.loads(history)
        except json.JSONDecodeError:
            conversation_history = []
    
    # Pass to run_query
    result = await loop.run_in_executor(
        None, 
        lambda: run_query(message, conversation_history)
    )
```

### 2. ✅ Refined "Explain" Intent Classification

**Updated Router System Prompt** (`agents/router.py`):

Added explicit counter-examples:
```
8. **explain**: User wants ONLY definition or explanation of a metric/term (NO data requested)
   - Examples: "What is funding rate?", "Define approval rate", "Why did X happen?"
   - Counter-examples (NOT explain): 
     * "Show me funding rate" → use trend
     * "What is the current approval rate?" → use trend/distribution
     * "What about last quarter?" → use trend (conversational follow-up)
     * "Break that down by channel" → use distribution (conversational follow-up)
   - IMPORTANT: Conversational follow-ups like "what about...", "show me that...", 
     "break it down..." are NOT explain queries
```

Updated classification rules:
```
**Classification Rules:**
- If query is a conversational follow-up (what about, show that, break it down) 
  → use appropriate analytical intent based on context
- If query asks "why did", "what caused", "reason for" about a specific event/trend 
  → explain
- If query asks "what is", "define", "explain" WITHOUT asking for data 
  → explain

Do NOT use "explain" for:
- Conversational follow-ups: "What about last quarter?" → trend
- Data requests: "Show me funding rate" → trend
- Breakdowns: "Break that down by channel" → distribution
```

---

## Test Results

### Automated Test (`test_conversation_awareness.py`)

```
✅ First query: "Show me issuances last month"
   - Intent: trend ✓
   - Metric: issued_amnt ✓
   - Has chart: True ✓

✅ Follow-up: "What about last quarter?"
   - Intent: trend ✓ (NOT explain)
   - Metric: issued_amnt ✓ (inferred from context)
   - Has chart: True ✓

✅ Follow-up: "Break that down by channel"
   - Intent: distribution ✓ (NOT explain)
   - Metric: issued_amnt ✓ (kept from context)
   - Has chart: True ✓
```

**Result**: 🎉 ALL TESTS PASSED

---

## Verification Checklist

- [x] Conversation history added to GraphState
- [x] Router receives conversation history
- [x] Planner receives conversation history
- [x] run_query accepts conversation_history parameter
- [x] API endpoint accepts history parameter
- [x] API endpoint parses and passes history
- [x] Router system prompt updated with counter-examples
- [x] Follow-ups classified correctly (NOT as explain)
- [x] Follow-ups use conversation context
- [x] Follow-ups generate charts
- [x] Context inference working
- [x] All automated tests pass

---

## Example Conversations Now Working

### Example 1: Time Window Follow-ups
```
User: "Show me issuances last month"
Assistant: [Shows chart for last month]

User: "What about last quarter?"  ← Correctly uses trend intent
Assistant: [Shows chart for last quarter with same metric]

User: "And last year?"  ← Correctly uses trend intent
Assistant: [Shows chart for last year with same metric]
```

### Example 2: Segmentation Follow-ups
```
User: "Show me approvals last month"
Assistant: [Shows approval chart]

User: "Break that down by channel"  ← Correctly uses distribution intent
Assistant: [Shows approvals by channel]

User: "Now by grade"  ← Correctly uses distribution intent
Assistant: [Shows approvals by grade]
```

### Example 3: Genuine Explanations Still Work
```
User: "Show me issuances over time"
Assistant: [Shows chart with drop in March]

User: "Why did issuances drop in March?"  ← Correctly uses explain intent
Assistant: [Provides business explanation without chart]
```

---

## Files Modified

### Backend
1. **`topup-backend/agents/__init__.py`**
   - Added conversation_history to GraphState
   - Updated router_node to pass history
   - Updated planner_node to pass history
   - Updated run_query to accept and use history

2. **`topup-backend/agents/router.py`**
   - Updated system prompt with counter-examples
   - Clarified when to use "explain" intent
   - Added explicit rules for conversational follow-ups

3. **`topup-backend/app/main.py`**
   - Added history parameter to chat endpoint
   - Parse conversation history from JSON
   - Pass history to run_query

### Tests Created
1. **`topup-backend/test_conversation_awareness.py`**
   - Tests conversational follow-ups
   - Verifies correct intent classification
   - Confirms context inference working
   - Ensures charts are generated

---

## Impact

### User Experience
- ✅ Natural multi-turn conversations work correctly
- ✅ Follow-ups use context from previous queries
- ✅ Charts generated for all data queries
- ✅ Explanation agent only used for genuine "why" questions

### Performance
- ✅ No performance degradation
- ✅ Conversation history limited to last 10 messages
- ✅ History truncated to 200 chars per message

### Reliability
- ✅ Backward compatible (history parameter optional)
- ✅ Graceful handling of invalid history JSON
- ✅ Fallback to empty history if parsing fails

---

## Status: ✅ COMPLETE

The conversation routing issue is fully resolved. The system now:

1. **Correctly routes conversational follow-ups** through the normal pipeline with context
2. **Uses conversation history** for intent classification and planning
3. **Reserves "explain" intent** for genuine definition/explanation queries
4. **Generates charts and insights** for all data queries
5. **Maintains backward compatibility** with existing functionality

**Ready for production use.**
