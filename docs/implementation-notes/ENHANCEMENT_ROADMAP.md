# Topup CXO Assistant - Enhancement Roadmap

## Current Status ✅

### Completed Features
1. ✅ **7 Core Intents**: trend, variance, forecast_vs_actual, funnel, distribution, relationship, explain
2. ✅ **Smart Granularity**: Daily (≤1 month), Weekly (1-4 months), Monthly (>3 months)
3. ✅ **Executive Insights**: Negative-first prioritization, actionable recommendations
4. ✅ **Human-Readable Labels**: Clean axis labels, legends, and titles
5. ✅ **Chart Coverage**: All analytical queries generate charts
6. ✅ **Time Windows**: last_7d, last_full_week, last_30d, last_full_month, last_3_full_months
7. ✅ **NEW: QTD, MTD, YTD Support**: Quarter/Month/Year-to-date time windows

## Phase 1: Enhanced Time Windows & Multi-Metric Support 🚧

### 1.1 Additional Time Windows (COMPLETED)
- ✅ Quarter-to-date (QTD)
- ✅ Month-to-date (MTD)  
- ✅ Year-to-date (YTD)

### 1.2 Multi-Metric Comparisons (TODO)
**Need**: "Show app submits vs approvals vs issuances"

**Implementation**:
- Add new SQL template: `multi_metric_trend.sql`
- Support multiple metrics in single query
- Generate multi-line charts with different colors per metric
- Update planner to handle "vs" queries

**Example Queries**:
- "Show app submits vs approvals vs issuances this quarter"
- "Compare submissions, approvals, and issuances by channel"
- "App submit $ vs # trends"

### 1.3 Baseline Comparisons (TODO)
**Need**: "How are we trending vs baseline?"

**Implementation**:
- Add baseline calculation logic
- Support "vs baseline" in variance queries
- Show deviation from baseline in insights

## Phase 2: Advanced Segmentation 🔮

### 2.1 Multi-Segment Breakdowns (TODO)
**Need**: "Show by FICO band AND channel"

**Current**: Single segment at a time
**Target**: Multiple segment dimensions

**Implementation**:
- Update SQL templates to support GROUP BY multiple columns
- Generate grouped/stacked bar charts
- Handle complex segment combinations

**Example Queries**:
- "Show issuances by FICO band and channel"
- "Approval rates by grade and repeat type"
- "Funnel by channel and product type"

### 2.2 Audience-Level Segments (TODO)
**Need**: Support for business-specific segments

**New Segments to Add**:
- `audience`: Karma, Experian, Small Partners, Top Up, Pagaya, DM, ITA Prime, NP
- `program`: ITA Subsequent, ITA Concurrent, Top Up, PA, CIAB
- `sub_segment`: CK-Lightbox, CK-Others, Experian Activate, Experian API

**Implementation**:
- Extend database schema with new segment columns
- Update segment filters in Plan model
- Add to router and planner prompts

## Phase 3: Conversational Intelligence 🤖

### 3.1 Conversation History (TODO)
**Need**: Context-aware follow-ups

**Implementation**:
- Store last 5 queries in session
- Pass conversation history to planner
- Enable pronoun resolution ("show it by channel", "compare to last month")

**Example Flow**:
```
User: "Show QTD approvals"
Bot: [Shows chart]
User: "Break it down by channel"  ← Understands "it" = approvals
Bot: [Shows channel breakdown]
User: "Which one is declining?"  ← Understands context
Bot: [Identifies declining channels]
```

### 3.2 Smart Follow-Up Suggestions (TODO)
**Need**: Contextual next questions

**Current**: Generic suggestions by intent
**Target**: Data-driven suggestions based on actual results

**Implementation**:
- Analyze query results to identify interesting patterns
- Generate 3-5 contextual follow-up questions
- Display as clickable chips below chart

**Example Suggestions After "QTD Approvals by Channel"**:
- "Which channels are below forecast?"
- "Show week-over-week trend for Email"
- "Compare to last quarter"
- "What's the funnel for declining channels?"

### 3.3 Drill-Down Navigation (TODO)
**Need**: Click-to-drill on chart elements

**Implementation**:
- Make chart segments clickable
- Auto-generate drill-down query
- Maintain breadcrumb navigation

**Example**:
- Click "Email" in channel chart → Shows Email weekly trend
- Click specific week → Shows that week's funnel
- Breadcrumb: "All Channels > Email > Week 42"

## Phase 4: Forward-Looking Analytics 🔮

### 4.1 Projection Intent (TODO)
**Need**: "What are projections for rest of quarter?"

**Implementation**:
- Add "projection" intent to router
- Create projection SQL template
- Use simple linear regression or moving average
- Show projected vs actual with confidence bands

**Example Queries**:
- "What's the outlook for next month?"
- "Project end-of-quarter performance"
- "Where will we land vs forecast?"

### 4.2 Momentum Analysis (TODO)
**Need**: "Based on current trajectory..."

**Implementation**:
- Calculate velocity (rate of change)
- Identify acceleration/deceleration
- Predict target achievement probability

## Phase 5: Channel-Specific Metrics 📊

### 5.1 Email Metrics (TODO)
**Need**: "Show Email metrics — sends, open rate, click rate"

**New Metrics**:
- `email_sends`, `email_opens`, `email_clicks`
- `open_rate`, `click_rate`, `click_to_send_rate`, `response_rate`

### 5.2 OMB Metrics (TODO)
**Need**: "Show OMB metrics — logins, impressions, click rate"

**New Metrics**:
- `omb_logins`, `omb_impressions`, `omb_clicks`
- `omb_click_rate`, `omb_response_rate`

### 5.3 Engagement Analysis (TODO)
**Need**: "How are we trending vs baseline for offer rates, take rates?"

**New Metrics**:
- `offer_rate`, `take_rate`, `avg_loan_size`
- Baseline comparisons for each

## Phase 6: Performance Optimization ⚡

### 6.1 Query Caching Enhancement (TODO)
- Extend cache TTL for common queries
- Pre-cache popular query patterns
- Implement cache warming on startup

### 6.2 Parallel Processing (TODO)
- Execute chart and insights generation in parallel
- Reduce total latency by 30-40%

### 6.3 Incremental Data Loading (TODO)
- Stream chart data as it becomes available
- Show partial results while processing

## Implementation Priority

### High Priority (Next Sprint)
1. ✅ QTD/MTD/YTD time windows
2. Multi-metric comparisons
3. Conversation history
4. Smart follow-up suggestions

### Medium Priority (Following Sprint)
5. Multi-segment breakdowns
6. Audience-level segments
7. Projection intent
8. Drill-down navigation

### Low Priority (Future)
9. Channel-specific metrics
10. Baseline comparisons
11. Performance optimizations

## Technical Debt

### Database Schema
- Add audience, program, sub_segment columns
- Add email/OMB metrics tables
- Create indexes for common query patterns

### Code Refactoring
- Extract common SQL generation logic
- Consolidate metric calculation functions
- Improve error handling and fallbacks

### Testing
- Add integration tests for new intents
- Test multi-segment combinations
- Validate conversation context handling

## Success Metrics

### User Engagement
- Average queries per session: Target 5+ (current: ~2)
- Follow-up question click rate: Target 40%+
- Drill-down usage: Target 30%+ of sessions

### Query Coverage
- Intent classification accuracy: Target 95%+ (current: ~90%)
- Successful query execution: Target 98%+ (current: ~95%)
- Cache hit rate: Target 60%+ (current: ~40%)

### Performance
- P50 latency: Target <1s (current: ~1.4s)
- P95 latency: Target <2s (current: ~2.5s)
- Chart generation: Target <200ms (current: ~300ms)

## Notes

- All enhancements should maintain backward compatibility
- Prioritize executive-level insights over technical details
- Keep UI simple and intuitive
- Test with real user queries before deployment
