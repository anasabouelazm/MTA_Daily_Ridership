-- Week 2 / comparable transportation-system comparison
-- All metrics are unit-free or stay within one system. No cross-system totals.

WITH system_mean AS (
    SELECT
        t.transport_id,
        t.transport_name,
        t.activity_measure,
        AVG(f.activity_value::numeric) AS mean_activity
    FROM fact_daily_metrics f
    JOIN dim_transportation t ON t.transport_id = f.transport_id
    GROUP BY 1, 2, 3
),
daily_change AS (
    SELECT
        f.transport_id,
        (f.activity_value::numeric
         - LAG(f.activity_value::numeric) OVER (PARTITION BY f.transport_id ORDER BY f.date_key))
        / m.mean_activity AS relative_daily_change
    FROM fact_daily_metrics f
    JOIN system_mean m ON m.transport_id = f.transport_id
),
volatility AS (
    SELECT
        transport_id,
        STDDEV_SAMP(relative_daily_change) AS daily_change_volatility
    FROM daily_change
    GROUP BY transport_id
),
periods AS (
    SELECT
        f.transport_id,
        AVG(f.activity_value::numeric) FILTER (
            WHERE f.date_key BETWEEN DATE '2020-03-01' AND DATE '2021-02-28'
        ) AS first12_activity,
        AVG(f.activity_value::numeric) FILTER (
            WHERE f.date_key BETWEEN DATE '2023-11-01' AND DATE '2024-10-31'
        ) AS last12_activity,
        AVG(f.recovery_percentage) FILTER (
            WHERE f.date_key BETWEEN DATE '2023-11-01' AND DATE '2024-10-31'
        ) AS last12_recovery,
        100.0 * COUNT(*) FILTER (
            WHERE f.recovery_percentage > 100
        ) / COUNT(*) AS pct_days_above_100
    FROM fact_daily_metrics f
    GROUP BY f.transport_id
)
SELECT
    t.transport_name,
    t.activity_measure,
    ROUND(m.mean_activity, 1) AS mean_daily_activity,
    ROUND(p.first12_activity, 1) AS first12_mean_activity,
    ROUND(p.last12_activity, 1) AS last12_mean_activity,
    ROUND(100 * (p.last12_activity / p.first12_activity - 1), 2) AS period_change_pct,
    ROUND(p.last12_recovery, 2) AS last12_mean_recovery_pct,
    ROUND(p.pct_days_above_100, 2) AS pct_days_recovery_above_100,
    ROUND(v.daily_change_volatility, 4) AS daily_change_volatility,
    RANK() OVER (ORDER BY v.daily_change_volatility DESC) AS volatility_rank,
    RANK() OVER (ORDER BY p.last12_recovery DESC) AS recovery_rank
FROM system_mean m
JOIN volatility v ON v.transport_id = m.transport_id
JOIN periods p ON p.transport_id = m.transport_id
JOIN dim_transportation t ON t.transport_id = m.transport_id
ORDER BY volatility_rank;

-- Interpretation note: period_change_pct compares the first 12 available months
-- (March 2020-February 2021, deeply affected by COVID-19) with the last 12
-- months (November 2023-October 2024). It is not a normal-year growth rate.
