-- Trend analysis with flexible granularity (daily, weekly, monthly)
-- Parameters: :start_date, :end_date, :metric, :date_col, :channel, :grade, :prod_type, :repeat_type, :term, :cr_fico_band
-- Granularity is controlled by {time_group} and {time_label} placeholders

SELECT 
    {time_group} AS period,
    {time_label} AS period_label,
    {metric_expression} AS metric_value,
    COUNT(*) AS record_count
FROM cps_tb
WHERE {date_col} BETWEEN :start_date AND :end_date
    AND {date_col} IS NOT NULL
    {channel_filter}
    {grade_filter}
    {prod_type_filter}
    {repeat_type_filter}
    {term_filter}
    {fico_band_filter}
    {purpose_filter}
GROUP BY {time_group}
ORDER BY period
LIMIT 10000;
