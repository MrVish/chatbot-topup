# Data Directory

This directory contains the SQLite database and setup scripts for the Topup CXO Assistant.

## Files

- `topup.db` - SQLite database with sample data (created by setup_database.py)
- `setup_database.py` - Script to create and populate the database
- `verify_database.py` - Script to verify database contents
- `test_templates.py` - Script to test SQL templates
- `chroma/` - Chroma vector database for RAG (created in task 11)

## Database Schema

### cps_tb (Customer Acquisition Table)

Contains customer acquisition data with application creation, submission, approval, and issuance information.

**Columns:**
- `loan_id` - Primary key (unique loan identifier)
- `app_create_d` - Application creation date
- `prod_type` - Product type (Prime, NP, D2P)
- `repeat_type` - Customer type (Repeat, New)
- `channel` - Marketing channel (OMB, Email, Search, D2LC, DM, LT, Experian, Karma, Small Partners)
- `grade` - Credit grade (P1, P2, P3, P4, P5, P6)
- `term` - Loan term in months (36, 48, 60, 72, 84)
- `offered_flag` - Offer flag (0/1)
- `website_complete_flag` - Website completion flag (0/1)
- `app_submit_d` - Application submission date
- `app_submit_amnt` - Submitted loan amount
- `cr_appr_flag` - Approval flag (0/1)
- `apps_approved_d` - Application approval date
- `apps_approved_amnt` - Approved loan amount
- `issued_flag` - Issuance flag (0/1)
- `issued_d` - Loan issuance date
- `issued_amnt` - Issued loan amount
- `cr_fico` - FICO credit score
- `cr_fico_band` - FICO band (<640, 640-699, 700-759, 760+)
- `a_income` - Annual income
- `cr_dti` - Debt-to-income ratio
- `purpose` - Loan purpose (debt_consolidation, home_improvement, major_purchase, medical, car, other)
- `interest_rate` - Interest rate percentage
- `offer_apr` - Offered APR percentage
- `origination_fee` - Origination fee amount

**Indexes:**
- `idx_cps_create_d` on `app_create_d`
- `idx_cps_submit_d` on `app_submit_d`
- `idx_cps_approved_d` on `apps_approved_d`
- `idx_cps_issued_d` on `issued_d`
- `idx_cps_channel` on `channel`
- `idx_cps_grade` on `grade`
- `idx_cps_prod_type` on `prod_type`

### forecast_df (Forecast Table)

Contains forecast, outlook, and actual data for submissions, approvals, and issuances.

**Columns:**
- `date` - Forecast date (part of composite primary key)
- `prod_type` - Product type (part of composite primary key)
- `repeat_type` - Customer type (part of composite primary key)
- `channel` - Marketing channel (part of composite primary key)
- `grade` - Credit grade (part of composite primary key)
- `term` - Loan term (part of composite primary key)
- `forecast_app_submits` - Forecasted application submissions
- `forecast_apps_approved` - Forecasted approvals
- `forecast_issuance` - Forecasted issuances
- `outlook_app_submits` - Outlook application submissions
- `outlook_apps_approved` - Outlook approvals
- `outlook_issuance` - Outlook issuances
- `actual_app_submits` - Actual application submissions
- `actual_apps_approved` - Actual approvals
- `actual_issuance` - Actual issuances

**Primary Key:** Composite key on (date, prod_type, repeat_type, channel, grade, term)

**Indexes:**
- `idx_forecast_date` on `date`

## Sample Data

The database is populated with:
- **1,500 records** in `cps_tb` covering the last 6 months
- **21,060 records** in `forecast_df` covering the last 3 months (13 weeks × 1,620 segment combinations)

Data includes realistic distributions across:
- 9 channels (OMB, Email, Search, D2LC, DM, LT, Experian, Karma, Small Partners)
- 6 grades (P1-P6)
- 3 product types (Prime, NP, D2P)
- 2 repeat types (Repeat, New)
- 5 loan terms (36, 48, 60, 72, 84 months)
- 4 FICO bands (<640, 640-699, 700-759, 760+)
- 6 loan purposes (debt_consolidation, home_improvement, major_purchase, medical, car, other)

## Setup Instructions

### Initial Setup

```bash
# From topup-backend directory
python data/setup_database.py
```

This will:
1. Create `data/topup.db` SQLite database
2. Create `cps_tb` and `forecast_df` tables
3. Create indexes for performance
4. Generate 1,500 sample records in `cps_tb`
5. Generate 21,060 sample records in `forecast_df`

### Verify Setup

```bash
python data/verify_database.py
```

This will display:
- Row counts for each table
- Sample data from each table
- Date ranges
- Segment distributions

### Test SQL Templates

```bash
python data/test_templates.py
```

This will test all SQL templates in the `templates/` directory.

## Regenerating Data

To regenerate the database with fresh sample data:

```bash
# Delete existing database
rm data/topup.db

# Run setup again
python data/setup_database.py
```

## Database Access

The database is configured for **read-only access** in production:

```python
import sqlite3

# Open in read-only mode
conn = sqlite3.connect('data/topup.db', uri=True)
conn.execute("PRAGMA query_only = ON")
```

This prevents accidental data modification through SQL injection or other means.

## Performance Considerations

- All date columns are indexed for fast filtering
- Channel and grade columns are indexed for segment filtering
- Row limit of 10,000 enforced in all SQL templates
- Pre-aggregated views can be added for frequently accessed queries

## Future Enhancements

- Add materialized views for common aggregations
- Implement incremental data loading
- Add data validation constraints
- Create backup/restore scripts
