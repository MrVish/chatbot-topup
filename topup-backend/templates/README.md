# SQL Templates

This directory contains parameterized SQL templates for the Topup CXO Assistant.

## Template Files

### 1. trend_weekly.sql
Analyzes trends over time with weekly granularity.

**Parameters:**
- `:start_date`, `:end_date` - Date range
- `{date_col}` - Date column to use (app_submit_d, apps_approved_d, issued_d)
- `{metric_expression}` - SQL expression for the metric
- Segment filters: `{channel_filter}`, `{grade_filter}`, etc.

**Metric Expressions:**
- App Submits (Amount): `SUM(app_submit_amnt)`
- App Submits (Count): `COUNT(app_submit_d)`
- App Approvals (Amount): `SUM(CASE WHEN cr_appr_flag = 1 THEN apps_approved_amnt ELSE 0 END)`
- App Approvals (Count): `SUM(cr_appr_flag)`
- Issuances (Amount): `SUM(CASE WHEN issued_flag = 1 THEN issued_amnt ELSE 0 END)`
- Issuances (Count): `SUM(issued_flag)`
- Approval Rate: `CAST(SUM(cr_appr_flag) AS REAL) / NULLIF(SUM(offered_flag), 0) * 100`
- Funding Rate: `CAST(SUM(issued_flag) AS REAL) / NULLIF(COUNT(app_submit_d), 0) * 100`
- Website Complete Rate: `CAST(SUM(website_complete_flag) AS REAL) / NULLIF(COUNT(app_create_d), 0) * 100`
- Average APR: `AVG(offer_apr)`
- Average Interest Rate: `AVG(interest_rate)`
- Average FICO: `AVG(cr_fico)`
- Average DTI: `AVG(cr_dti)`
- Average Income: `AVG(a_income)`
- Total Origination Fees: `SUM(origination_fee)`

### 2. funnel_last_full_month.sql
Analyzes conversion funnel: Submissions → Approvals → Issuances.

**Parameters:**
- `:start_date`, `:end_date` - Date range
- Segment filters

**Returns:**
- Stage name, value (amount and count), conversion rate

### 3. forecast_vs_actual_weekly.sql
Compares forecast and outlook predictions against actual results.

**Parameters:**
- `:start_date`, `:end_date` - Date range
- `{forecast_col}`, `{outlook_col}`, `{actual_col}` - Column names for metric type
- Segment filters: `{channel_filter}`, `{grade_filter}`, `{prod_type_filter}`, `{repeat_type_filter}`, `{term_filter}`

**Metric Types:**
- Submits: forecast_app_submits, outlook_app_submits, actual_app_submits
- Approved: forecast_apps_approved, outlook_apps_approved, actual_apps_approved
- Issuance: forecast_issuance, outlook_issuance, actual_issuance

**Returns:**
- Week, forecast value, outlook value, actual value, deltas, accuracy percentages, absolute error percentages

### 4. mom_delta.sql
Month-over-Month comparison with percentage deltas.

**Parameters:**
- `{date_col}` - Date column
- `{metric_expression}` - Metric to compare
- Segment filters

**Returns:**
- Month, current value, prior month value, delta, delta percentage

### 5. wow_delta.sql
Week-over-Week comparison with percentage deltas.

**Parameters:**
- `{date_col}` - Date column
- `{metric_expression}` - Metric to compare
- Segment filters

**Returns:**
- Week, current value, prior week value, delta, delta percentage

### 6. distribution.sql
Segment composition analysis (e.g., by channel, grade, FICO band).

**Parameters:**
- `:start_date`, `:end_date` - Date range
- `{date_col}` - Date column
- `{metric_expression}` - Metric to analyze
- `{segment_by}` - Column to segment by (channel, grade, cr_fico_band, etc.)
- Segment filters

**Returns:**
- Segment name, metric value, record count, percentage of total

## Filter Placeholders

All templates support dynamic filter injection:

- `{channel_filter}` → `AND channel = :channel` (if provided)
- `{grade_filter}` → `AND grade = :grade` (if provided)
- `{prod_type_filter}` → `AND prod_type = :prod_type` (if provided)
- `{repeat_type_filter}` → `AND repeat_type = :repeat_type` (if provided)
- `{term_filter}` → `AND term = :term` (if provided)
- `{fico_band_filter}` → `AND cr_fico_band = :cr_fico_band` (if provided)
- `{purpose_filter}` → `AND purpose = :purpose` (if provided)

If a filter is not provided, the placeholder is replaced with an empty string.

## Safety Features

All templates include:

1. **NULLIF guards** - Prevents division by zero errors
2. **Row limits** - Maximum 10,000 rows returned
3. **Parameterized queries** - All user inputs use SQLite parameter substitution
4. **Read-only operations** - No INSERT, UPDATE, DELETE, or DROP statements

## Usage Example

```python
from pathlib import Path
import sqlite3

# Load template
template_path = Path("templates/trend_weekly.sql")
template = template_path.read_text()

# Replace placeholders
sql = template.format(
    date_col="issued_d",
    metric_expression="SUM(CASE WHEN issued_flag = 1 THEN issued_amt ELSE 0 END)",
    channel_filter="AND channel = :channel",
    grade_filter="",
    prod_type_filter="",
    repeat_type_filter="",
    term_filter="",
    fico_band_filter=""
)

# Execute with parameters
conn = sqlite3.connect("data/topup.db", uri=True, check_same_thread=False)
conn.execute("PRAGMA query_only = ON")  # Read-only mode
cursor = conn.execute(sql, {
    "start_date": "2024-10-01",
    "end_date": "2024-11-10",
    "channel": "Email"
})
results = cursor.fetchall()
```

## Date Functions Reference

SQLite date functions used in templates:

- `date('now')` - Current date
- `date('now', '-7 day')` - 7 days ago
- `date('now', 'start of month')` - First day of current month
- `date('now', 'start of month', '-1 month')` - First day of last month
- `date('now', 'weekday 0')` - Most recent Monday
- `strftime('%Y-%W', date)` - Year-week format (e.g., "2024-45")
- `strftime('%Y-%m', date)` - Year-month format (e.g., "2024-11")
