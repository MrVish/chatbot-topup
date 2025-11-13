"""Quick verification script for generated data."""
import sqlite3

conn = sqlite3.connect('topup-backend/data/topup.db')
cursor = conn.cursor()

print("\n=== Sample cps_tb Records ===")
cursor.execute("""
    SELECT channel, grade, cr_fico_band, app_submit_amnt, cr_appr_flag, issued_flag
    FROM cps_tb 
    WHERE app_submit_d IS NOT NULL
    LIMIT 5
""")
print("Channel | Grade | FICO Band | Submit Amt | Approved | Issued")
print("-" * 65)
for row in cursor.fetchall():
    print(f"{row[0]:8} | {row[1]:5} | {row[2]:9} | ${row[3]:9,.2f} | {row[4]:8} | {row[5]:6}")

print("\n=== Sample forecast_df Records ===")
cursor.execute("""
    SELECT date, channel, grade, 
           ROUND(forecast_issuance, 2) as forecast, 
           ROUND(actual_issuance, 2) as actual,
           ROUND((actual_issuance - forecast_issuance) / forecast_issuance * 100, 1) as variance_pct
    FROM forecast_df 
    WHERE channel = 'OMB' AND grade = 'P3'
    ORDER BY date DESC 
    LIMIT 5
""")
print("Date       | Channel | Grade | Forecast | Actual | Variance %")
print("-" * 65)
for row in cursor.fetchall():
    print(f"{row[0]} | {row[1]:7} | {row[2]:5} | {row[3]:8.2f} | {row[4]:6.2f} | {row[5]:9.1f}%")

print("\n=== Date Range Coverage ===")
cursor.execute("SELECT MIN(app_submit_d), MAX(app_submit_d) FROM cps_tb WHERE app_submit_d IS NOT NULL")
min_date, max_date = cursor.fetchone()
print(f"cps_tb: {min_date} to {max_date}")

cursor.execute("SELECT MIN(date), MAX(date) FROM forecast_df")
min_date, max_date = cursor.fetchone()
print(f"forecast_df: {min_date} to {max_date}")

conn.close()
print("\n✓ Verification complete!\n")
