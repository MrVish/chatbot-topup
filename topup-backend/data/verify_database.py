"""Verify database setup."""
import sqlite3

conn = sqlite3.connect('data/topup.db')
cursor = conn.cursor()

# Check row counts
cursor.execute('SELECT COUNT(*) FROM cps_tb')
cps_count = cursor.fetchone()[0]
print(f'✓ cps_tb rows: {cps_count}')

cursor.execute('SELECT COUNT(*) FROM forecast_df')
forecast_count = cursor.fetchone()[0]
print(f'✓ forecast_df rows: {forecast_count}')

# Check sample data
print('\n--- Sample cps_tb data ---')
cursor.execute('SELECT loan_id, app_create_d, app_submit_d, channel, grade, prod_type, cr_fico_band, issued_flag FROM cps_tb LIMIT 3')
for row in cursor.fetchall():
    print(row)

print('\n--- Sample forecast_df data ---')
cursor.execute('SELECT date, prod_type, channel, grade, term, forecast_issuance, actual_issuance FROM forecast_df LIMIT 3')
for row in cursor.fetchall():
    print(row)

# Check date ranges
print('\n--- Date ranges ---')
cursor.execute('SELECT MIN(app_create_d), MAX(app_create_d) FROM cps_tb')
min_date, max_date = cursor.fetchone()
print(f'cps_tb create date range: {min_date} to {max_date}')

cursor.execute('SELECT MIN(app_submit_d), MAX(app_submit_d) FROM cps_tb WHERE app_submit_d IS NOT NULL')
min_date, max_date = cursor.fetchone()
print(f'cps_tb submit date range: {min_date} to {max_date}')

cursor.execute('SELECT MIN(date), MAX(date) FROM forecast_df')
min_date, max_date = cursor.fetchone()
print(f'forecast_df date range: {min_date} to {max_date}')

# Check segment distributions
print('\n--- Segment distributions ---')
cursor.execute('SELECT channel, COUNT(*) FROM cps_tb GROUP BY channel')
print('Channels:', dict(cursor.fetchall()))

cursor.execute('SELECT grade, COUNT(*) FROM cps_tb GROUP BY grade')
print('Grades:', dict(cursor.fetchall()))

cursor.execute('SELECT cr_fico_band, COUNT(*) FROM cps_tb GROUP BY cr_fico_band ORDER BY CASE cr_fico_band WHEN "<640" THEN 1 WHEN "640-699" THEN 2 WHEN "700-759" THEN 3 WHEN "760+" THEN 4 END')
print('FICO bands:', dict(cursor.fetchall()))

cursor.execute('SELECT purpose, COUNT(*) FROM cps_tb GROUP BY purpose')
print('Purposes:', dict(cursor.fetchall()))

# Check flags
print('\n--- Flags ---')
cursor.execute('SELECT SUM(offered_flag), SUM(website_complete_flag), SUM(cr_appr_flag), SUM(issued_flag) FROM cps_tb')
offered, website_complete, approved, issued = cursor.fetchone()
print(f'Offered: {offered}, Website Complete: {website_complete}, Approved: {approved}, Issued: {issued}')

conn.close()
print('\n✓ Database verification complete!')
