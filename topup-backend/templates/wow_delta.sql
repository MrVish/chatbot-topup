-- Week-over-Week delta comparison
-- Parameters: :metric, :date_col, :channel, :grade, :prod_type, :repeat_type, :term, :cr_fico_band, :purpose

WITH weekly_data AS (
    SELECT 
        strftime('%Y-%W', {date_col}) AS week,
        strftime('%Y-%m-%d', {date_col}, 'weekday 0', '-6 days') AS week_start,
        {metric_expression} AS metric_value
    FROM cps_tb
    WHERE {date_col} >= date('now', '-12 weeks')
        AND {date_col} <= date('now')
        AND {date_col} IS NOT NULL
        {channel_filter}
        {grade_filter}
        {prod_type_filter}
        {repeat_type_filter}
        {term_filter}
        {fico_band_filter}
        {purpose_filter}
    GROUP BY strftime('%Y-%W', {date_col})
),
lagged_data AS (
    SELECT
        week,
        week_start,
        metric_value,
        LAG(metric_value, 1) OVER (ORDER BY week) AS prior_week_value
    FROM weekly_data
)
SELECT
    week,
    week_start,
    metric_value AS current_value,
    prior_week_value,
    metric_value - prior_week_value AS delta,
    ROUND(
        (metric_value - prior_week_value) / NULLIF(prior_week_value, 0) * 100,
        2
    ) AS delta_pct
FROM lagged_data
WHERE prior_week_value IS NOT NULL
ORDER BY week DESC
LIMIT 10000;
