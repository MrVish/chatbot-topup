import sqlite3
conn = sqlite3.connect('data/topup.db')
cursor = conn.execute('''
    SELECT 
        ROUND(CAST(SUM(actual_issuance) AS REAL) / NULLIF(SUM(forecast_issuance), 0) * 100, 2) AS accuracy
    FROM forecast_df 
    WHERE date BETWEEN "2025-08-12" AND "2025-09-01"
''')
print('Accuracy:', cursor.fetchone()[0], '%')
conn.close()
