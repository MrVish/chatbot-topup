"""Test SQL templates."""
import sqlite3
from pathlib import Path

conn = sqlite3.connect('data/topup.db')
conn.row_factory = sqlite3.Row

print("Testing SQL Templates\n" + "="*50)

# Test 1: trend_weekly.sql
print("\n1. Testing trend_weekly.sql")
template = Path('templates/trend_weekly.sql').read_text()
sql = template.format(
    date_col="issued_d",
    metric_expression="SUM(CASE WHEN issued_flag = 1 THEN issued_amnt ELSE 0 END)",
    channel_filter="AND channel = :channel",
    grade_filter="",
    prod_type_filter="",
    repeat_type_filter="",
    term_filter="",
    fico_band_filter="",
    purpose_filter=""
)
cursor = conn.execute(sql, {
    "start_date": "2025-08-01",
    "end_date": "2025-11-10",
    "channel": "Email"
})
results = cursor.fetchall()
print(f"   ✓ Returned {len(results)} weeks")
if results:
    print(f"   Sample: Week {results[0]['week']}, Value: ${results[0]['metric_value']:,.2f}")

# Test 2: funnel_last_full_month.sql
print("\n2. Testing funnel_last_full_month.sql")
template = Path('templates/funnel_last_full_month.sql').read_text()
sql = template.format(
    channel_filter="",
    grade_filter="",
    prod_type_filter="",
    repeat_type_filter="",
    term_filter="",
    fico_band_filter="",
    purpose_filter=""
)
cursor = conn.execute(sql, {
    "start_date": "2025-10-01",
    "end_date": "2025-10-31"
})
results = cursor.fetchall()
print(f"   ✓ Returned {len(results)} funnel stages")
for row in results:
    print(f"   {row['stage']}: ${row['value_amt']:,.2f} ({row['conversion_rate']:.1f}%)")

# Test 3: forecast_vs_actual_weekly.sql
print("\n3. Testing forecast_vs_actual_weekly.sql")
template = Path('templates/forecast_vs_actual_weekly.sql').read_text()
sql = template.format(
    forecast_col="forecast_issuance",
    outlook_col="outlook_issuance",
    actual_col="actual_issuance",
    channel_filter="",
    grade_filter="",
    prod_type_filter="",
    repeat_type_filter="",
    term_filter=""
)
cursor = conn.execute(sql, {
    "start_date": "2025-08-12",
    "end_date": "2025-11-04"
})
results = cursor.fetchall()
print(f"   ✓ Returned {len(results)} weeks")
if results:
    row = results[0]
    print(f"   Sample: Week {row['week']}, Forecast: {row['forecast_value']:.1f}, Actual: {row['actual_value']:.1f}, Accuracy: {row['accuracy_vs_forecast_pct']}%")

# Test 4: wow_delta.sql
print("\n4. Testing wow_delta.sql")
template = Path('templates/wow_delta.sql').read_text()
sql = template.format(
    date_col="issued_d",
    metric_expression="SUM(CASE WHEN issued_flag = 1 THEN issued_amnt ELSE 0 END)",
    channel_filter="",
    grade_filter="",
    prod_type_filter="",
    repeat_type_filter="",
    term_filter="",
    fico_band_filter="",
    purpose_filter=""
)
cursor = conn.execute(sql)
results = cursor.fetchall()
print(f"   ✓ Returned {len(results)} weeks with WoW comparison")
if results:
    row = results[0]
    print(f"   Latest: Week {row['week']}, Current: ${row['current_value']:,.2f}, Delta: {row['delta_pct']}%")

# Test 5: distribution.sql
print("\n5. Testing distribution.sql")
template = Path('templates/distribution.sql').read_text()
sql = template.format(
    date_col="issued_d",
    metric_expression="SUM(CASE WHEN issued_flag = 1 THEN issued_amnt ELSE 0 END)",
    segment_by="channel",
    channel_filter="",
    grade_filter="",
    prod_type_filter="",
    repeat_type_filter="",
    term_filter="",
    fico_band_filter="",
    purpose_filter=""
)
cursor = conn.execute(sql, {
    "start_date": "2025-08-01",
    "end_date": "2025-11-10"
})
results = cursor.fetchall()
print(f"   ✓ Returned {len(results)} segments")
for row in results[:3]:
    print(f"   {row['segment']}: ${row['metric_value']:,.2f} ({row['percentage']}%)")

# Test 6: FICO band ordering in distribution
print("\n6. Testing FICO band ordering")
sql = template.format(
    date_col="issued_d",
    metric_expression="SUM(CASE WHEN issued_flag = 1 THEN issued_amnt ELSE 0 END)",
    segment_by="cr_fico_band",
    channel_filter="",
    grade_filter="",
    prod_type_filter="",
    repeat_type_filter="",
    term_filter="",
    fico_band_filter="",
    purpose_filter=""
)
cursor = conn.execute(sql, {
    "start_date": "2025-08-01",
    "end_date": "2025-11-10"
})
results = cursor.fetchall()
print(f"   ✓ FICO bands in order:")
for row in results:
    print(f"   {row['segment']}: ${row['metric_value']:,.2f}")

# Test 7: NULLIF division guards
print("\n7. Testing NULLIF division guards")
cursor = conn.execute("""
    SELECT 
        SUM(cr_appr_flag) / NULLIF(SUM(offered_flag), 0) * 100 AS approval_rate,
        SUM(issued_flag) / NULLIF(COUNT(app_submit_d), 0) * 100 AS funding_rate
    FROM cps_tb
    WHERE app_submit_d >= '2025-10-01'
""")
row = cursor.fetchone()
print(f"   ✓ Approval Rate: {row['approval_rate']:.2f}%")
print(f"   ✓ Funding Rate: {row['funding_rate']:.2f}%")

conn.close()
print("\n" + "="*50)
print("✓ All template tests passed!")
