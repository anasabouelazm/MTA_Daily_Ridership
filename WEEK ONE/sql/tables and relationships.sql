Create table dim_date(
date_key DATE primary key,
year int,
month int,
day int,
day_name VARCHAR(30)
);


create TABLE dim_transportation (
    transport_id INT PRIMARY KEY,
    transport_name VARCHAR(100) UNIQUE,
    activity_measure VARCHAR(100)
);

CREATE TABLE fact_daily_metrics (
    
    activity_value BIGINT,
    recovery_percentage NUMERIC(10,2),
	date_key DATE references dim_date(date_key),
	transport_id INT references dim_transportation(transport_id)
);


SELECT COUNT(*) FROM dim_date;

SELECT COUNT(*) FROM dim_transportation;

SELECT COUNT(*) FROM fact_daily_metrics;

SELECT
    d.date_key,
    t.transport_name,
    f.activity_value,
    f.recovery_percentage
FROM fact_daily_metrics f
JOIN dim_date d
    ON f.date_key = d.date_key
JOIN dim_transportation t
    ON f.transport_id = t.transport_id
LIMIT 10;