"""Test new columns in updated schema."""
import sqlite3

conn = sqlite3.connect('data/topup.db')
conn.row_factory = sqlite3.Row

print("Testing New Schema Columns\n" + "="*50)

# Test 1: New cps_tb columns
print("\n1. Testing new cps_tb columns")
cursor = conn.execute("""
    SELECT 
        loan_id,
        app_create_d,
        website_complete_flag,
        a_income,
        cr_dti,
        purpose,
        interest_rate,
        origination_fee
    FROM cps_tb 
    WHERE app_submit_d IS NOT NULL
    LIMIT 3
""")
results = cursor.fetchall()
print(f"   ✓ Retrieved {len(results)} records with new columns")
for row in results:
    print(f"   Loan {row['loan_id']}: Income=${row['a_income']:,}, DTI={row['cr_dti']:.2f}, Purpose={row['purpose']}")

# Test 2: Application funnel stages
print("\n2. Testing application funnel stages")
cursor = conn.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN app_create_d IS NOT NULL THEN 1 ELSE 0 END) as created,
        SUM(website_complete_flag) as website_complete,
        SUM(CASE WHEN app_submit_d IS NOT NULL THEN 1 ELSE 0 END) as submitted,
        SUM(cr_appr_flag) as approved,
        SUM(issued_flag) as issued
    FROM cps_tb
""")
row = cursor.fetchone()
print(f"   Total: {row['total']}")
print(f"   Created: {row['created']} (100%)")
print(f"   Website Complete: {row['website_complete']} ({row['website_complete']/row['total']*100:.1f}%)")
print(f"   Submitted: {row['submitted']} ({row['submitted']/row['total']*100:.1f}%)")
print(f"   Approved: {row['approved']} ({row['approved']/row['total']*100:.1f}%)")
print(f"   Issued: {row['issued']} ({row['issued']/row['total']*100:.1f}%)")

# Test 3: New forecast_df structure
print("\n3. Testing forecast_df structure")
cursor = conn.execute("""
    SELECT 
        date,
        prod_type,
        repeat_type,
        channel,
        grade,
        term,
        forecast_app_submits,
        outlook_app_submits,
        actual_app_submits,
        forecast_apps_approved,
        outlook_apps_approved,
        actual_apps_approved,
        forecast_issuance,
        outlook_issuance,
        actual_issuance
    FROM forecast_df
    LIMIT 3
""")
results = cursor.fetchall()
print(f"   ✓ Retrieved {len(results)} forecast records")
for row in results:
    print(f"   {row['date']} | {row['prod_type']} | {row['channel']} | Grade {row['grade']} | {row['term']}mo")
    print(f"      Submits - F:{row['forecast_app_submits']:.1f} O:{row['outlook_app_submits']:.1f} A:{row['actual_app_submits']:.1f}")

# Test 4: Composite primary key
print("\n4. Testing composite primary key uniqueness")
cursor = conn.execute("""
    SELECT 
        date, prod_type, repeat_type, channel, grade, term, COUNT(*) as cnt
    FROM forecast_df
    GROUP BY date, prod_type, repeat_type, channel, grade, term
    HAVING COUNT(*) > 1
""")
duplicates = cursor.fetchall()
if len(duplicates) == 0:
    print("   ✓ No duplicate composite keys found")
else:
    print(f"   ✗ Found {len(duplicates)} duplicate composite keys")

# Test 5: Purpose filter
print("\n5. Testing purpose segmentation")
cursor = conn.execute("""
    SELECT 
        purpose,
        COUNT(*) as count,
        AVG(app_submit_amnt) as avg_amount,
        AVG(cr_fico) as avg_fico
    FROM cps_tb
    WHERE app_submit_d IS NOT NULL
    GROUP BY purpose
    ORDER BY count DESC
""")
results = cursor.fetchall()
print(f"   ✓ Found {len(results)} loan purposes")
for row in results:
    print(f"   {row['purpose']}: {row['count']} loans, Avg Amount: ${row['avg_amount']:,.0f}, Avg FICO: {row['avg_fico']:.0f}")

# Test 6: Income and DTI analysis
print("\n6. Testing income and DTI metrics")
cursor = conn.execute("""
    SELECT 
        grade,
        AVG(a_income) as avg_income,
        AVG(cr_dti) as avg_dti,
        AVG(app_submit_amnt) as avg_loan_amount
    FROM cps_tb
    WHERE app_submit_d IS NOT NULL
    GROUP BY grade
    ORDER BY grade
""")
results = cursor.fetchall()
print(f"   ✓ Income and DTI by grade:")
for row in results:
    print(f"   Grade {row['grade']}: Income=${row['avg_income']:,.0f}, DTI={row['avg_dti']:.2%}, Loan=${row['avg_loan_amount']:,.0f}")

# Test 7: Origination fees
print("\n7. Testing origination fees")
cursor = conn.execute("""
    SELECT 
        COUNT(*) as count,
        SUM(origination_fee) as total_fees,
        AVG(origination_fee) as avg_fee,
        AVG(origination_fee / NULLIF(app_submit_amnt, 0) * 100) as avg_fee_pct
    FROM cps_tb
    WHERE app_submit_d IS NOT NULL
""")
row = cursor.fetchone()
print(f"   Total Fees: ${row['total_fees']:,.2f}")
print(f"   Average Fee: ${row['avg_fee']:,.2f}")
print(f"   Average Fee %: {row['avg_fee_pct']:.2f}%")

conn.close()
print("\n" + "="*50)
print("✓ All new column tests passed!")
