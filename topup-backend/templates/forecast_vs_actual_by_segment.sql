-- Forecast vs Actual comparison by segment (grade, channel, etc.)
-- Shows all three metrics (submits, approvals, issuance) broken down by the segment
-- Parameters: :start_date, :end_date, segment dimension

SELECT 
    {segment_by} AS segment,
    SUM(forecast_app_submits) AS forecast_app_submits,
    SUM(actual_app_submits) AS actual_app_submits,
    SUM(actual_app_submits) - SUM(forecast_app_submits) AS delta_app_submits,
    ROUND(
        CAST(SUM(actual_app_submits) AS REAL) / NULLIF(SUM(forecast_app_submits), 0) * 100, 
        2
    ) AS accuracy_app_submits_pct,
    
    SUM(forecast_apps_approved) AS forecast_apps_approved,
    SUM(actual_apps_approved) AS actual_apps_approved,
    SUM(actual_apps_approved) - SUM(forecast_apps_approved) AS delta_apps_approved,
    ROUND(
        CAST(SUM(actual_apps_approved) AS REAL) / NULLIF(SUM(forecast_apps_approved), 0) * 100, 
        2
    ) AS accuracy_apps_approved_pct,
    
    SUM(forecast_issuance) AS forecast_issuance,
    SUM(actual_issuance) AS actual_issuance,
    SUM(actual_issuance) - SUM(forecast_issuance) AS delta_issuance,
    ROUND(
        CAST(SUM(actual_issuance) AS REAL) / NULLIF(SUM(forecast_issuance), 0) * 100, 
        2
    ) AS accuracy_issuance_pct
FROM forecast_df
WHERE date BETWEEN :start_date AND :end_date
    AND date IS NOT NULL
    {channel_filter}
    {grade_filter}
    {prod_type_filter}
    {repeat_type_filter}
    {term_filter}
GROUP BY {segment_by}
ORDER BY segment
LIMIT 10000;
