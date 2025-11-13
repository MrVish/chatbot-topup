# Chart Traces Fix

## Issue Fixed

**Problem**: Charts were showing multiple unnecessary lines. For a simple query like "Show me issuances last month", the chart displayed 3 lines:
1. Week Start (metadata column)
2. Metric Value (the actual data)
3. Record Count (metadata column)

This made charts confusing and cluttered with irrelevant information.

**Visual Impact**:
- Legend showed "Week Start", "Metric Value", "Record Count"
- Three lines plotted on the chart
- Users couldn't easily see the actual trend
- Metadata columns distracted from the main metric

---

## Root Cause

In `topup-backend/tools/chart_tool.py`, the `_build_trend_chart` function was plotting ALL columns except the first one:

```python
# Get value columns (all except first)
value_cols = df.columns[1:].tolist()
```

The SQL query returns these columns:
- `week` (time dimension)
- `week_start` (helper column for display)
- `metric_value` (the actual metric)
- `record_count` (metadata)

The chart tool was treating `week_start`, `metric_value`, AND `record_count` as data series to plot.

---

## Solution

Updated the chart tool to filter out metadata/helper columns before plotting:

```python
# Identify time column (first column is typically the time dimension)
time_col = df.columns[0]

# Get value columns - filter out metadata/helper columns
# For trend charts, we want to plot the actual metric, not helper columns
all_cols = df.columns[1:].tolist()

# Filter out known metadata columns that shouldn't be plotted
metadata_cols = ['week_start', 'month_start', 'quarter_start', 'year_start', 'record_count']
value_cols = [col for col in all_cols if col not in metadata_cols]

# If no value columns found after filtering, default to metric_value
if not value_cols:
    if 'metric_value' in all_cols:
        value_cols = ['metric_value']
    else:
        value_cols = [all_cols[0]] if all_cols else []
```

**Key Changes**:
1. Added explicit list of metadata columns to filter out
2. Only plot columns that represent actual metrics
3. Fallback to `metric_value` if no other columns found
4. Preserves multi-metric functionality (multiple actual metrics still plotted)

---

## Test Results

### Before Fix
```
Query: "Show me issuances last month"
Chart traces: 3
- Week Start (❌ metadata)
- Metric Value (✓ actual data)
- Record Count (❌ metadata)
```

### After Fix
```
Query: "Show me issuances last month"
Chart traces: 1
- Metric Value (✓ actual data only)
```

### Multi-Metric Still Works
```
Query: "Show app submits vs approvals"
Chart traces: 2
- App Submits ($) (✓ actual metric)
- Approvals ($) (✓ actual metric)
```

---

## Automated Test

Created `test_chart_traces.py` to verify:

```bash
python topup-backend/test_chart_traces.py
```

**Results**:
```
✅ Single metric queries show 1 trace
✅ Metadata columns filtered out
✅ Multi-metric queries show multiple traces
```

---

## Files Modified

### Backend
1. **`topup-backend/tools/chart_tool.py`**
   - Updated `_build_trend_chart` function
   - Added metadata column filtering
   - Preserved multi-metric functionality

### Tests Created
1. **`topup-backend/test_chart_traces.py`**
   - Tests single metric queries
   - Tests multi-metric queries
   - Verifies correct number of traces

---

## Impact

### User Experience
- ✅ Charts are cleaner and easier to read
- ✅ Only relevant data is displayed
- ✅ Legend shows only actual metrics
- ✅ No confusion from metadata columns

### Chart Types Affected
- ✅ Trend charts (line/area)
- ✅ Time series analysis
- ✅ Single metric queries
- ✅ Multi-metric comparisons (still work correctly)

### Backward Compatibility
- ✅ No breaking changes
- ✅ Multi-metric charts still show multiple lines
- ✅ All existing queries work correctly

---

## Metadata Columns Filtered

The following columns are now filtered out from charts:
- `week_start` - Helper column for week display
- `month_start` - Helper column for month display
- `quarter_start` - Helper column for quarter display
- `year_start` - Helper column for year display
- `record_count` - Row count metadata

These columns are still in the data, just not plotted on the chart.

---

## Verification Checklist

- [x] Single metric queries show 1 trace
- [x] Metadata columns filtered out
- [x] Multi-metric queries show multiple traces
- [x] Chart legends are clean
- [x] No breaking changes
- [x] All automated tests pass
- [x] Visual inspection confirms fix

---

## Status: ✅ COMPLETE

The chart traces issue is fully resolved. Charts now display only the relevant metric data, making them cleaner and easier to understand.

**Ready for production use.**
