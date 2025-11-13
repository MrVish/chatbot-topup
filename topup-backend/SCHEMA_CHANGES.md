# Database Schema Changes

This document summarizes the changes made to align the database schema with the provided table structures.

## Changes Summary

### cps_tb Table

**Added Columns:**
- `loan_id` - Primary key (replaces auto-increment id)
- `app_create_d` - Application creation date (new stage in funnel)
- `website_complete_flag` - Tracks website completion
- `a_income` - Annual income
- `cr_dti` - Debt-to-income ratio
- `purpose` - Loan purpose
- `interest_rate` - Interest rate (separate from APR)
- `origination_fee` - Origination fee amount

**Renamed Columns:**
- `app_submit_amt` → `app_submit_amnt`
- `approval_amt` → `apps_approved_amnt`
- `issued_amt` → `issued_amnt`

**Removed Columns:**
- `id` (replaced by loan_id)

**New Indexes:**
- `idx_cps_create_d` on `app_create_d`
- `idx_cps_prod_type` on `prod_type`

### forecast_df Table

**Changed Structure:**
- Removed auto-increment `id` column
- Added composite primary key: (date, prod_type, repeat_type, channel, grade, term)

**Added Columns:**
- `prod_type` - Product type dimension
- `repeat_type` - Customer type dimension
- `term` - Loan term dimension
- `forecast_app_submits` - Forecast for submissions
- `forecast_apps_approved` - Forecast for approvals
- `outlook_app_submits` - Outlook for submissions
- `outlook_apps_approved` - Outlook for approvals
- `outlook_issuance` - Outlook for issuances
- `actual_app_submits` - Actual submissions
- `actual_apps_approved` - Actual approvals
- `actual_issuance` - Actual issuances (renamed from actual_issuance)

**Removed Columns:**
- `id` (replaced by composite primary key)
- Simple `forecast_issuance` and `actual_issuance` (expanded to three metrics)

## SQL Template Updates

All SQL templates have been updated to:

1. Use new column names (`app_submit_amnt`, `apps_approved_amnt`, `issued_amnt`)
2. Support new filter: `{purpose_filter}`
3. Handle new forecast columns (forecast/outlook/actual for submits/approved/issuance)
4. Use proper CAST to REAL for division operations

### Updated Templates:

1. **trend_weekly.sql** - Added purpose_filter support
2. **funnel_last_full_month.sql** - Updated column names, added purpose_filter
3. **forecast_vs_actual_weekly.sql** - Complete rewrite to support forecast/outlook/actual for all three metrics
4. **mom_delta.sql** - Added purpose_filter support
5. **wow_delta.sql** - Added purpose_filter support
6. **distribution.sql** - Added purpose_filter support

## Sample Data Updates

### cps_tb
- 1,500 records with realistic data
- Includes new fields: income, DTI, purpose, origination fees
- Application funnel: Create → Submit → Approve → Issue
- ~86% website completion rate
- ~49% approval rate
- ~72% of approved loans get issued
- 9 channels: OMB, Email, Search, D2LC, DM, LT, Experian, Karma, Small Partners
- 6 grades: P1, P2, P3, P4, P5, P6
- 5 terms: 36, 48, 60, 72, 84 months
- 3 product types: Prime, NP, D2P
- 2 repeat types: Repeat, New

### forecast_df
- 21,060 records (13 weeks × 1,620 segment combinations)
- Segment combinations: 9 channels × 6 grades × 5 terms × 3 prod_types × 2 repeat_types
- Includes forecast, outlook, and actual for all three metrics (submits, approved, issuance)
- Realistic variance between forecast/outlook/actual (±15%)

## Migration Notes

If migrating from old schema:

```sql
-- Rename columns in cps_tb
ALTER TABLE cps_tb RENAME COLUMN app_submit_amt TO app_submit_amnt;
ALTER TABLE cps_tb RENAME COLUMN approval_amt TO apps_approved_amnt;
ALTER TABLE cps_tb RENAME COLUMN issued_amt TO issued_amnt;

-- Add new columns
ALTER TABLE cps_tb ADD COLUMN app_create_d DATE;
ALTER TABLE cps_tb ADD COLUMN website_complete_flag INTEGER;
ALTER TABLE cps_tb ADD COLUMN a_income INTEGER;
ALTER TABLE cps_tb ADD COLUMN cr_dti REAL;
ALTER TABLE cps_tb ADD COLUMN purpose TEXT;
ALTER TABLE cps_tb ADD COLUMN interest_rate REAL;
ALTER TABLE cps_tb ADD COLUMN origination_fee REAL;

-- Recreate forecast_df with new structure
DROP TABLE forecast_df;
-- Run setup_database.py to recreate
```

## Verification

Run the following scripts to verify the changes:

```bash
# Verify database structure and data
python data/verify_database.py

# Test all SQL templates
python data/test_templates.py
```

## Impact on Other Components

### Models (schemas.py)
- ✅ Updated SegmentFilters to include `purpose` field
- ✅ Updated metric description to include new column names
- ✅ Updated date_col to include `app_create_d`

### SQL Tool (Task 4)
- Will need to handle new column names
- Will need to support purpose filter
- Will need to handle forecast/outlook/actual columns

### RAG System (Task 11)
- Documentation should reference new column names
- Examples should use updated schema

### Frontend
- Charts should handle new data structure
- Filters should include purpose dropdown
- Forecast charts should show forecast vs outlook vs actual
