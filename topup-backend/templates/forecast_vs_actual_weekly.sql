-- Forecast vs Actual comparison with delta and accuracy
-- Parameters: :start_date, :end_date, :metric_type (submits/approved/issuance), :channel, :grade, :prod_type, :repeat_type, :term

SELECT 
    strftime('%Y-%W', date) AS week,
    strftime('%Y-%m-%d', date, 'weekday 0', '-6 days') AS week_start,
    SUM({forecast_col}) AS forecast_value,
    SUM({outlook_col}) AS outlook_value,
    SUM({actual_col}) AS actual_value,
    SUM({actual_col}) - SUM({forecast_col}) AS delta_vs_forecast,
    SUM({actual_col}) - SUM({outlook_col}) AS delta_vs_outlook,
    ROUND(
        CAST(SUM({actual_col}) AS REAL) / NULLIF(SUM({forecast_col}), 0) * 100, 
        2
    ) AS accuracy_vs_forecast_pct,
    ROUND(
        CAST(SUM({actual_col}) AS REAL) / NULLIF(SUM({outlook_col}), 0) * 100, 
        2
    ) AS accuracy_vs_outlook_pct,
    ROUND(
        CAST(ABS(SUM({actual_col}) - SUM({forecast_col})) AS REAL) / NULLIF(SUM({forecast_col}), 0) * 100,
        2
    ) AS abs_error_vs_forecast_pct,
    ROUND(
        CAST(ABS(SUM({actual_col}) - SUM({outlook_col})) AS REAL) / NULLIF(SUM({outlook_col}), 0) * 100,
        2
    ) AS abs_error_vs_outlook_pct
FROM forecast_df
WHERE date BETWEEN :start_date AND :end_date
    AND date IS NOT NULL
    {channel_filter}
    {grade_filter}
    {prod_type_filter}
    {repeat_type_filter}
    {term_filter}
GROUP BY strftime('%Y-%W', date)
ORDER BY week
LIMIT 10000;
