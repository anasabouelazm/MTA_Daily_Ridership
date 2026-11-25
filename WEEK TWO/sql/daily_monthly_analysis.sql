-- Week 2 / daily and monthly analysis
-- Uses only the Week 1 star schema. No schema changes are made.
-- Units differ by system, so activity is never summed across systems.

-- 1. Daily series per system, with day type and 7-day rolling activity.
--    Zero activity days are retained (not treated as missing).
WITH daily AS (
    SELECT
        f.date_key,
        t.transport_name,
        t.activity_measure,
        f.activity_value,
        f.recovery_percentage,
        CASE WHEN d.day_name IN ('Saturday', 'Sunday') THEN 'Weekend' ELSE 'Weekday' END AS day_type
    FROM fact_daily_metrics f
    JOIN dim_transportation t ON t.transport_id = f.transport_id
    JOIN dim_date d ON d.date_key = f.date_key
)
SELECT
    date_key,
    transport_name,
    activity_measure,
    activity_value,
    recovery_percentage,
    day_type,
    ROUND(AVG(activity_value) OVER (
        PARTITION BY transport_name ORDER BY date_key
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 1) AS activity_7day_mean
FROM daily
ORDER BY transport_name, date_key;

-- 2. Monthly mean activity and recovery per system, plus month-over-month change.
--    MoM is computed within each system only.
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', f.date_key)::date AS month_start,
        t.transport_name,
        t.activity_measure,
        AVG(f.activity_value) AS avg_activity,
        AVG(f.recovery_percentage) AS avg_recovery
    FROM fact_daily_metrics f
    JOIN dim_transportation t ON t.transport_id = f.transport_id
    GROUP BY 1, 2, 3
)
SELECT
    month_start,
    transport_name,
    activity_measure,
    ROUND(avg_activity, 1) AS avg_activity,
    ROUND(avg_recovery, 2) AS avg_recovery_pct,
    ROUND(100 * (avg_activity / LAG(avg_activity) OVER (
        PARTITION BY transport_name ORDER BY month_start
    ) - 1), 2) AS activity_mom_pct
FROM monthly
ORDER BY transport_name, month_start;

-- 3. Recurring month-of-year pattern, indexed to each year's own mean (100).
--    This reduces the confounding effect of the 2020-2024 recovery trend.
WITH indexed AS (
    SELECT
        f.date_key,
        t.transport_name,
        EXTRACT(MONTH FROM f.date_key)::int AS month_num,
        f.activity_value / AVG(f.activity_value) OVER (
            PARTITION BY t.transport_name, EXTRACT(YEAR FROM f.date_key)
        ) * 100 AS activity_index
    FROM fact_daily_metrics f
    JOIN dim_transportation t ON t.transport_id = f.transport_id
)
SELECT
    transport_name,
    month_num,
    ROUND(AVG(activity_index), 1) AS avg_activity_index_100
FROM indexed
GROUP BY transport_name, month_num
ORDER BY transport_name, month_num;

-- 4. Weekday versus weekend activity and recovery by system (zeros included).
SELECT
    t.transport_name,
    CASE WHEN d.day_name IN ('Saturday', 'Sunday') THEN 'Weekend' ELSE 'Weekday' END AS day_type,
    COUNT(*) AS days,
    ROUND(AVG(f.activity_value), 1) AS avg_activity,
    ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.activity_value))::numeric, 1) AS median_activity,
    ROUND(AVG(f.recovery_percentage), 2) AS avg_recovery_pct
FROM fact_daily_metrics f
JOIN dim_transportation t ON t.transport_id = f.transport_id
JOIN dim_date d ON d.date_key = f.date_key
GROUP BY 1, 2
ORDER BY 1, 2;
