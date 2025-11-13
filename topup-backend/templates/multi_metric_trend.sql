-- Multi-metric trend analysis for comparing multiple metrics over time
-- Each metric uses its appropriate date column
-- Parameters: :start_date, :end_date, filters

WITH 
-- App Submits by submission date
app_submits AS (
    SELECT
        DATE(app_submit_d) as period,
        SUM(app_submit_amnt) as app_submit_amnt,
        COUNT(app_submit_d) as app_submit_count
    FROM cps_tb
    WHERE app_submit_d BETWEEN :start_date AND :end_date
        {channel_filter}
        {grade_filter}
        {prod_type_filter}
        {repeat_type_filter}
        {term_filter}
        {fico_band_filter}
        {purpose_filter}
    GROUP BY DATE(app_submit_d)
),

-- Approvals by approval date
app_approvals AS (
    SELECT
        DATE(apps_approved_d) as period,
        SUM(CASE WHEN cr_appr_flag = 1 THEN apps_approved_amnt ELSE 0 END) as apps_approved_amnt,
        SUM(cr_appr_flag) as apps_approved_count
    FROM cps_tb
    WHERE apps_approved_d BETWEEN :start_date AND :end_date
        AND cr_appr_flag = 1
        {channel_filter}
        {grade_filter}
        {prod_type_filter}
        {repeat_type_filter}
        {term_filter}
        {fico_band_filter}
        {purpose_filter}
    GROUP BY DATE(apps_approved_d)
),

-- Issuances by issuance date
issuances AS (
    SELECT
        DATE(issued_d) as period,
        SUM(CASE WHEN issued_flag = 1 THEN issued_amnt ELSE 0 END) as issued_amnt,
        SUM(issued_flag) as issued_count
    FROM cps_tb
    WHERE issued_d BETWEEN :start_date AND :end_date
        AND issued_flag = 1
        {channel_filter}
        {grade_filter}
        {prod_type_filter}
        {repeat_type_filter}
        {term_filter}
        {fico_band_filter}
        {purpose_filter}
    GROUP BY DATE(issued_d)
),

-- Get all unique periods
all_periods AS (
    SELECT DISTINCT period FROM app_submits
    UNION
    SELECT DISTINCT period FROM app_approvals
    UNION
    SELECT DISTINCT period FROM issuances
),

-- Combine all metrics
daily_metrics AS (
    SELECT
        p.period,
        COALESCE(s.app_submit_amnt, 0) as app_submit_amnt,
        COALESCE(s.app_submit_count, 0) as app_submit_count,
        COALESCE(a.apps_approved_amnt, 0) as apps_approved_amnt,
        COALESCE(a.apps_approved_count, 0) as apps_approved_count,
        COALESCE(i.issued_amnt, 0) as issued_amnt,
        COALESCE(i.issued_count, 0) as issued_count
    FROM all_periods p
    LEFT JOIN app_submits s ON p.period = s.period
    LEFT JOIN app_approvals a ON p.period = a.period
    LEFT JOIN issuances i ON p.period = i.period
),

-- Aggregate by requested granularity
aggregated AS (
    SELECT
        CASE 
            WHEN '{granularity}' = 'daily' THEN period
            WHEN '{granularity}' = 'weekly' THEN DATE(period, 'weekday 0', '-6 days')
            WHEN '{granularity}' = 'monthly' THEN DATE(period, 'start of month')
        END as period,
        
        SUM(app_submit_amnt) as app_submit_amnt,
        SUM(app_submit_count) as app_submit_count,
        SUM(apps_approved_amnt) as apps_approved_amnt,
        SUM(apps_approved_count) as apps_approved_count,
        SUM(issued_amnt) as issued_amnt,
        SUM(issued_count) as issued_count
        
    FROM daily_metrics
    GROUP BY 
        CASE 
            WHEN '{granularity}' = 'daily' THEN period
            WHEN '{granularity}' = 'weekly' THEN DATE(period, 'weekday 0', '-6 days')
            WHEN '{granularity}' = 'monthly' THEN DATE(period, 'start of month')
        END
)

SELECT
    period,
    app_submit_amnt,
    app_submit_count,
    apps_approved_amnt,
    apps_approved_count,
    issued_amnt,
    issued_count
FROM aggregated
WHERE period IS NOT NULL
ORDER BY period ASC;
