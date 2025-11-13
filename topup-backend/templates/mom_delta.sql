-- Month-over-Month delta comparison
-- Parameters: :metric, :date_col, :channel, :grade, :prod_type, :repeat_type, :term, :cr_fico_band, :purpose

WITH monthly_data AS (
    SELECT 
        strftime('%Y-%m', {date_col}) AS month,
        {metric_expression} AS metric_value
    FROM cps_tb
    WHERE {date_col} >= date('now', 'start of month', '-3 months')
        AND {date_col} < date('now', 'start of month')
        AND {date_col} IS NOT NULL
        {channel_filter}
        {grade_filter}
        {prod_type_filter}
        {repeat_type_filter}
        {term_filter}
        {fico_band_filter}
        {purpose_filter}
    GROUP BY strftime('%Y-%m', {date_col})
),
lagged_data AS (
    SELECT
        month,
        metric_value,
        LAG(metric_value, 1) OVER (ORDER BY month) AS prior_month_value
    FROM monthly_data
)
SELECT
    month,
    metric_value AS current_value,
    prior_month_value,
    metric_value - prior_month_value AS delta,
    ROUND(
        (metric_value - prior_month_value) / NULLIF(prior_month_value, 0) * 100,
        2
    ) AS delta_pct
FROM lagged_data
WHERE prior_month_value IS NOT NULL
ORDER BY month DESC
LIMIT 10000;
