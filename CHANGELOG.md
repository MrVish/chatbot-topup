# Changelog

All notable changes to the Topup CXO Assistant project.

## [Unreleased] - 2024-11-14

### Added - Forecast Gap Analysis Feature

#### New SQL Template
- **forecast_variance_decomposition.sql**: Comprehensive variance decomposition template
  - Breaks down forecast variance by all segment dimensions (channel, grade, prod_type, repeat_type, term)
  - Shows both absolute variance and percentage contribution
  - Supports all three metrics: submits, approvals, issuance
  - Respects segment filters for focused analysis

#### New Chart Type
- **Waterfall Chart**: Visual variance decomposition
  - Displays contribution percentages as primary metric
  - Shows absolute amounts in parentheses for context
  - Color-coded: green for positive variance, red for negative
  - Y-axis labeled "Contribution to Total Variance (%)"
  - Starts at 0%, ends at 100%

#### Schema Updates
- Added `forecast_gap_analysis` intent to Plan schema
- Added `waterfall` chart type to Plan schema
- Updated SQL tool to handle forecast gap analysis intent
- Updated chart tool with waterfall chart builder

#### Planner Enhancements
- Added smart intent detection for gap-related queries
- Keywords: "forecast gap", "gap analysis", "largest gap", "biggest gap", "driving the forecast", "forecast miss", "forecast variance"
- Clear distinction between `forecast_vs_actual` (comparison) and `forecast_gap_analysis` (decomposition)
- Updated system prompt with detailed intent classification rules

### Changed

#### Planner Intent Detection
- Reordered intent detection to check gap keywords BEFORE general forecast keywords
- Prevents "gap" queries from being misclassified as `forecast_vs_actual`
- Updated table selection logic to include `forecast_gap_analysis`
- Updated chart type mapping to use waterfall for gap analysis

#### Waterfall Chart Display
- Changed from absolute dollar amounts to percentage-based display
- Primary value: contribution percentage (e.g., +514.7%)
- Secondary value: absolute amount in parentheses (e.g., -$124K)
- More intuitive for understanding relative impact of segments

### Technical Details

#### Files Modified
- `topup-backend/templates/forecast_variance_decomposition.sql` - New template
- `topup-backend/models/schemas.py` - Added new intent and chart type
- `topup-backend/tools/sql_tool.py` - Added forecast gap analysis handling
- `topup-backend/tools/chart_tool.py` - Added waterfall chart builder
- `topup-backend/agents/planner.py` - Enhanced intent detection

#### Files Added
- `docs/implementation-notes/FORECAST_GAP_ANALYSIS_COMPLETE.md` - Feature documentation
- `docs/implementation-notes/PLANNER_FORECAST_GAP_FIX.md` - Planner fix details
- `docs/implementation-notes/WATERFALL_PERCENTAGE_UPDATE.md` - Chart update details

### Testing
- All SQL template tests passing
- Waterfall chart generation validated
- Intent detection verified for gap queries
- Both light and dark themes supported

### Example Queries

The following queries now trigger forecast gap analysis:
- "where are we seeing the largest gap between forecast and actual performance for issuance?"
- "show me the forecast gap analysis for submits"
- "what's driving the forecast miss for approvals?"
- "forecast variance decomposition for issuance"
- "where is the biggest gap in our forecast?"
- "gap analysis for issuance this month"

### Benefits

1. **Better Insights**: Quickly identify which segments drive forecast variances
2. **Actionable**: Focus improvement efforts on high-impact segments
3. **Visual**: Waterfall chart makes variance decomposition intuitive
4. **Flexible**: Works with all metrics and respects segment filters
5. **Percentage-Based**: Easy to compare relative impact across segments

---

## Previous Changes

See `docs/implementation-notes/` for detailed documentation of previous features and fixes:
- Forecast vs Actual by Segment
- Trend Analysis Granularity Fixes
- WoW Variance by Segment
- Multi-Metric Comparison
- Conversation Features
- And more...
