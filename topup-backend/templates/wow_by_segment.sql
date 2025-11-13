-- Week-over-Week comparison by segment
-- Shows current week vs prior week for each segment value
-- Parameters: :metric, :date_col, :segment_col

WITH current_week AS (
    SELECT 
        {segment_col} AS segment,
        {metric_expression} AS current_value
    FROM cps_tb
    WHERE {date_col} >= date('now', '-7 days', 'weekday 0', '-6 days')
        AND {date_col} < date('now', 'weekday 0', '-6 days')
        AND {date_col} IS NOT NULL
        AND {segment_col} IS NOT NULL
    GROUP BY {segment_col}
),
prior_week AS (
    SELECT 
        {segment_col} AS segment,
        {metric_expression} AS prior_value
    FROM cps_tb
    WHERE {date_col} >= date('now', '-14 days', 'weekday 0', '-6 days')
        AND {date_col} < date('now', '-7 days', 'weekday 0', '-6 days')
        AND {date_col} IS NOT NULL
        AND {segment_col} IS NOT NULL
    GROUP BY {segment_col}
)
SELECT
    c.segment,
    c.current_value AS current_week,
    COALESCE(p.prior_value, 0) AS prior_week,
    c.current_value - COALESCE(p.prior_value, 0) AS delta,
    ROUND(
        (c.current_value - COALESCE(p.prior_value, 0)) / NULLIF(COALESCE(p.prior_value, 0), 0) * 100,
        2
    ) AS delta_pct
FROM current_week c
LEFT JOIN prior_week p ON c.segment = p.segment
ORDER BY current_week DESC
LIMIT 10000;
