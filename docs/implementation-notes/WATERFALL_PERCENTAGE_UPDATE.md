# Waterfall Chart Update: Percentage-Based Display

## Change Summary
Updated the forecast gap analysis waterfall chart to display **contribution percentages** as the primary metric instead of absolute dollar amounts, making it easier to understand the relative impact of each segment.

## What Changed

### Before
- Y-axis showed absolute dollar amounts (e.g., -$124K, +$122K)
- Started at forecast total, ended at actual total
- Hard to compare relative impact of different segments

### After
- Y-axis shows **contribution percentages** (e.g., +514.7%, -507.7%)
- Starts at 0%, ends at 100%
- Absolute amounts shown in parentheses for context
- Y-axis labeled "Contribution to Total Variance (%)"
- Y-axis tick labels have "%" suffix

## Example Output

### Chart Structure
```
Start (0%)
  ↓ +514.7% (D2LC channel: -$124K)
  ↓ -507.7% (OMB channel: +$122K)
  ↓ +292.8% (P2 grade: -$71K)
  ↓ -261.4% (P3 grade: +$63K)
  ...
Total (100%)
```

### Text Labels
Each bar shows:
- **Primary**: Contribution percentage (e.g., `+514.7%`)
- **Secondary**: Absolute amount (e.g., `(-$124)`)

Format: `+514.7%<br>(-124)`

### Interpretation
- **Positive %**: Segment performed worse than forecast (driving the miss)
- **Negative %**: Segment performed better than forecast (offsetting the miss)
- **Large absolute %**: Segment has outsized impact on total variance

Example: `+514.7%` means D2LC's underperformance accounts for 514.7% of the total variance (which is negative, so this segment is making it worse).

## Technical Details

### File Modified
`topup-backend/tools/chart_tool.py` - `_build_waterfall_chart()` function

### Key Changes

1. **Y-values**: Changed from `delta` to `contribution_pct`
   ```python
   # Before
   y_values = [forecast] + segments_df['delta'].tolist() + [actual]
   
   # After
   y_values = [0] + segments_df['contribution_pct'].tolist() + [100]
   ```

2. **Text Labels**: Show percentage + absolute value
   ```python
   # Before
   text_labels = [f"{v:,.0f}" for v in y_values]
   
   # After
   text_labels.append(f"{row['contribution_pct']:+.1f}%<br>({row['delta']:+,.0f})")
   ```

3. **Y-axis Configuration**
   ```python
   layout["yaxis"]["title"] = "Contribution to Total Variance (%)"
   layout["yaxis"]["ticksuffix"] = "%"
   ```

4. **Measure Types**: Changed end point from 'absolute' to 'total'
   ```python
   measures = ['absolute'] + ['relative'] * len(segments_df) + ['total']
   ```

## Benefits

1. **Easier Comparison**: Percentages make it easy to see which segments have the biggest impact
2. **Intuitive**: 100% total makes sense conceptually
3. **Context Preserved**: Absolute amounts still shown for reference
4. **Better Storytelling**: "D2LC accounts for 515% of the variance" is more impactful than "$124K"

## Test Results

✅ All tests passing
✅ Chart displays percentages correctly
✅ Absolute values shown in parentheses
✅ Y-axis properly labeled with % suffix
✅ Both light and dark themes working

## Example Use Case

**Query**: "Where are we seeing the largest gap between forecast and actual for issuance?"

**Response**: Waterfall chart showing:
- D2LC channel: **+514.7%** (-$124K) - Biggest driver of the miss
- OMB channel: **-507.7%** (+$122K) - Offsetting the miss
- P2 grade: **+292.8%** (-$71K) - Contributing to the miss
- P3 grade: **-261.4%** (+$63K) - Offsetting the miss

**Insight**: "The forecast miss is primarily driven by D2LC channel underperforming by $124K, which accounts for 515% of the total variance. This is partially offset by OMB channel overperforming by $122K."

## Status
✅ Implementation complete
✅ Backend auto-reloaded
✅ Ready for testing in UI

---

**Date**: 2024-11-14
**Feature**: Forecast Gap Analysis - Percentage-Based Waterfall Chart
