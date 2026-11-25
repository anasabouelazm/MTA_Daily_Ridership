-- Week 2 / additional analytical queries supporting questions 11 and 12.

-- 1. Similarity of movement patterns. Each activity series is divided by its
--    own mean, then smoothed over 7 days. Pearson correlation is therefore
--    unit-free. Correlation is association, not causation.
WITH normalized AS (
    SELECT
        f.date_key,
        t.transport_name,
        f.activity_value::numeric / AVG(f.activity_value::numeric) OVER (
            PARTITION BY t.transport_name
        ) AS activity_index
    FROM fact_daily_metrics f
    JOIN dim_transportation t ON t.transport_id = f.transport_id
),
smoothed AS (
    SELECT
        date_key,
        transport_name,
        ROW_NUMBER() OVER (
            PARTITION BY transport_name ORDER BY date_key
        ) AS row_num,
        AVG(activity_index) OVER (
            PARTITION BY transport_name ORDER BY date_key
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS roll7_index
    FROM normalized
),
wide AS (
    SELECT
        date_key,
        MAX(roll7_index) FILTER (WHERE transport_name = 'Subways') AS subways,
        MAX(roll7_index) FILTER (WHERE transport_name = 'Buses') AS buses,
        MAX(roll7_index) FILTER (WHERE transport_name = 'LIRR') AS lirr,
        MAX(roll7_index) FILTER (WHERE transport_name = 'Metro-North') AS metro_north,
        MAX(roll7_index) FILTER (WHERE transport_name = 'Access-A-Ride') AS access_a_ride,
        MAX(roll7_index) FILTER (WHERE transport_name = 'Bridges and Tunnels') AS bridges_tunnels,
        MAX(roll7_index) FILTER (WHERE transport_name = 'Staten Island Railway') AS sir
    FROM smoothed
    WHERE row_num >= 7
    GROUP BY date_key
)
SELECT
    ROUND(corr(subways, buses)::numeric, 3) AS subways_buses,
    ROUND(corr(subways, lirr)::numeric, 3) AS subways_lirr,
    ROUND(corr(subways, metro_north)::numeric, 3) AS subways_metro_north,
    ROUND(corr(subways, sir)::numeric, 3) AS subways_sir,
    ROUND(corr(lirr, metro_north)::numeric, 3) AS lirr_metro_north,
    ROUND(corr(subways, bridges_tunnels)::numeric, 3) AS subways_bridges_tunnels,
    ROUND(corr(buses, bridges_tunnels)::numeric, 3) AS buses_bridges_tunnels
FROM wide;

-- 2. Largest and smallest daily activity observations per system.
WITH ranked AS (
    SELECT
        t.transport_name,
        f.date_key,
        f.activity_value,
        f.recovery_percentage,
        ROW_NUMBER() OVER (PARTITION BY f.transport_id ORDER BY f.activity_value DESC) AS high_rank,
        ROW_NUMBER() OVER (PARTITION BY f.transport_id ORDER BY f.activity_value ASC) AS low_rank
    FROM fact_daily_metrics f
    JOIN dim_transportation t ON t.transport_id = f.transport_id
)
SELECT transport_name, 'highest' AS kind, date_key, activity_value, recovery_percentage
FROM ranked WHERE high_rank <= 3
UNION ALL
SELECT transport_name, 'lowest' AS kind, date_key, activity_value, recovery_percentage
FROM ranked WHERE low_rank <= 3
ORDER BY transport_name, kind, date_key;

-- 3. Staten Island Railway zero-activity days by year (zeros are kept).
SELECT
    d.year,
    COUNT(*) AS zero_activity_days,
    COUNT(*) FILTER (WHERE d.day_name IN ('Saturday', 'Sunday')) AS weekend_zero_days
FROM fact_daily_metrics f
JOIN dim_transportation t ON t.transport_id = f.transport_id
JOIN dim_date d ON d.date_key = f.date_key
WHERE t.transport_name = 'Staten Island Railway' AND f.activity_value = 0
GROUP BY d.year
ORDER BY d.year;

-- 4. Days with recovery above 100 percent by year and system (not removed).
SELECT
    d.year,
    t.transport_name,
    COUNT(*) FILTER (WHERE f.recovery_percentage > 100) AS days_above_100,
    ROUND(MAX(f.recovery_percentage), 2) AS max_recovery_pct
FROM fact_daily_metrics f
JOIN dim_transportation t ON t.transport_id = f.transport_id
JOIN dim_date d ON d.date_key = f.date_key
GROUP BY d.year, t.transport_name
HAVING COUNT(*) FILTER (WHERE f.recovery_percentage > 100) > 0
ORDER BY t.transport_name, d.year;

-- 5. Largest single-day relative activity drops per system, using each
--    system's own mean as the denominator (works with zero values).
WITH means AS (
    SELECT transport_id, AVG(activity_value::numeric) AS mean_activity
    FROM fact_daily_metrics GROUP BY transport_id
),
changes AS (
    SELECT
        t.transport_name,
        f.date_key,
        (f.activity_value::numeric - LAG(f.activity_value::numeric) OVER (
            PARTITION BY f.transport_id ORDER BY f.date_key
        )) / m.mean_activity * 100 AS relative_change_pct
    FROM fact_daily_metrics f
    JOIN dim_transportation t ON t.transport_id = f.transport_id
    JOIN means m ON m.transport_id = f.transport_id
),
ranked AS (
    SELECT
        transport_name,
        date_key,
        relative_change_pct,
        ROW_NUMBER() OVER (
            PARTITION BY transport_name ORDER BY relative_change_pct
        ) AS drop_rank
    FROM changes
)
SELECT transport_name, date_key, ROUND(relative_change_pct, 2) AS relative_change_pct
FROM ranked
WHERE drop_rank <= 3
ORDER BY transport_name, relative_change_pct;
