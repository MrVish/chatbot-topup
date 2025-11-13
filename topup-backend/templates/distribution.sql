-- Distribution/composition analysis by segment
-- Parameters: :start_date, :end_date, :metric, :date_col, :segment_by, :channel, :grade, :prod_type, :repeat_type, :term, :cr_fico_band, :purpose

WITH segment_data AS (
    SELECT 
        {segment_by} AS segment,
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
    GROUP BY {segment_by}
),
total_data AS (
    SELECT SUM(metric_value) AS total_value
    FROM segment_data
)
SELECT
    s.segment,
    s.metric_value,
    s.record_count,
    ROUND(s.metric_value / NULLIF(t.total_value, 0) * 100, 2) AS percentage
FROM segment_data s
CROSS JOIN total_data t
ORDER BY 
    CASE 
        -- Special ordering for FICO bands
        WHEN s.segment = '<640' THEN 1
        WHEN s.segment = '640-699' THEN 2
        WHEN s.segment = '700-759' THEN 3
        WHEN s.segment = '760+' THEN 4
        ELSE 5
    END,
    s.metric_value DESC
LIMIT 10000;
