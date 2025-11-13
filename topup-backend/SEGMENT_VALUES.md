# Segment Values Reference

This document lists all valid segment values used in the Topup CXO Assistant database.

## Channels (9 total)

Marketing channels for customer acquisition:

1. **OMB** - Online Marketing/Brand
2. **Email** - Email marketing campaigns
3. **Search** - Search engine marketing
4. **D2LC** - Direct to Lending Club
5. **DM** - Direct Mail
6. **LT** - Lending Tree
7. **Experian** - Experian partnership
8. **Karma** - Credit Karma partnership
9. **Small Partners** - Small partner channels

## Grades (6 total)

Credit risk grades from best to worst:

1. **P1** - Prime tier 1 (best credit)
2. **P2** - Prime tier 2
3. **P3** - Prime tier 3
4. **P4** - Prime tier 4
5. **P5** - Prime tier 5
6. **P6** - Prime tier 6 (highest risk)

### Grade Characteristics

| Grade | Avg Income | Avg Loan Amount | Base APR |
|-------|-----------|-----------------|----------|
| P1    | $120,000  | $30,000        | 6.5%     |
| P2    | $100,000  | $25,000        | 9.5%     |
| P3    | $80,000   | $20,000        | 12.5%    |
| P4    | $65,000   | $15,000        | 16.5%    |
| P5    | $50,000   | $10,000        | 20.5%    |
| P6    | $40,000   | $7,500         | 24.5%    |

## Terms (5 total)

Loan term lengths in months:

1. **36** - 3 years
2. **48** - 4 years
3. **60** - 5 years
4. **72** - 6 years
5. **84** - 7 years

## Product Types (3 total)

Loan product categories:

1. **Prime** - Prime lending products
2. **NP** - Near-prime products
3. **D2P** - Direct-to-prime products

## Repeat Types (2 total)

Customer acquisition type:

1. **Repeat** - Returning customers
2. **New** - New customers

## FICO Bands (4 total)

Credit score ranges:

1. **<640** - Below 640 (subprime)
2. **640-699** - 640 to 699 (near-prime)
3. **700-759** - 700 to 759 (prime)
4. **760+** - 760 and above (super-prime)

## Loan Purposes (6 total)

Reasons for loan application:

1. **debt_consolidation** - Consolidating existing debt
2. **home_improvement** - Home renovation/improvement
3. **major_purchase** - Large purchases (furniture, appliances, etc.)
4. **medical** - Medical expenses
5. **car** - Vehicle purchase or repair
6. **other** - Other purposes

## Segment Combinations

### cps_tb Table
- Total possible combinations: 9 channels × 6 grades × 5 terms × 3 prod_types × 2 repeat_types × 6 purposes = **9,720 combinations**
- Actual records: 1,500 (sample subset)

### forecast_df Table
- Total combinations per week: 9 channels × 6 grades × 5 terms × 3 prod_types × 2 repeat_types = **1,620 combinations**
- Weeks of data: 13 weeks
- Total records: **21,060 records**

## Usage in Filters

When filtering data, use these exact values:

```python
# Example filter
filters = {
    "channel": "Email",           # Must match exactly
    "grade": "P1",                # Case-sensitive
    "term": 60,                   # Integer
    "prod_type": "Prime",         # Must match exactly
    "repeat_type": "New",         # Must match exactly
    "cr_fico_band": "700-759",    # Must match exactly
    "purpose": "debt_consolidation"  # Underscore, not space
}
```

## SQL Filter Examples

```sql
-- Filter by channel
WHERE channel = 'Email'

-- Filter by grade
WHERE grade IN ('P1', 'P2', 'P3')

-- Filter by term
WHERE term = 60

-- Filter by product type
WHERE prod_type = 'Prime'

-- Filter by repeat type
WHERE repeat_type = 'New'

-- Filter by FICO band
WHERE cr_fico_band = '700-759'

-- Filter by purpose
WHERE purpose = 'debt_consolidation'

-- Multiple filters
WHERE channel = 'Email'
  AND grade = 'P1'
  AND term = 60
  AND prod_type = 'Prime'
  AND repeat_type = 'New'
```

## Validation

To verify all segment values are present in the database:

```bash
python data/verify_segments.py
```

This will check:
- All 9 channels are present
- All 6 grades are present
- All 5 terms are present
- All 3 product types are present
- All 2 repeat types are present
- forecast_df has complete coverage (21,060 records)
