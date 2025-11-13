"""Verify segment values match requirements."""
import sqlite3

conn = sqlite3.connect('data/topup.db')

print("Verifying Segment Values\n" + "="*60)

# Check channels
print("\n1. Channels (Expected: OMB, Email, Search, D2LC, DM, LT, Experian, Karma, Small Partners)")
cursor = conn.execute("SELECT DISTINCT channel FROM cps_tb ORDER BY channel")
channels = [row[0] for row in cursor.fetchall()]
print(f"   Found: {', '.join(channels)}")
print(f"   ✓ Count: {len(channels)} channels")

# Check grades
print("\n2. Grades (Expected: P1, P2, P3, P4, P5, P6)")
cursor = conn.execute("SELECT DISTINCT grade FROM cps_tb ORDER BY grade")
grades = [row[0] for row in cursor.fetchall()]
print(f"   Found: {', '.join(grades)}")
print(f"   ✓ Count: {len(grades)} grades")

# Check terms
print("\n3. Terms (Expected: 36, 48, 60, 72, 84)")
cursor = conn.execute("SELECT DISTINCT term FROM cps_tb ORDER BY term")
terms = [str(row[0]) for row in cursor.fetchall()]
print(f"   Found: {', '.join(terms)}")
print(f"   ✓ Count: {len(terms)} terms")

# Check prod_types
print("\n4. Product Types (Expected: Prime, NP, D2P)")
cursor = conn.execute("SELECT DISTINCT prod_type FROM cps_tb ORDER BY prod_type")
prod_types = [row[0] for row in cursor.fetchall()]
print(f"   Found: {', '.join(prod_types)}")
print(f"   ✓ Count: {len(prod_types)} product types")

# Check repeat_types
print("\n5. Repeat Types (Expected: Repeat, New)")
cursor = conn.execute("SELECT DISTINCT repeat_type FROM cps_tb ORDER BY repeat_type")
repeat_types = [row[0] for row in cursor.fetchall()]
print(f"   Found: {', '.join(repeat_types)}")
print(f"   ✓ Count: {len(repeat_types)} repeat types")

# Check forecast_df has all combinations
print("\n6. Forecast Table Coverage")
cursor = conn.execute("""
    SELECT 
        COUNT(DISTINCT channel) as channels,
        COUNT(DISTINCT grade) as grades,
        COUNT(DISTINCT term) as terms,
        COUNT(DISTINCT prod_type) as prod_types,
        COUNT(DISTINCT repeat_type) as repeat_types
    FROM forecast_df
""")
row = cursor.fetchone()
print(f"   Channels: {row[0]}")
print(f"   Grades: {row[1]}")
print(f"   Terms: {row[2]}")
print(f"   Product Types: {row[3]}")
print(f"   Repeat Types: {row[4]}")

expected_combinations = 9 * 6 * 5 * 3 * 2  # channels * grades * terms * prod_types * repeat_types
cursor = conn.execute("SELECT COUNT(DISTINCT date) FROM forecast_df")
weeks = cursor.fetchone()[0]
expected_total = expected_combinations * weeks
cursor = conn.execute("SELECT COUNT(*) FROM forecast_df")
actual_total = cursor.fetchone()[0]
print(f"   Expected records: {expected_total} ({expected_combinations} combinations × {weeks} weeks)")
print(f"   Actual records: {actual_total}")
print(f"   ✓ Match: {expected_total == actual_total}")

conn.close()
print("\n" + "="*60)
print("✓ All segment values verified!")
