# Planner Fix: Forecast Gap Analysis Intent Recognition

## Problem
The query "where are we seeing the largest gap between forecast and actual performance for issuance?" was being classified as `forecast_vs_actual` instead of `forecast_gap_analysis`.

## Root Cause
The planner's intent hint detection was too broad - it caught any query containing "forecast" and routed it to `forecast_vs_actual`, before checking for gap-specific keywords.

## Solution
Updated `topup-backend/agents/planner.py` to:

### 1. Added Gap-Specific Keywords Detection (Line ~648)
```python
# Check for forecast gap analysis BEFORE general forecast queries
elif any(keyword in content.lower() for keyword in [
    'forecast gap', 
    'gap analysis', 
    'variance decomposition', 
    'driving the forecast', 
    'largest gap', 
    'biggest gap', 
    'forecast miss', 
    'forecast variance'
]):
    plan_hints['intent'] = 'forecast_gap_analysis'
    plan_hints['chart'] = 'waterfall'
elif 'forecast' in content.lower() or 'vs actual' in content.lower():
    plan_hints['intent'] = 'forecast_vs_actual'
```

**Key Change**: Gap detection now happens BEFORE the general forecast check, ensuring gap queries are caught first.

### 2. Updated System Prompt
Added clear distinction between the two forecast intents:

```
**Intent Classification - Forecast Queries:**
IMPORTANT: Distinguish between two types of forecast queries:

1. **forecast_vs_actual** - Comparing forecast to actual over time or by segment
   - Keywords: "forecast vs actual", "compare forecast", "forecast performance"
   - Shows: Time series or segment comparison of forecast vs actual values
   - Chart: grouped_bar

2. **forecast_gap_analysis** - Analyzing WHY there's a gap (variance decomposition)
   - Keywords: "forecast gap", "gap analysis", "largest gap", "biggest gap", 
     "driving the forecast", "forecast miss", "forecast variance", "variance decomposition"
   - Shows: Which segments contribute most to the overall forecast variance
   - Chart: waterfall
   - Example: "Where are we seeing the largest gap?" → forecast_gap_analysis
```

### 3. Updated Table Selection Rules
```python
**Table Selection Rules:**
- forecast_vs_actual intent → forecast_df
- forecast_gap_analysis intent → forecast_df  # ADDED
- All other intents → cps_tb
```

### 4. Updated Chart Type Mapping
```python
chart_mapping = {
    "trend": "line",
    "variance": "line",
    "forecast_vs_actual": "grouped_bar",
    "forecast_gap_analysis": "waterfall",  # ADDED
    "funnel": "funnel",
    "distribution": "pie",
    "relationship": "scatter",
    "multi_metric": "line",
    "explain": "line"
}
```

### 5. Updated Table Selection Logic
```python
if plan.intent in ["forecast_vs_actual", "forecast_gap_analysis"]:  # ADDED forecast_gap_analysis
    plan.table = "forecast_df"
    plan.date_col = "date"
```

## Test Queries

### Should Trigger `forecast_gap_analysis`:
✅ "where are we seeing the largest gap between forecast and actual performance for issuance?"
✅ "show me the forecast gap analysis for submits"
✅ "what's driving the forecast miss for approvals?"
✅ "forecast variance decomposition for issuance"
✅ "where is the biggest gap in our forecast?"
✅ "gap analysis for issuance this month"

### Should Trigger `forecast_vs_actual`:
✅ "compare forecast vs actual for issuance"
✅ "show me forecast and actual performance"
✅ "how does actual compare to forecast?"

## Expected Behavior

When user asks: **"where are we seeing the largest gap between forecast and actual performance for issuance?"**

The system will now:
1. ✅ Classify as `forecast_gap_analysis` (not `forecast_vs_actual`)
2. ✅ Use `forecast_df` table
3. ✅ Execute `forecast_variance_decomposition.sql` template
4. ✅ Generate waterfall chart showing variance by segment
5. ✅ Display which channels, grades, product types, etc. contribute most to the gap

## Files Modified
- `topup-backend/agents/planner.py` - Updated intent detection and system prompt

## Status
✅ Changes deployed
✅ Backend server auto-reloaded with new code
✅ Ready for testing in the UI

## Next Steps
Test in the UI with the query:
```
where are we seeing the largest gap between forecast and actual performance for issuance?
```

Expected result: Waterfall chart showing variance decomposition by segment.
