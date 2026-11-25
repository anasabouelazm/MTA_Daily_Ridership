-- Week 2 / COVID-19 impact and recovery analysis
-- "Recovery" is the source percentage of a comparable pre-pandemic day:
-- 100 means activity matched that 2019 month/day-type baseline; it is not a
-- share of current activity. Values above 100 are retained.

-- 1. Early-pandemic impact (March-April 2020) by system.
WITH early AS (
    SELECT
        t.transport_name,
        AVG(f.recovery_percentage) AS early_mean_recovery,
        MIN(f.recovery_percentage) AS early_min_recovery,
        MIN(f.activity_value) AS early_min_activity
    FROM fact_daily_metrics f
    JOIN dim_transportation t ON t.transport_id = f.transport_id
    WHERE f.date_key BETWEEN DATE '2020-03-01' AND DATE '2020-04-30'
    GROUP BY t.transport_name
),
late AS (
    SELECT
        t.transport_name,
        AVG(f.recovery_percentage) AS late_mean_recovery,
        100.0 * COUNT(*) FILTER (WHERE f.recovery_percentage > 100) / COUNT(*) AS late_pct_above_100,
        MAX(f.recovery_percentage) AS max_recovery
    FROM fact_daily_metrics f
    JOIN dim_transportation t ON t.transport_id = f.transport_id
    WHERE f.date_key BETWEEN DATE '2023-11-01' AND DATE '2024-10-31'
    GROUP BY t.transport_name
)
SELECT
    e.transport_name,
    ROUND(e.early_mean_recovery, 2) AS early_mean_recovery_pct,
    e.early_min_recovery AS early_min_recovery_pct,
    e.early_min_activity,
    ROUND(l.late_mean_recovery, 2) AS late_mean_recovery_pct,
    ROUND(l.late_pct_above_100, 2) AS late_pct_days_above_100,
    l.max_recovery AS late_max_recovery_pct
FROM early e
JOIN late l ON l.transport_name = e.transport_name
ORDER BY e.early_mean_recovery DESC;

-- 2. First date at which the 7-day mean recovery was >= 100 for at least
--    14 consecutive days. This is a deliberately conservative "sustained"
--    definition; isolated high days are reported separately below.
WITH recovery_daily AS (
    SELECT
        f.date_key,
        t.transport_name,
        f.recovery_percentage,
        ROW_NUMBER() OVER (PARTITION BY f.transport_id ORDER BY f.date_key) AS row_num,
        AVG(f.recovery_percentage::numeric) OVER (
            PARTITION BY f.transport_id ORDER BY f.date_key
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS roll7_recovery
    FROM fact_daily_metrics f
    JOIN dim_transportation t ON t.transport_id = f.transport_id
),
flagged AS (
    SELECT
        date_key,
        transport_name,
        roll7_recovery >= 100 AS above,
        BOOL_AND(roll7_recovery >= 100) OVER (
            PARTITION BY transport_name ORDER BY date_key
            ROWS BETWEEN 0 PRECEDING AND 13 FOLLOWING
        ) AS above_next_14
    FROM recovery_daily
    WHERE row_num >= 7
)
SELECT
    transport_name,
    MIN(date_key) FILTER (WHERE above AND above_next_14) AS first_sustained_100_date,
    MIN(date_key) FILTER (WHERE above) AS first_roll7_100_date
FROM flagged
GROUP BY transport_name
ORDER BY transport_name;

-- 3. Isolated days above 100 versus sustained recovery.
SELECT
    t.transport_name,
    COUNT(*) FILTER (WHERE f.recovery_percentage > 100) AS days_above_100,
    MAX(f.recovery_percentage) AS max_recovery_pct,
    MIN(f.date_key) FILTER (WHERE f.recovery_percentage > 100) AS first_day_above_100,
    MAX(f.date_key) FILTER (WHERE f.recovery_percentage > 100) AS last_day_above_100
FROM fact_daily_metrics f
JOIN dim_transportation t ON t.transport_id = f.transport_id
GROUP BY t.transport_name
ORDER BY t.transport_name;

-- 4. February 2023 methodology change context. The source documentation says
--    the upgrade affected pre-COVID comparison percentages, not activity
--    estimates. Both windows below are 12 calendar months, matched by month.
WITH windows AS (
    SELECT
        t.transport_name,
        AVG(f.recovery_percentage) FILTER (
            WHERE f.date_key BETWEEN DATE '2022-02-01' AND DATE '2023-01-31'
        ) AS pre_recovery,
        AVG(f.recovery_percentage) FILTER (
            WHERE f.date_key BETWEEN DATE '2023-02-01' AND DATE '2024-01-31'
        ) AS post_recovery,
        AVG(f.activity_value::numeric) FILTER (
            WHERE f.date_key BETWEEN DATE '2022-02-01' AND DATE '2023-01-31'
        ) AS pre_activity,
        AVG(f.activity_value::numeric) FILTER (
            WHERE f.date_key BETWEEN DATE '2023-02-01' AND DATE '2024-01-31'
        ) AS post_activity
    FROM fact_daily_metrics f
    JOIN dim_transportation t ON t.transport_id = f.transport_id
    GROUP BY t.transport_name
)
SELECT
    transport_name,
    ROUND(pre_recovery, 2) AS pre_change_mean_recovery_pct,
    ROUND(post_recovery, 2) AS post_change_mean_recovery_pct,
    ROUND(post_recovery - pre_recovery, 2) AS recovery_change_pp,
    ROUND(100 * (post_activity / pre_activity - 1), 2) AS activity_change_pct
FROM windows
ORDER BY transport_name;

-- 5. 2023-11-10: recovery jumps sharply on one day while activity does not.
--    This is shown as a possible baseline/comparison artifact, not as demand.
SELECT
    t.transport_name,
    f.activity_value,
    f.recovery_percentage,
    ROUND(AVG(f2.recovery_percentage::numeric), 2) AS nearby_6day_mean_recovery
FROM fact_daily_metrics f
JOIN dim_transportation t ON t.transport_id = f.transport_id
JOIN fact_daily_metrics f2
    ON f2.transport_id = f.transport_id
   AND (
        f2.date_key BETWEEN DATE '2023-11-07' AND DATE '2023-11-09'
        OR f2.date_key BETWEEN DATE '2023-11-11' AND DATE '2023-11-13'
   )
WHERE f.date_key = DATE '2023-11-10'
GROUP BY t.transport_name, f.activity_value, f.recovery_percentage
ORDER BY t.transport_name;
