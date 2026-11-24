-- MTA Daily Ridership - Week 1 data load (PostgreSQL)
--
-- Run from the repository root (the folder that contains "WEEK ONE"), after
-- creating the tables with "tables and relationships.sql":
--   psql -d mta_ridership -f "WEEK ONE/sql/load.sql"
--
-- \copy is a psql client-side command, so the relative CSV paths below are
-- resolved against the shell's current directory, not against this SQL file.
--
-- The whole load runs in one transaction. If a COPY or validation check fails,
-- the transaction is rolled back and the previous table contents are kept.

\set ON_ERROR_STOP on

BEGIN;

TRUNCATE TABLE fact_daily_metrics, dim_date, dim_transportation;

\copy dim_date (date_key, year, month, day, day_name) FROM 'WEEK ONE/database/dim_date.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')

\copy dim_transportation (transport_id, transport_name, activity_measure) FROM 'WEEK ONE/database/dim_transportation.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')

\copy fact_daily_metrics (date_key, activity_value, recovery_percentage, transport_id) FROM 'WEEK ONE/database/fact_daily_metrics.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')

DO $$
DECLARE
    v_dim_date BIGINT;
    v_dim_transportation BIGINT;
    v_fact BIGINT;
    v_duplicate_grain BIGINT;
    v_fact_dates BIGINT;
    v_fact_transports BIGINT;
BEGIN
    SELECT count(*) INTO v_dim_date FROM dim_date;
    SELECT count(*) INTO v_dim_transportation FROM dim_transportation;
    SELECT count(*) INTO v_fact FROM fact_daily_metrics;

    IF v_dim_date <> 1706 THEN
        RAISE EXCEPTION 'dim_date has % rows; expected 1706', v_dim_date;
    END IF;

    IF v_dim_transportation <> 7 THEN
        RAISE EXCEPTION 'dim_transportation has % rows; expected 7', v_dim_transportation;
    END IF;

    IF v_fact <> 11942 THEN
        RAISE EXCEPTION 'fact_daily_metrics has % rows; expected 11942', v_fact;
    END IF;

    SELECT count(*) INTO v_duplicate_grain
    FROM (
        SELECT date_key, transport_id
        FROM fact_daily_metrics
        GROUP BY date_key, transport_id
        HAVING count(*) > 1
    ) duplicates;

    IF v_duplicate_grain <> 0 THEN
        RAISE EXCEPTION 'fact_daily_metrics has % duplicate (date_key, transport_id) grains', v_duplicate_grain;
    END IF;

    SELECT count(DISTINCT date_key) INTO v_fact_dates FROM fact_daily_metrics;
    SELECT count(DISTINCT transport_id) INTO v_fact_transports FROM fact_daily_metrics;

    IF v_fact_dates <> 1706 THEN
        RAISE EXCEPTION 'fact_daily_metrics covers % dates; expected 1706', v_fact_dates;
    END IF;

    IF v_fact_transports <> 7 THEN
        RAISE EXCEPTION 'fact_daily_metrics covers % transport systems; expected 7', v_fact_transports;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM fact_daily_metrics f
        LEFT JOIN dim_date d ON d.date_key = f.date_key
        WHERE d.date_key IS NULL
    ) THEN
        RAISE EXCEPTION 'fact_daily_metrics contains date_key values missing from dim_date';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM fact_daily_metrics f
        LEFT JOIN dim_transportation t ON t.transport_id = f.transport_id
        WHERE t.transport_id IS NULL
    ) THEN
        RAISE EXCEPTION 'fact_daily_metrics contains transport_id values missing from dim_transportation';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM fact_daily_metrics
        WHERE activity_value < 0 OR recovery_percentage < 0
    ) THEN
        RAISE EXCEPTION 'fact_daily_metrics contains negative measures';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM fact_daily_metrics
        GROUP BY transport_id
        HAVING count(*) <> 1706
    ) THEN
        RAISE EXCEPTION 'one or more transport systems do not have exactly 1706 fact rows';
    END IF;
END
$$;

COMMIT;

SELECT 'dim_date' AS table_name, count(*) AS row_count FROM dim_date
UNION ALL
SELECT 'dim_transportation', count(*) FROM dim_transportation
UNION ALL
SELECT 'fact_daily_metrics', count(*) FROM fact_daily_metrics
ORDER BY table_name;
