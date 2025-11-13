"""
Sample Data Generation Script for Topup CXO Assistant.

This script generates realistic sample data for testing the Topup system:
- 1000+ rows of cps_tb data with realistic distributions
- 100+ rows of forecast_df data with forecast vs actual variances
- Data covers last 6 months for testing time windows
- Includes variety of channels, grades, FICO bands, and other segments

Requirements: 1.1
"""

import sqlite3
import random
import os
from datetime import datetime, timedelta
from pathlib import Path


# Configuration constants
CHANNELS = ["OMB", "Email", "Search", "D2LC", "DM", "LT", "Experian", "Karma", "Small Partners"]
GRADES = ["P1", "P2", "P3", "P4", "P5", "P6"]
PROD_TYPES = ["Prime", "NP", "D2P"]
REPEAT_TYPES = ["Repeat", "New"]
TERMS = [36, 48, 60, 72, 84]
FICO_BANDS = ["<640", "640-699", "700-759", "760+"]
PURPOSES = [
    "debt_consolidation",
    "home_improvement",
    "major_purchase",
    "medical",
    "car",
    "credit_card",
    "other"
]

# Realistic distributions (weights for random.choices)
CHANNEL_WEIGHTS = [25, 20, 15, 12, 10, 8, 5, 3, 2]  # OMB and Email are most common
GRADE_WEIGHTS = [10, 15, 25, 25, 15, 10]  # P3 and P4 are most common
PROD_TYPE_WEIGHTS = [50, 30, 20]  # Prime is most common
REPEAT_TYPE_WEIGHTS = [60, 40]  # More repeat customers
TERM_WEIGHTS = [15, 20, 35, 20, 10]  # 60-month is most common
FICO_BAND_WEIGHTS = [15, 25, 35, 25]  # 700-759 is most common


def get_database_path():
    """Get the database path, checking both possible locations."""
    # Try relative to script location
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent
    
    # Check if we're in topup-backend/scripts
    db_path = backend_dir / "data" / "topup.db"
    if db_path.parent.exists():
        return str(db_path)
    
    # Try workspace root
    workspace_root = backend_dir.parent
    db_path = workspace_root / "data" / "topup.db"
    if db_path.parent.exists():
        return str(db_path)
    
    # Default to backend/data
    db_path = backend_dir / "data" / "topup.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return str(db_path)


def create_tables(conn: sqlite3.Connection):
    """Create database tables if they don't exist."""
    cursor = conn.cursor()
    
    # Create cps_tb table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cps_tb (
            loan_id INTEGER PRIMARY KEY,
            app_create_d DATE,
            prod_type TEXT,
            repeat_type TEXT,
            channel TEXT,
            grade TEXT,
            term INTEGER,
            offered_flag INTEGER,
            website_complete_flag INTEGER,
            app_submit_d DATE,
            app_submit_amnt REAL,
            cr_appr_flag INTEGER,
            apps_approved_d DATE,
            apps_approved_amnt REAL,
            issued_flag INTEGER,
            issued_d DATE,
            issued_amnt REAL,
            cr_fico INTEGER,
            cr_fico_band TEXT,
            a_income INTEGER,
            cr_dti REAL,
            purpose TEXT,
            interest_rate REAL,
            offer_apr REAL,
            origination_fee REAL
        )
    """)
    
    # Create forecast_df table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS forecast_df (
            date DATE,
            prod_type TEXT,
            repeat_type TEXT,
            channel TEXT,
            grade TEXT,
            term INTEGER,
            forecast_app_submits REAL,
            forecast_apps_approved REAL,
            forecast_issuance REAL,
            outlook_app_submits REAL,
            outlook_apps_approved REAL,
            outlook_issuance REAL,
            actual_app_submits REAL,
            actual_apps_approved REAL,
            actual_issuance REAL,
            PRIMARY KEY (date, prod_type, repeat_type, channel, grade, term)
        )
    """)
    
    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cps_create_d ON cps_tb(app_create_d)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cps_submit_d ON cps_tb(app_submit_d)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cps_approved_d ON cps_tb(apps_approved_d)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cps_issued_d ON cps_tb(issued_d)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cps_channel ON cps_tb(channel)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cps_grade ON cps_tb(grade)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cps_prod_type ON cps_tb(prod_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cps_repeat_type ON cps_tb(repeat_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cps_fico_band ON cps_tb(cr_fico_band)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_forecast_date ON forecast_df(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_forecast_channel ON forecast_df(channel)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_forecast_grade ON forecast_df(grade)")
    
    conn.commit()
    print("✓ Tables and indexes created")


def clear_existing_data(conn: sqlite3.Connection):
    """Clear existing data from tables."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cps_tb")
    cursor.execute("DELETE FROM forecast_df")
    conn.commit()
    print("✓ Existing data cleared")


def generate_fico_score(fico_band: str) -> int:
    """Generate a FICO score within the specified band."""
    if fico_band == "<640":
        return random.randint(550, 639)
    elif fico_band == "640-699":
        return random.randint(640, 699)
    elif fico_band == "700-759":
        return random.randint(700, 759)
    else:  # "760+"
        return random.randint(760, 850)


def calculate_approval_probability(grade: str, fico: int, channel: str) -> float:
    """Calculate approval probability based on grade, FICO, and channel."""
    # Base probability by grade
    base_prob = {
        "P1": 0.85,
        "P2": 0.80,
        "P3": 0.75,
        "P4": 0.65,
        "P5": 0.55,
        "P6": 0.45
    }[grade]
    
    # Adjust by FICO
    if fico >= 760:
        base_prob += 0.10
    elif fico >= 700:
        base_prob += 0.05
    elif fico < 640:
        base_prob -= 0.10
    
    # Adjust by channel (some channels have better quality)
    if channel in ["OMB", "Email"]:
        base_prob += 0.05
    elif channel in ["Small Partners", "Karma"]:
        base_prob -= 0.05
    
    return min(0.95, max(0.20, base_prob))


def calculate_issuance_probability(grade: str, fico: int) -> float:
    """Calculate issuance probability for approved loans."""
    # Base probability
    base_prob = 0.75
    
    # Adjust by grade
    if grade in ["P1", "P2"]:
        base_prob += 0.10
    elif grade in ["P5", "P6"]:
        base_prob -= 0.10
    
    # Adjust by FICO
    if fico >= 760:
        base_prob += 0.05
    elif fico < 640:
        base_prob -= 0.05
    
    return min(0.95, max(0.50, base_prob))


def generate_cps_tb_data(conn: sqlite3.Connection, num_records: int = 1200):
    """
    Generate sample data for cps_tb table.
    
    Args:
        conn: SQLite connection
        num_records: Number of records to generate (default: 1200)
    """
    cursor = conn.cursor()
    
    # Get existing max loan_id
    cursor.execute("SELECT MAX(loan_id) FROM cps_tb")
    max_id = cursor.fetchone()[0]
    start_id = (max_id or 0) + 1
    
    # Generate data for last 6 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    records = []
    
    print(f"Generating {num_records} cps_tb records...")
    
    for i in range(num_records):
        loan_id = start_id + i
        
        # Random application create date (weighted towards recent dates)
        days_offset = int(random.triangular(0, 180, 150))  # More recent data
        create_date = start_date + timedelta(days=days_offset)
        
        # Random attributes with realistic distributions
        channel = random.choices(CHANNELS, weights=CHANNEL_WEIGHTS)[0]
        grade = random.choices(GRADES, weights=GRADE_WEIGHTS)[0]
        prod_type = random.choices(PROD_TYPES, weights=PROD_TYPE_WEIGHTS)[0]
        repeat_type = random.choices(REPEAT_TYPES, weights=REPEAT_TYPE_WEIGHTS)[0]
        term = random.choices(TERMS, weights=TERM_WEIGHTS)[0]
        fico_band = random.choices(FICO_BANDS, weights=FICO_BAND_WEIGHTS)[0]
        purpose = random.choice(PURPOSES)
        
        # FICO score based on band
        fico = generate_fico_score(fico_band)
        
        # Income based on FICO and grade (higher grade = higher income)
        base_income = {
            "P1": 130000,
            "P2": 105000,
            "P3": 85000,
            "P4": 68000,
            "P5": 52000,
            "P6": 42000
        }[grade]
        income = int(base_income + random.gauss(0, 15000))
        income = max(30000, income)  # Minimum income
        
        # DTI (debt-to-income ratio) - lower for better grades
        base_dti = {
            "P1": 0.25,
            "P2": 0.28,
            "P3": 0.32,
            "P4": 0.36,
            "P5": 0.40,
            "P6": 0.43
        }[grade]
        dti = base_dti + random.gauss(0, 0.05)
        dti = max(0.10, min(0.50, dti))
        
        # Loan amount based on grade and income
        base_amount = {
            "P1": 35000,
            "P2": 28000,
            "P3": 22000,
            "P4": 17000,
            "P5": 12000,
            "P6": 8000
        }[grade]
        submit_amnt = base_amount + random.gauss(0, 5000)
        submit_amnt = max(5000, submit_amnt)
        
        # APR and interest rate based on grade and FICO
        base_apr = {
            "P1": 6.5,
            "P2": 9.5,
            "P3": 12.5,
            "P4": 16.5,
            "P5": 20.5,
            "P6": 24.5
        }[grade]
        # Adjust by FICO
        if fico >= 760:
            base_apr -= 1.5
        elif fico >= 700:
            base_apr -= 0.5
        elif fico < 640:
            base_apr += 2.0
        
        offer_apr = base_apr + random.gauss(0, 1.0)
        offer_apr = max(5.0, min(35.0, offer_apr))
        interest_rate = offer_apr + random.uniform(-0.3, 0.3)
        
        # Origination fee (1-5% of loan amount)
        origination_fee = submit_amnt * random.uniform(0.01, 0.05)
        
        # Flags and progression logic
        offered_flag = 1
        website_complete_flag = 1 if random.random() < 0.88 else 0
        
        # Submission date (0-3 days after create if website complete)
        submit_date = None
        if website_complete_flag:
            submit_date = create_date + timedelta(days=random.randint(0, 3))
        
        # Approval logic
        cr_appr_flag = 0
        approved_date = None
        approved_amnt = None
        if submit_date:
            approval_prob = calculate_approval_probability(grade, fico, channel)
            if random.random() < approval_prob:
                cr_appr_flag = 1
                approved_date = submit_date + timedelta(days=random.randint(1, 4))
                # Approved amount is usually same or slightly less
                approved_amnt = submit_amnt * random.uniform(0.95, 1.0)
        
        # Issuance logic
        issued_flag = 0
        issued_date = None
        issued_amnt = None
        if cr_appr_flag:
            issuance_prob = calculate_issuance_probability(grade, fico)
            if random.random() < issuance_prob:
                issued_flag = 1
                issued_date = approved_date + timedelta(days=random.randint(1, 7))
                issued_amnt = approved_amnt
        
        records.append((
            loan_id,
            create_date.strftime("%Y-%m-%d"),
            prod_type,
            repeat_type,
            channel,
            grade,
            term,
            offered_flag,
            website_complete_flag,
            submit_date.strftime("%Y-%m-%d") if submit_date else None,
            round(submit_amnt, 2) if submit_date else None,
            cr_appr_flag,
            approved_date.strftime("%Y-%m-%d") if approved_date else None,
            round(approved_amnt, 2) if approved_amnt else None,
            issued_flag,
            issued_date.strftime("%Y-%m-%d") if issued_date else None,
            round(issued_amnt, 2) if issued_amnt else None,
            fico,
            fico_band,
            income,
            round(dti, 3),
            purpose,
            round(interest_rate, 2),
            round(offer_apr, 2),
            round(origination_fee, 2)
        ))
        
        # Progress indicator
        if (i + 1) % 200 == 0:
            print(f"  Generated {i + 1}/{num_records} records...")
    
    # Insert all records
    cursor.executemany("""
        INSERT INTO cps_tb (
            loan_id, app_create_d, prod_type, repeat_type, channel, grade, term,
            offered_flag, website_complete_flag, app_submit_d, app_submit_amnt,
            cr_appr_flag, apps_approved_d, apps_approved_amnt, issued_flag,
            issued_d, issued_amnt, cr_fico, cr_fico_band, a_income, cr_dti,
            purpose, interest_rate, offer_apr, origination_fee
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, records)
    
    conn.commit()
    print(f"✓ Generated {num_records} records in cps_tb")


def generate_forecast_df_data(conn: sqlite3.Connection):
    """
    Generate sample forecast data with realistic variances.
    
    Generates weekly forecast data for last 6 months with:
    - Forecast predictions
    - Outlook adjustments
    - Actual results with variances
    """
    cursor = conn.cursor()
    
    # Generate weekly forecast data for last 6 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    # Round to Monday
    start_date = start_date - timedelta(days=start_date.weekday())
    
    records = []
    current_date = start_date
    week_count = 0
    
    print("Generating forecast_df records...")
    
    # Generate for major combinations only (to keep it manageable)
    major_channels = ["OMB", "Email", "Search", "D2LC"]
    major_grades = ["P2", "P3", "P4"]
    major_prod_types = ["Prime", "NP"]
    major_repeat_types = ["Repeat", "New"]
    major_terms = [36, 60]
    
    while current_date <= end_date:
        week_count += 1
        
        for prod_type in major_prod_types:
            for repeat_type in major_repeat_types:
                for channel in major_channels:
                    for grade in major_grades:
                        for term in major_terms:
                            # Base volumes (vary by segment)
                            channel_multiplier = {
                                "OMB": 1.5,
                                "Email": 1.2,
                                "Search": 1.0,
                                "D2LC": 0.8
                            }[channel]
                            
                            grade_multiplier = {
                                "P2": 1.2,
                                "P3": 1.5,
                                "P4": 1.3
                            }[grade]
                            
                            base_volume = 50 * channel_multiplier * grade_multiplier
                            
                            # Add weekly seasonality (higher on certain weeks)
                            if week_count % 4 == 1:  # First week of month
                                base_volume *= 1.2
                            
                            # Forecast values
                            forecast_submits = base_volume * random.uniform(0.9, 1.1)
                            forecast_approved = forecast_submits * random.uniform(0.60, 0.75)
                            forecast_issuance = forecast_approved * random.uniform(0.65, 0.80)
                            
                            # Outlook (mid-period adjustment, closer to actuals)
                            outlook_submits = forecast_submits * random.uniform(0.95, 1.05)
                            outlook_approved = forecast_approved * random.uniform(0.95, 1.05)
                            outlook_issuance = forecast_issuance * random.uniform(0.95, 1.05)
                            
                            # Actuals with realistic variance
                            # Some segments consistently over/under-perform
                            if channel == "OMB" and grade == "P3":
                                # OMB P3 tends to over-perform
                                variance_factor = random.uniform(1.05, 1.20)
                            elif channel == "D2LC":
                                # D2LC tends to under-perform
                                variance_factor = random.uniform(0.85, 0.95)
                            else:
                                # Normal variance
                                variance_factor = random.uniform(0.90, 1.10)
                            
                            actual_submits = forecast_submits * variance_factor
                            actual_approved = forecast_approved * variance_factor * random.uniform(0.95, 1.05)
                            actual_issuance = forecast_issuance * variance_factor * random.uniform(0.95, 1.05)
                            
                            records.append((
                                current_date.strftime("%Y-%m-%d"),
                                prod_type,
                                repeat_type,
                                channel,
                                grade,
                                term,
                                round(forecast_submits, 2),
                                round(forecast_approved, 2),
                                round(forecast_issuance, 2),
                                round(outlook_submits, 2),
                                round(outlook_approved, 2),
                                round(outlook_issuance, 2),
                                round(actual_submits, 2),
                                round(actual_approved, 2),
                                round(actual_issuance, 2)
                            ))
        
        current_date += timedelta(days=7)
        
        if week_count % 4 == 0:
            print(f"  Generated {week_count} weeks of forecast data...")
    
    # Insert all records
    cursor.executemany("""
        INSERT OR REPLACE INTO forecast_df (
            date, prod_type, repeat_type, channel, grade, term,
            forecast_app_submits, forecast_apps_approved, forecast_issuance,
            outlook_app_submits, outlook_apps_approved, outlook_issuance,
            actual_app_submits, actual_apps_approved, actual_issuance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, records)
    
    conn.commit()
    print(f"✓ Generated {len(records)} records in forecast_df ({week_count} weeks)")


def print_summary_statistics(conn: sqlite3.Connection):
    """Print summary statistics of generated data."""
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("DATA GENERATION SUMMARY")
    print("="*60)
    
    # cps_tb statistics
    cursor.execute("SELECT COUNT(*) FROM cps_tb")
    total_records = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM cps_tb WHERE app_submit_d IS NOT NULL")
    submitted = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM cps_tb WHERE cr_appr_flag = 1")
    approved = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM cps_tb WHERE issued_flag = 1")
    issued = cursor.fetchone()[0]
    
    cursor.execute("SELECT MIN(app_create_d), MAX(app_create_d) FROM cps_tb")
    min_date, max_date = cursor.fetchone()
    
    print(f"\ncps_tb Table:")
    print(f"  Total records: {total_records:,}")
    print(f"  Submitted: {submitted:,} ({submitted/total_records*100:.1f}%)")
    print(f"  Approved: {approved:,} ({approved/submitted*100:.1f}% of submitted)")
    print(f"  Issued: {issued:,} ({issued/approved*100:.1f}% of approved)")
    print(f"  Date range: {min_date} to {max_date}")
    
    # Channel distribution
    cursor.execute("""
        SELECT channel, COUNT(*) as cnt 
        FROM cps_tb 
        GROUP BY channel 
        ORDER BY cnt DESC 
        LIMIT 5
    """)
    print(f"\n  Top 5 Channels:")
    for channel, cnt in cursor.fetchall():
        print(f"    {channel}: {cnt:,}")
    
    # Grade distribution
    cursor.execute("""
        SELECT grade, COUNT(*) as cnt 
        FROM cps_tb 
        GROUP BY grade 
        ORDER BY grade
    """)
    print(f"\n  Grade Distribution:")
    for grade, cnt in cursor.fetchall():
        print(f"    {grade}: {cnt:,}")
    
    # forecast_df statistics
    cursor.execute("SELECT COUNT(*) FROM forecast_df")
    forecast_records = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT date) FROM forecast_df")
    forecast_weeks = cursor.fetchone()[0]
    
    cursor.execute("SELECT MIN(date), MAX(date) FROM forecast_df")
    min_date, max_date = cursor.fetchone()
    
    print(f"\nforecast_df Table:")
    print(f"  Total records: {forecast_records:,}")
    print(f"  Weeks covered: {forecast_weeks}")
    print(f"  Date range: {min_date} to {max_date}")
    
    # Forecast accuracy
    cursor.execute("""
        SELECT 
            AVG(ABS(actual_issuance - forecast_issuance) / NULLIF(forecast_issuance, 0)) * 100 as mape
        FROM forecast_df
        WHERE forecast_issuance > 0
    """)
    mape = cursor.fetchone()[0]
    print(f"  Average forecast error (MAPE): {mape:.1f}%")
    
    print("\n" + "="*60)
    print("✓ Data generation complete!")
    print("="*60 + "\n")


def main():
    """Main function to generate sample data."""
    print("\n" + "="*60)
    print("TOPUP SAMPLE DATA GENERATOR")
    print("="*60 + "\n")
    
    # Get database path
    db_path = get_database_path()
    print(f"Database path: {db_path}\n")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    try:
        # Create tables
        create_tables(conn)
        
        # Clear existing data
        clear_existing_data(conn)
        
        # Generate cps_tb data (1200 records for good variety)
        generate_cps_tb_data(conn, num_records=1200)
        
        # Generate forecast_df data
        generate_forecast_df_data(conn)
        
        # Print summary
        print_summary_statistics(conn)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
