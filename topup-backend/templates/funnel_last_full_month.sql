-- Funnel analysis for submission → approval → issuance
-- Parameters: :start_date, :end_date, :channel, :grade, :prod_type, :repeat_type, :term, :cr_fico_band, :purpose

WITH funnel_data AS (
    SELECT
        -- Submissions (amount by default)
        SUM(CASE WHEN app_submit_d BETWEEN :start_date AND :end_date THEN app_submit_amnt ELSE 0 END) AS submissions_amt,
        COUNT(CASE WHEN app_submit_d BETWEEN :start_date AND :end_date THEN 1 END) AS submissions_count,
        
        -- Approvals (amount by default)
        SUM(CASE WHEN apps_approved_d BETWEEN :start_date AND :end_date AND cr_appr_flag = 1 THEN apps_approved_amnt ELSE 0 END) AS approvals_amt,
        SUM(CASE WHEN apps_approved_d BETWEEN :start_date AND :end_date THEN cr_appr_flag END) AS approvals_count,
        
        -- Issuances (amount by default)
        SUM(CASE WHEN issued_d BETWEEN :start_date AND :end_date AND issued_flag = 1 THEN issued_amnt ELSE 0 END) AS issuances_amt,
        SUM(CASE WHEN issued_d BETWEEN :start_date AND :end_date THEN issued_flag END) AS issuances_count
    FROM cps_tb
    WHERE 1=1
        {channel_filter}
        {grade_filter}
        {prod_type_filter}
        {repeat_type_filter}
        {term_filter}
        {fico_band_filter}
        {purpose_filter}
)
SELECT
    'Submissions' AS stage,
    1 AS stage_order,
    submissions_amt AS value_amt,
    submissions_count AS value_count,
    100.0 AS conversion_rate
FROM funnel_data

UNION ALL

SELECT
    'Approvals' AS stage,
    2 AS stage_order,
    approvals_amt AS value_amt,
    approvals_count AS value_count,
    ROUND(approvals_amt / NULLIF(submissions_amt, 0) * 100, 2) AS conversion_rate
FROM funnel_data

UNION ALL

SELECT
    'Issuances' AS stage,
    3 AS stage_order,
    issuances_amt AS value_amt,
    issuances_count AS value_count,
    ROUND(issuances_amt / NULLIF(submissions_amt, 0) * 100, 2) AS conversion_rate
FROM funnel_data

ORDER BY stage_order;
