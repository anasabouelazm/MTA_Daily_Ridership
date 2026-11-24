-- MTA Daily Ridership - Week 1 star schema (PostgreSQL)
--
-- WARNING: this script rebuilds the Week 1 tables. It drops them first, so any
-- existing rows in these three tables are removed. Run load.sql afterwards to
-- reload the CSV data.
--
-- Run from the repository root (the folder that contains "WEEK ONE"):
--   psql -d mta_ridership -f "WEEK ONE/sql/tables and relationships.sql"

BEGIN;

DROP TABLE IF EXISTS fact_daily_metrics;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_transportation;

CREATE TABLE dim_date (
    date_key DATE PRIMARY KEY,
    year INT NOT NULL,
    month INT NOT NULL,
    day INT NOT NULL,
    day_name VARCHAR(30) NOT NULL
);

CREATE TABLE dim_transportation (
    transport_id INT PRIMARY KEY,
    transport_name VARCHAR(100) NOT NULL UNIQUE,
    activity_measure VARCHAR(100) NOT NULL
);

-- Grain: one row per date_key x transport_id (1,706 dates x 7 systems = 11,942).
CREATE TABLE fact_daily_metrics (
    date_key DATE NOT NULL REFERENCES dim_date(date_key),
    activity_value BIGINT NOT NULL CHECK (activity_value >= 0),
    recovery_percentage NUMERIC(10, 2) NOT NULL CHECK (recovery_percentage >= 0),
    transport_id INT NOT NULL REFERENCES dim_transportation(transport_id),
    PRIMARY KEY (date_key, transport_id)
);

CREATE INDEX idx_fact_daily_metrics_date_key
    ON fact_daily_metrics (date_key);

CREATE INDEX idx_fact_daily_metrics_transport_id
    ON fact_daily_metrics (transport_id);

COMMIT;
