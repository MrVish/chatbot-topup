# Phase 1: Conversation Memory - Implementation Guide

## Status: 🚧 IN PROGRESS

This document tracks the implementation of conversation awareness.

## Changes Required

### 1. Backend: Chat Endpoint (main.py)
**Status**: ⏳ TODO

**Current**: GET endpoint with query parameters
**Change**: Add `history` parameter (JSON string of last 5 messages)

```python
@app.get("/chat")
async def chat_sse(
    message: str,
    history: Optional[str] = None,  # NEW: JSON array of messages
    # ... other parameters
):
    # Parse history
    conversation_history = []
    if history:
        try:
            conversation_history = json.loads(history)
        except:
            conversation_history = []
    
    # Pass to run_query
    result = await loop.run_in_executor(
        None, 
        run_query, 
        message, 
        conversation_history  # NEW parameter
    )
```

### 2. Backend: Orchestrator (agents/__init__.py)
**Status**: ⏳ TODO

**Change**: Accept and pass conversation history

```python
def run_query(user_query: str, conversation_history: List[Dict] = None) -> Dict:
    """
    Execute query with conversation context.
    
    Args:
        user_query: Current user query
        conversation_history: List of previous messages
            Format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    """
    # Add history to state
    state = {
        "user_query": user_query,
        "conversation_history": conversation_history or [],
        # ... rest of state
    }
```

### 3. Backend: Router Agent (agents/router.py)
**Status**: ⏳ TODO

**Change**: Use conversation history for context

```python
def classify(user_query: str, conversation_history: List[Dict] = None) -> str:
    """
    Classify intent with conversation context.
    """
    # Build context-aware prompt
    context_prompt = ""
    if conversation_history:
        # Get last 2-3 messages for context
        recent = conversation_history[-4:]  # Last 2 exchanges
        context_prompt = "\n\nConversation History:\n"
        for msg in recent:
            context_prompt += f"{msg['role']}: {msg['content']}\n"
    
    user_message = f"""{context_prompt}

Current User Query: {user_query}

Classify the intent considering the conversation context."""
```

### 4. Backend: Planner Agent (agents/planner.py)
**Status**: ⏳ TODO

**Change**: Use history to infer missing parameters

```python
def make_plan(
    user_query: str, 
    intent: str,
    conversation_history: List[Dict] = None
) -> Plan:
    """
    Generate plan with conversation context.
    """
    # Extract context from history
    context_info = ""
    if conversation_history:
        # Look for previous metrics, time windows, segments
        last_plan = _extract_last_plan(conversation_history)
        if last_plan:
            context_info = f"""

Previous Query Context:
- Metric: {last_plan.get('metric')}
- Time Window: {last_plan.get('window')}
- Segments: {last_plan.get('segments')}

Use this context to infer missing parameters in the current query."""
    
    user_message = f"""{context_info}

User Query: {user_query}
Classified Intent: {intent}

Generate a complete query plan."""
```

### 5. Frontend: Chat Store (hooks/useChatStore.ts)
**Status**: ⏳ TODO

**Change**: Track conversation history

```typescript
interface ChatStore {
  messages: Message[];
  conversationHistory: Array<{role: string, content: string, plan?: any}>;
  
  // New action
  getRecentHistory: () => Array<{role: string, content: string}>;
}

// Implementation
getRecentHistory: () => {
  const messages = get().messages;
  // Get last 5 messages (10 total with user+assistant pairs)
  return messages.slice(-10).map(msg => ({
    role: msg.role,
    content: msg.content.text || JSON.stringify(msg.content.card?.insight)
  }));
}
```

### 6. Frontend: Chat Page (app/page.tsx)
**Status**: ⏳ TODO

**Change**: Send history with each request

```typescript
const send = React.useCallback((message: string) => {
  // Get recent history
  const history = getRecentHistory();
  
  // Build query parameters
  const params = new URLSearchParams({
    message,
    history: JSON.stringify(history),  // NEW
    // ... other params
  });
  
  const url = `${apiUrl}/chat?${params.toString()}`;
  const es = new EventSource(url);
  // ...
}, [getRecentHistory]);
```

## Testing Plan

### Test Case 1: Context Retention
```
User: "Show issuances last month"
Assistant: [Shows chart]
User: "What about last quarter?"  ← Should infer metric=issuances
Expected: Chart for issuances last quarter
```

### Test Case 2: Pronoun Resolution
```
User: "Show app submits vs approvals"
Assistant: [Shows comparison]
User: "Break that down by channel"  ← Should infer same metrics
Expected: Multi-metric chart segmented by channel
```

### Test Case 3: Follow-up Questions
```
User: "How are we doing this quarter?"
Assistant: [Shows multi-metric]
User: "Show me just approvals"  ← Should keep same time window
Expected: Approvals chart for QTD
```

## Implementation Order

1. ✅ Create this implementation guide
2. ⏳ Update backend orchestrator to accept history
3. ⏳ Update router agent with context awareness
4. ⏳ Update planner agent with context inference
5. ⏳ Update chat endpoint to accept history parameter
6. ⏳ Update frontend to send history
7. ⏳ Test conversation flows
8. ✅ Move to Phase 2

## Notes

- Keep history to last 5 messages (10 total with pairs) to avoid token overflow
- Store full plan in history for better context
- Consider adding "Clear conversation" button in UI
- Log conversation context for debugging

## Next: Phase 2

Once Phase 1 is complete, we'll implement LLM SQL generation fallback.
