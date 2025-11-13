-- Forecast vs Actual Variance Decomposition Analysis
-- Shows which segments contribute most to the overall forecast gap
-- Parameters: :start_date, :end_date, metric type (submits/approved/issuance)

WITH 
-- Calculate overall totals
overall_totals AS (
    SELECT
        SUM({forecast_col}) as total_forecast,
        SUM({actual_col}) as total_actual,
        SUM({actual_col}) - SUM({forecast_col}) as total_delta,
        CASE 
            WHEN SUM({forecast_col}) > 0 
            THEN ROUND((SUM({actual_col}) - SUM({forecast_col})) * 100.0 / SUM({forecast_col}), 2)
            ELSE 0 
        END as total_delta_pct
    FROM forecast_df
    WHERE date BETWEEN :start_date AND :end_date
        AND date IS NOT NULL
        {channel_filter}
        {grade_filter}
        {prod_type_filter}
        {repeat_type_filter}
        {term_filter}
),

-- Breakdown by each segment dimension
channel_breakdown AS (
    SELECT
        'channel' as dimension,
        channel as segment_value,
        SUM({forecast_col}) as forecast_value,
        SUM({actual_col}) as actual_value,
        SUM({actual_col}) - SUM({forecast_col}) as delta,
        CASE 
            WHEN SUM({forecast_col}) > 0 
            THEN ROUND((SUM({actual_col}) - SUM({forecast_col})) * 100.0 / SUM({forecast_col}), 2)
            ELSE 0 
        END as delta_pct,
        -- Contribution to overall delta
        ROUND((SUM({actual_col}) - SUM({forecast_col})) * 100.0 / 
            NULLIF((SELECT total_delta FROM overall_totals), 0), 2) as contribution_pct
    FROM forecast_df
    WHERE date BETWEEN :start_date AND :end_date
        AND date IS NOT NULL
        AND channel IS NOT NULL
        {grade_filter}
        {prod_type_filter}
        {repeat_type_filter}
        {term_filter}
    GROUP BY channel
),

grade_breakdown AS (
    SELECT
        'grade' as dimension,
        grade as segment_value,
        SUM({forecast_col}) as forecast_value,
        SUM({actual_col}) as actual_value,
        SUM({actual_col}) - SUM({forecast_col}) as delta,
        CASE 
            WHEN SUM({forecast_col}) > 0 
            THEN ROUND((SUM({actual_col}) - SUM({forecast_col})) * 100.0 / SUM({forecast_col}), 2)
            ELSE 0 
        END as delta_pct,
        ROUND((SUM({actual_col}) - SUM({forecast_col})) * 100.0 / 
            NULLIF((SELECT total_delta FROM overall_totals), 0), 2) as contribution_pct
    FROM forecast_df
    WHERE date BETWEEN :start_date AND :end_date
        AND date IS NOT NULL
        AND grade IS NOT NULL
        {channel_filter}
        {prod_type_filter}
        {repeat_type_filter}
        {term_filter}
    GROUP BY grade
),

prod_type_breakdown AS (
    SELECT
        'prod_type' as dimension,
        prod_type as segment_value,
        SUM({forecast_col}) as forecast_value,
        SUM({actual_col}) as actual_value,
        SUM({actual_col}) - SUM({forecast_col}) as delta,
        CASE 
            WHEN SUM({forecast_col}) > 0 
            THEN ROUND((SUM({actual_col}) - SUM({forecast_col})) * 100.0 / SUM({forecast_col}), 2)
            ELSE 0 
        END as delta_pct,
        ROUND((SUM({actual_col}) - SUM({forecast_col})) * 100.0 / 
            NULLIF((SELECT total_delta FROM overall_totals), 0), 2) as contribution_pct
    FROM forecast_df
    WHERE date BETWEEN :start_date AND :end_date
        AND date IS NOT NULL
        AND prod_type IS NOT NULL
        {channel_filter}
        {grade_filter}
        {repeat_type_filter}
        {term_filter}
    GROUP BY prod_type
),

repeat_type_breakdown AS (
    SELECT
        'repeat_type' as dimension,
        repeat_type as segment_value,
        SUM({forecast_col}) as forecast_value,
        SUM({actual_col}) as actual_value,
        SUM({actual_col}) - SUM({forecast_col}) as delta,
        CASE 
            WHEN SUM({forecast_col}) > 0 
            THEN ROUND((SUM({actual_col}) - SUM({forecast_col})) * 100.0 / SUM({forecast_col}), 2)
            ELSE 0 
        END as delta_pct,
        ROUND((SUM({actual_col}) - SUM({forecast_col})) * 100.0 / 
            NULLIF((SELECT total_delta FROM overall_totals), 0), 2) as contribution_pct
    FROM forecast_df
    WHERE date BETWEEN :start_date AND :end_date
        AND date IS NOT NULL
        AND repeat_type IS NOT NULL
        {channel_filter}
        {grade_filter}
        {prod_type_filter}
        {term_filter}
    GROUP BY repeat_type
),

term_breakdown AS (
    SELECT
        'term' as dimension,
        CAST(term AS TEXT) as segment_value,
        SUM({forecast_col}) as forecast_value,
        SUM({actual_col}) as actual_value,
        SUM({actual_col}) - SUM({forecast_col}) as delta,
        CASE 
            WHEN SUM({forecast_col}) > 0 
            THEN ROUND((SUM({actual_col}) - SUM({forecast_col})) * 100.0 / SUM({forecast_col}), 2)
            ELSE 0 
        END as delta_pct,
        ROUND((SUM({actual_col}) - SUM({forecast_col})) * 100.0 / 
            NULLIF((SELECT total_delta FROM overall_totals), 0), 2) as contribution_pct
    FROM forecast_df
    WHERE date BETWEEN :start_date AND :end_date
        AND date IS NOT NULL
        AND term IS NOT NULL
        {channel_filter}
        {grade_filter}
        {prod_type_filter}
        {repeat_type_filter}
    GROUP BY term
),

-- Combine all breakdowns
all_segments AS (
    SELECT * FROM channel_breakdown
    UNION ALL
    SELECT * FROM grade_breakdown
    UNION ALL
    SELECT * FROM prod_type_breakdown
    UNION ALL
    SELECT * FROM repeat_type_breakdown
    UNION ALL
    SELECT * FROM term_breakdown
),

-- Add overall summary row
summary AS (
    SELECT
        'OVERALL' as dimension,
        'Total' as segment_value,
        total_forecast as forecast_value,
        total_actual as actual_value,
        total_delta as delta,
        total_delta_pct as delta_pct,
        100.0 as contribution_pct
    FROM overall_totals
)

-- Return summary first, then segments ordered by absolute contribution
SELECT * FROM (
    SELECT * FROM summary
    UNION ALL
    SELECT * FROM all_segments
    WHERE ABS(delta) > 0  -- Only show segments with variance
)
ORDER BY 
    CASE WHEN dimension = 'OVERALL' THEN 0 ELSE 1 END,
    ABS(contribution_pct) DESC
LIMIT 100;
