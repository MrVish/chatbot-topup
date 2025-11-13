# Scripts Directory

This directory contains utility scripts for the Topup CXO Assistant backend.

## Available Scripts

### generate_sample_data.py

Generates realistic sample data for testing the Topup system.

**Features:**
- Generates 1200+ rows of `cps_tb` data with realistic distributions
- Generates 100+ rows of `forecast_df` data with forecast vs actual variances
- Data covers last 6 months for testing time windows
- Includes variety of channels, grades, FICO bands, and other segments
- Realistic approval and issuance rates based on grade and FICO
- Forecast data includes intentional variances for testing accuracy metrics

**Usage:**
```bash
# From workspace root
python topup-backend/scripts/generate_sample_data.py

# Or from backend directory
cd topup-backend
python scripts/generate_sample_data.py
```

**Output:**
- Creates/updates `topup-backend/data/topup.db`
- Clears existing data before generating new data
- Prints summary statistics including:
  - Total records generated
  - Approval and issuance rates
  - Date range coverage
  - Channel and grade distributions
  - Forecast accuracy metrics

**Data Characteristics:**

*cps_tb Table:*
- 1200 loan records
- ~88% submission rate (website complete)
- ~72% approval rate (varies by grade and FICO)
- ~79% issuance rate (of approved loans)
- Realistic distributions:
  - Channels: OMB and Email most common
  - Grades: P3 and P4 most common
  - FICO: 700-759 most common
  - Terms: 60-month most common

*forecast_df Table:*
- 2500+ forecast records
- 27 weeks of data (last 6 months)
- Weekly granularity
- Major segment combinations (channels, grades, terms)
- Average forecast error (MAPE): ~7%
- Realistic variances:
  - OMB P3 tends to over-perform
  - D2LC tends to under-perform
  - Normal variance: ±10%

### verify_data.py

Quick verification script to check generated data.

**Usage:**
```bash
python topup-backend/scripts/verify_data.py
```

**Output:**
- Sample records from cps_tb
- Sample forecast vs actual comparisons
- Date range coverage
- Data quality checks

## Requirements

These scripts require the following Python packages (already in requirements.txt):
- sqlite3 (built-in)
- random (built-in)
- datetime (built-in)

## Notes

- The scripts automatically detect the database path
- Data is cleared before generation to ensure clean state
- All monetary values are rounded to 2 decimal places
- Dates are formatted as YYYY-MM-DD for SQLite compatibility
- Indexes are created automatically for query performance
