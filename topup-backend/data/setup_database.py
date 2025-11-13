"""
Database setup script for Topup CXO Assistant.
Creates SQLite database with sample data for testing.
"""

import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path


def create_database(db_path: str = "./data/topup.db"):
    """Create SQLite database with cps_tb and forecast_df tables."""
    
    # Ensure data directory exists
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
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
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_forecast_date ON forecast_df(date)")
    
    conn.commit()
    return conn


def generate_sample_data(conn: sqlite3.Connection, num_records: int = 1500):
    """Generate sample data for cps_tb table."""
    
    cursor = conn.cursor()
    
    # Configuration
    channels = ["OMB", "Email", "Search", "D2LC", "DM", "LT", "Experian", "Karma", "Small Partners"]
    grades = ["P1", "P2", "P3", "P4", "P5", "P6"]
    prod_types = ["Prime", "NP", "D2P"]
    repeat_types = ["Repeat", "New"]
    terms = [36, 48, 60, 72, 84]
    fico_bands = ["<640", "640-699", "700-759", "760+"]
    purposes = ["debt_consolidation", "home_improvement", "major_purchase", "medical", "car", "other"]
    
    # Generate data for last 6 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    records = []
    
    for loan_id in range(1, num_records + 1):
        # Random application create date
        days_offset = random.randint(0, 180)
        create_date = start_date + timedelta(days=days_offset)
        
        # Random attributes
        channel = random.choice(channels)
        grade = random.choice(grades)
        prod_type = random.choice(prod_types)
        repeat_type = random.choice(repeat_types)
        term = random.choice(terms)
        fico_band = random.choice(fico_bands)
        purpose = random.choice(purposes)
        
        # FICO score based on band
        if fico_band == "<640":
            fico = random.randint(550, 639)
        elif fico_band == "640-699":
            fico = random.randint(640, 699)
        elif fico_band == "700-759":
            fico = random.randint(700, 759)
        else:
            fico = random.randint(760, 850)
        
        # Income based on FICO and grade
        base_income = {"P1": 120000, "P2": 100000, "P3": 80000, "P4": 65000, "P5": 50000, "P6": 40000}
        income = base_income[grade] + random.randint(-15000, 15000)
        
        # DTI (debt-to-income ratio)
        dti = random.uniform(0.15, 0.45)
        
        # Loan amount based on grade
        base_amount = {"P1": 30000, "P2": 25000, "P3": 20000, "P4": 15000, "P5": 10000, "P6": 7500}
        submit_amnt = base_amount[grade] + random.randint(-5000, 5000)
        
        # APR and interest rate based on grade and FICO
        base_apr = {"P1": 6.5, "P2": 9.5, "P3": 12.5, "P4": 16.5, "P5": 20.5, "P6": 24.5}
        offer_apr = base_apr[grade] + random.uniform(-2, 2)
        interest_rate = offer_apr + random.uniform(-0.5, 0.5)
        
        # Origination fee (1-5% of loan amount)
        origination_fee = submit_amnt * random.uniform(0.01, 0.05)
        
        # Flags and approval logic
        offered_flag = 1
        website_complete_flag = 1 if random.random() < 0.85 else 0
        
        # Submission date (0-2 days after create if website complete)
        submit_date = None
        if website_complete_flag:
            submit_date = create_date + timedelta(days=random.randint(0, 2))
        
        # Approval rate varies by grade and FICO
        approval_prob = 0.7 if fico >= 700 else 0.5
        if grade in ["P4", "P5"]:
            approval_prob -= 0.1
        
        cr_appr_flag = 0
        approved_date = None
        approved_amnt = None
        if submit_date and random.random() < approval_prob:
            cr_appr_flag = 1
            approved_date = submit_date + timedelta(days=random.randint(1, 3))
            approved_amnt = submit_amnt * random.uniform(0.9, 1.0)
        
        # Issuance logic (70% of approved get issued)
        issued_flag = 0
        issued_date = None
        issued_amnt = None
        if cr_appr_flag and random.random() < 0.7:
            issued_flag = 1
            issued_date = approved_date + timedelta(days=random.randint(1, 5))
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
            submit_amnt if submit_date else None,
            cr_appr_flag,
            approved_date.strftime("%Y-%m-%d") if approved_date else None,
            approved_amnt,
            issued_flag,
            issued_date.strftime("%Y-%m-%d") if issued_date else None,
            issued_amnt,
            fico,
            fico_band,
            income,
            dti,
            purpose,
            interest_rate,
            offer_apr,
            origination_fee
        ))
    
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


def generate_forecast_data(conn: sqlite3.Connection):
    """Generate sample forecast data."""
    
    cursor = conn.cursor()
    
    channels = ["OMB", "Email", "Search", "D2LC", "DM", "LT", "Experian", "Karma", "Small Partners"]
    grades = ["P1", "P2", "P3", "P4", "P5", "P6"]
    prod_types = ["Prime", "NP", "D2P"]
    repeat_types = ["Repeat", "New"]
    terms = [36, 48, 60, 72, 84]
    
    # Generate weekly forecast data for last 3 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    records = []
    current_date = start_date
    
    while current_date <= end_date:
        for prod_type in prod_types:
            for repeat_type in repeat_types:
                for channel in channels:
                    for grade in grades:
                        for term in terms:
                            # Base forecasts
                            base_submits = random.uniform(10, 50)
                            base_approved = base_submits * random.uniform(0.5, 0.7)
                            base_issuance = base_approved * random.uniform(0.6, 0.8)
                            
                            # Outlook (slightly different from forecast)
                            outlook_submits = base_submits * random.uniform(0.95, 1.05)
                            outlook_approved = base_approved * random.uniform(0.95, 1.05)
                            outlook_issuance = base_issuance * random.uniform(0.95, 1.05)
                            
                            # Actuals with variance
                            actual_submits = base_submits * random.uniform(0.85, 1.15)
                            actual_approved = base_approved * random.uniform(0.85, 1.15)
                            actual_issuance = base_issuance * random.uniform(0.85, 1.15)
                            
                            records.append((
                                current_date.strftime("%Y-%m-%d"),
                                prod_type,
                                repeat_type,
                                channel,
                                grade,
                                term,
                                base_submits,
                                base_approved,
                                base_issuance,
                                outlook_submits,
                                outlook_approved,
                                outlook_issuance,
                                actual_submits,
                                actual_approved,
                                actual_issuance
                            ))
        
        current_date += timedelta(days=7)
    
    cursor.executemany("""
        INSERT INTO forecast_df (
            date, prod_type, repeat_type, channel, grade, term,
            forecast_app_submits, forecast_apps_approved, forecast_issuance,
            outlook_app_submits, outlook_apps_approved, outlook_issuance,
            actual_app_submits, actual_apps_approved, actual_issuance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, records)
    
    conn.commit()
    print(f"✓ Generated {len(records)} records in forecast_df")


if __name__ == "__main__":
    print("Setting up Topup database...")
    conn = create_database()
    generate_sample_data(conn, num_records=1500)
    generate_forecast_data(conn)
    conn.close()
    print("✓ Database setup complete!")
