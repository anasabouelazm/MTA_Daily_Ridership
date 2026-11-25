# MTA Daily Ridership — Week 1
## Data Processing & Database Design

Week 1 establishes the data foundation for the MTA Daily Ridership project. It validates the original dataset, prepares reproducible outputs, designs a relational Star Schema, and loads the resulting tables into PostgreSQL.

## Objectives

- Inspect and validate the original MTA dataset.
- Verify missing values, duplicates, date continuity, and invalid measurements.
- Prepare the cleaned dataset.
- Transform the original wide dataset into dimension and fact tables.
- Design a relational Star Schema.
- Load and validate the database using PostgreSQL.

## Dataset Information

| Attribute | Value |
|---|---|
| Source | MTA Daily Ridership |
| Date Range | 2020-03-01 to 2024-10-31 |
| Daily Records | 1,706 |
| Original Columns | 15 |
| Transportation Systems | 7 |
| Missing Values | 0 |
| Duplicate Rows | 0 |

The original CSV and cleaned output are identical. The processing stage focuses on validation and reshaping rather than modifying source measurements.

## Project Structure

```text
WEEK ONE/
│
├── README.md
├── data/
│   └── raw/
│       └── MTA_Daily_Ridership.csv
│
├── database/
│   ├── dim_date.csv
│   ├── dim_transportation.csv
│   └── fact_daily_metrics.csv
│
├── python/
│   └── MTA_Processing.ipynb
│
├── sql/
│   ├── tables and relationships.sql
│   └── load.sql
│
└── MTA_Daily_Ridership_Cleaned.csv
```

## Data Processing Workflow

1. Load the original dataset.
2. Inspect dimensions, data types, and data quality.
3. Validate missing values, duplicate records, and date continuity.
4. Preserve the original published measurements.
5. Prepare the cleaned dataset.
6. Generate dimension and fact tables.
7. Validate the generated outputs.

## Database Design — Star Schema

The database consists of three tables:

| Table | Grain | Rows | Primary Key |
|---|---|---:|---|
| dim_date | One row per calendar date | 1,706 | date_key |
| dim_transportation | One row per transportation system | 7 | transport_id |
| fact_daily_metrics | One row per date and system | 11,942 | date_key, transport_id |

### Dimension Tables

**dim_date**
- date_key
- year
- month
- day
- day_name

**dim_transportation**
- transport_id
- transport_name
- activity_measure

### Fact Table

**fact_daily_metrics**
- date_key
- transport_id
- activity_value
- recovery_percentage

The fact table uses foreign keys referencing both dimensions. Constraints enforce data integrity, including non-negative activity and recovery values.

## Transportation Measurement Units

| Transportation System | Activity Measure |
|---|---|
| Subways | Estimated Ridership |
| Buses | Estimated Ridership |
| LIRR | Estimated Ridership |
| Metro-North | Estimated Ridership |
| Staten Island Railway | Estimated Ridership |
| Access-A-Ride | Scheduled Trips |
| Bridges and Tunnels | Traffic (Vehicles) |

Raw activity values must not be summed across systems with different measurement units.

## PostgreSQL Setup

Create the database:

```bash
createdb mta_ridership
```

Create the tables:

```bash
psql -d mta_ridership -f "WEEK ONE/sql/tables and relationships.sql"
```

Load the data:

```bash
psql -d mta_ridership -f "WEEK ONE/sql/load.sql"
```

The schema script drops and recreates the three tables. Do not execute it against a database whose existing Week 1 data must be preserved.

The loading script uses a transaction and performs post-load validation.

## Verification Queries

```sql
SELECT COUNT(*) FROM dim_date;
-- Expected: 1706

SELECT COUNT(*) FROM dim_transportation;
-- Expected: 7

SELECT COUNT(*) FROM fact_daily_metrics;
-- Expected: 11942
```

## Validation Results

The recorded validation results include:

- 1,706 daily observations.
- 7 transportation systems.
- 11,942 fact records.
- No duplicate fact grains.
- No foreign-key violations.
- All 14 original measures reconstructed exactly from the fact table.
- Database constraints successfully reject invalid records during validation tests.

## Execution

From the repository root:

```bash
jupyter nbconvert --to notebook --execute --inplace "WEEK ONE/python/MTA_Processing.ipynb"
```

The notebook generates:
- MTA_Daily_Ridership_Cleaned.csv
- dim_date.csv
- dim_transportation.csv
- fact_daily_metrics.csv

## Deliverables

- Data processing and validation notebook.
- Cleaned MTA dataset.
- Three database CSV exports.
- PostgreSQL Star Schema.
- SQL table creation and loading scripts.
- Data integrity validation.

## Important Data Notes

- The original dataset is preserved.
- Staten Island Railway contains published zero-activity observations that should not be automatically imputed.
- Access-A-Ride measures scheduled trips, not completed trips.
- Bridges and Tunnels data represents vehicles, not passengers.
- LIRR and Metro-North activity values are modeled estimates.
- The MTA methodology changed in February 2023, affecting the interpretation of recovery percentages.

---

**Week 1 Focus:** Data Processing | Data Validation | PostgreSQL | SQL | Star Schema