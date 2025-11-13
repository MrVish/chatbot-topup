# Topup CXO Assistant - Manual Testing Guide

This guide provides step-by-step instructions for manually testing the Topup CXO Assistant application.

## Prerequisites

Before starting, ensure you have:
- Python 3.9+ installed
- Node.js 18+ and pnpm installed
- OpenAI API key configured in `topup-backend/.env`
- Sample data generated in the database

## Setup Instructions

### 1. Backend Setup

```bash
# Navigate to backend directory
cd topup-backend

# Create and activate virtual environment (if not already done)
python -m venv venv

# Windows
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Generate sample data (if not already done)
python scripts/generate_sample_data.py

# Start backend server
python -m uvicorn app.main:app --reload --port 8000
```

The backend should start at `http://localhost:8000`

### 2. Frontend Setup

Open a new terminal:

```bash
# Navigate to frontend directory
cd topup-frontend

# Install dependencies (if not already done)
pnpm install

# Start development server
pnpm dev
```

The frontend should start at `http://localhost:3000`

## Manual Testing Checklist

### Test 1: Backend Server Health ✓

**Objective**: Verify backend server is running and /chat endpoint responds

**Steps**:
1. Open browser to `http://localhost:8000/health`
2. Verify you see JSON response with `"status": "healthy"`
3. Check that `cache_size` is present

**Expected Result**: 
```json
{
  "status": "healthy",
  "timestamp": 1699999999.999,
  "cache_size": 0,
  "service": "Topup CXO Assistant API",
  "version": "1.0.0"
}
```

**Pass Criteria**: ✓ Status is "healthy" or "degraded"

---

### Test 2: Frontend UI Loads ✓

**Objective**: Verify frontend application loads correctly

**Steps**:
1. Open browser to `http://localhost:3000`
2. Verify the chat interface loads
3. Check that the input box is visible
4. Verify toolbar with time chips is present

**Expected Result**: 
- Clean UI with chat window
- Input box at bottom
- Toolbar with "Last 7 days", "Last full week", etc. chips
- Theme toggle button visible

**Pass Criteria**: ✓ UI loads without errors

---

### Test 3: Trend Query ✓

**Objective**: Test trend query - "Show WoW issuance by channel last 8 weeks"

**Steps**:
1. In the chat input, type: `Show WoW issuance by channel last 8 weeks`
2. Click Send or press Enter
3. Observe streaming response
4. Wait for chart to render
5. Note the response time

**Expected Result**:
- Streaming status messages appear ("Planning your query...", "Crunching numbers...")
- Line or area chart displays with weekly data
- Chart shows multiple channels (Email, OMB, etc.)
- Insights panel shows executive summary with key findings
- Response completes in < 3.5 seconds

**Pass Criteria**: 
- ✓ Chart renders correctly
- ✓ Insights are displayed
- ✓ Response time < 3.5 seconds

---

### Test 4: Forecast Query ✓

**Objective**: Test forecast query - "How did actual issuance compare to forecast last month by grade?"

**Steps**:
1. Type: `How did actual issuance compare to forecast last month by grade?`
2. Send the query
3. Observe the response
4. Check the chart type

**Expected Result**:
- Grouped bar chart with forecast vs actual bars
- Multiple grades shown (P1, P2, P3, P4, etc.)
- Insights show forecast accuracy metrics
- Delta values highlighted (positive/negative variances)

**Pass Criteria**:
- ✓ Grouped bar chart displays
- ✓ Forecast and actual series visible
- ✓ Insights include accuracy metrics

---

### Test 5: Funnel Query ✓

**Objective**: Test funnel query - "Show the funnel for NP channel Email"

**Steps**:
1. Type: `Show the funnel for NP channel Email`
2. Send the query
3. Observe the funnel chart

**Expected Result**:
- Funnel chart with 3 stages:
  - Submissions (top)
  - Approvals (middle)
  - Issuances (bottom)
- Conversion rates shown between stages
- Insights highlight conversion metrics

**Pass Criteria**:
- ✓ Funnel chart renders
- ✓ Three stages visible
- ✓ Conversion rates calculated

---

### Test 6: Explain Query ✓

**Objective**: Test explain query - "What is funding rate?"

**Steps**:
1. Type: `What is funding rate?`
2. Send the query
3. Observe the response

**Expected Result**:
- Text response with definition
- No chart displayed (explain queries don't generate charts)
- Definition explains funding rate calculation
- Response is quick (< 2 seconds)

**Pass Criteria**:
- ✓ Definition is displayed
- ✓ No chart shown
- ✓ Response is clear and accurate

---

### Test 7: Segment Filters ✓

**Objective**: Apply channel filter and verify query includes filter

**Steps**:
1. Click on the "Channel" dropdown in the toolbar
2. Select "Email"
3. Type: `Show weekly issuance trend`
4. Send the query
5. Observe that results are filtered to Email channel only

**Expected Result**:
- Chart shows only Email channel data
- Insights reference Email channel specifically
- Filter badge appears showing "Channel: Email"

**Pass Criteria**:
- ✓ Filter is applied to query
- ✓ Results show only filtered data
- ✓ UI indicates active filter

---

### Test 8: Time Chips ✓

**Objective**: Click "Last 7 days" and verify query uses correct window

**Steps**:
1. Click the "Last 7 days" chip in the toolbar
2. Observe that a query is automatically generated or the time period is added to input
3. Send the query (if not auto-sent)
4. Verify the chart shows 7 days of data

**Expected Result**:
- Query includes "last 7 days" time window
- Chart displays 7 days of data points
- Date range in insights matches last 7 days

**Pass Criteria**:
- ✓ Time chip triggers correct query
- ✓ Data range matches selected period
- ✓ Chart displays correct time window

---

### Test 9: Chart Interactions ✓

**Objective**: Test hover, zoom, and export PNG/CSV

**Steps**:
1. Run any query that generates a chart
2. **Hover**: Move mouse over chart data points
3. **Zoom**: Click and drag to select a region on the chart
4. **Reset**: Double-click to reset zoom
5. **Export PNG**: Click the export menu and select "Export as PNG"
6. **Export CSV**: Click the export menu and select "Export as CSV"

**Expected Result**:
- **Hover**: Tooltip appears showing exact values
- **Zoom**: Chart zooms into selected region
- **Reset**: Chart returns to original view
- **PNG**: Chart image downloads
- **CSV**: Data file downloads with query results

**Pass Criteria**:
- ✓ Hover tooltips work
- ✓ Zoom functionality works
- ✓ PNG export downloads
- ✓ CSV export downloads with data

---

### Test 10: Theme Toggle ✓

**Objective**: Switch between light and dark mode

**Steps**:
1. Locate the theme toggle button (sun/moon icon)
2. Click to switch to dark mode
3. Observe UI changes
4. Click again to switch back to light mode
5. Refresh the page and verify theme persists

**Expected Result**:
- Dark mode: Dark background, light text, dark chart backgrounds
- Light mode: Light background, dark text, light chart backgrounds
- Theme preference persists after page refresh
- Charts update colors dynamically

**Pass Criteria**:
- ✓ Theme switches correctly
- ✓ Charts update colors
- ✓ Theme persists after refresh

---

### Test 11: Cache Functionality ✓

**Objective**: Repeat query and verify faster response

**Steps**:
1. Run a query: `Show weekly issuance trend last 4 weeks`
2. Note the response time (should be ~2-3 seconds)
3. Wait 2 seconds
4. Run the EXACT same query again
5. Note the response time (should be < 1 second)
6. Observe "Retrieved from cache..." message

**Expected Result**:
- First query: Normal response time (2-3s)
- Second query: Much faster (< 1s)
- Cache hit message appears in streaming status
- Results are identical

**Pass Criteria**:
- ✓ Second query is faster
- ✓ Cache hit message appears
- ✓ Results are consistent

---

### Test 12: Performance Verification ✓

**Objective**: Verify all queries complete within 3.5 seconds

**Steps**:
1. Run each of the following queries and time them:
   - "Show weekly issuance trend"
   - "How did we do vs forecast last month?"
   - "Show the funnel"
   - "What is approval rate?"
2. Record response times
3. Verify all are under 3.5 seconds

**Expected Result**:
- Trend queries: < 3.0s
- Forecast queries: < 3.5s
- Funnel queries: < 3.0s
- Explain queries: < 2.0s
- Cached queries: < 1.0s

**Pass Criteria**:
- ✓ All queries complete within 3.5 seconds
- ✓ P50 latency < 2.5 seconds
- ✓ Cached queries < 1 second

---

## Automated Testing

To run automated end-to-end tests:

```bash
cd topup-backend
python tests/test_e2e_integration.py
```

This will automatically test:
- Backend health
- Chat endpoint availability
- All query types
- Cache functionality
- Segment filters
- Export functionality
- Performance requirements

## Troubleshooting

### Backend won't start
- Check that port 8000 is not in use
- Verify OpenAI API key is set in `.env`
- Ensure virtual environment is activated
- Check that all dependencies are installed

### Frontend won't start
- Check that port 3000 is not in use
- Verify `node_modules` are installed (`pnpm install`)
- Check that backend is running first
- Clear Next.js cache: `rm -rf .next`

### Queries fail or timeout
- Verify database exists: `topup-backend/data/topup.db`
- Check that sample data is generated
- Verify OpenAI API key is valid
- Check backend logs for errors

### Charts don't render
- Check browser console for errors
- Verify Plotly.js is loaded
- Check that chart spec is valid JSON
- Try refreshing the page

### Cache not working
- Check that CACHE_TYPE=memory in `.env`
- Verify cache tool is initialized
- Check backend logs for cache operations
- Try restarting backend server

## Success Criteria

All tests should pass with:
- ✓ Backend server healthy
- ✓ Frontend UI loads
- ✓ All query types work (trend, forecast, funnel, explain)
- ✓ Charts render correctly
- ✓ Insights are generated
- ✓ Filters work
- ✓ Time chips work
- ✓ Chart interactions work (hover, zoom, export)
- ✓ Theme toggle works
- ✓ Cache improves performance
- ✓ All queries complete within 3.5 seconds

## Reporting Issues

If any tests fail, document:
1. Test name and number
2. Steps to reproduce
3. Expected vs actual result
4. Error messages (if any)
5. Screenshots (if applicable)
6. Browser and version
7. Backend logs

## Next Steps

After completing manual testing:
1. Document any issues found
2. Fix critical bugs
3. Optimize slow queries
4. Enhance UI/UX based on feedback
5. Prepare for production deployment
