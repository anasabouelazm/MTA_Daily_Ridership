# MTA Daily Ridership — Week 2 Exploratory Data Analysis

Week 2 turns the validated Week 1 data pipeline into evidence-based analysis: EDA, 12 analytical questions, KPI analysis, visualizations, SQL queries, and decision-maker insights.

## Objectives

- Review data quality without changing any source values.
- Compare transportation systems using unit-free, comparable measures.
- Describe daily, monthly, weekday/weekend, and seasonal patterns.
- Quantify COVID-19 impact and recovery against the source's pre-pandemic baseline.
- Identify similarity between systems and investigate unusual operational signals.
- Answer 12 explicit analytical questions with calculations from the actual dataset.

## Tools and technologies

- Python 3.13.5; pandas 2.3.3; NumPy 2.3.1; Matplotlib 3.11.2
- Jupyter (`python3` kernel) and `nbconvert` for fresh-kernel execution
- PostgreSQL 18 and psql for analytical SQL
- No additional project dependencies were introduced

## Data sources

- `WEEK ONE/MTA_Daily_Ridership_Cleaned.csv` — primary analysis input, 1,706 rows x 15 columns.
- `WEEK ONE/database/*.csv` and the Week 1 schema — used to validate the SQL analysis.
- `MTA_data_dictionary.csv` and `MTA_DailyRidershipData_Overview.pdf` from the source dataset folder — used to verify column meanings and caveats. They are not copied into the repository.

No Week 1 file is modified by this work. Original values, zero values, and recovery values above 100 are preserved.

## Folder structure

```text
WEEK TWO/
├── README.md
├── python/
│   ├── MTA_Exploratory_Data_Analysis.ipynb
│   ├── analysis_utils.py
│   └── __pycache__/               # ignored by .gitignore
├── sql/
│   ├── daily_monthly_analysis.sql
│   ├── transportation_comparison.sql
│   ├── covid_impact_recovery.sql
│   └── analytical_queries.sql
├── visualizations/
│   ├── 01_activity_distributions.png
│   ├── 02_system_performance.png
│   ├── 03_daily_activity_trends.png
│   ├── 04_monthly_recovery_trends.png
│   ├── 05_month_of_year_heatmap.png
│   ├── 06_weekday_weekend_ratio.png
│   ├── 07_covid_impact.png
│   ├── 08_recovery_distribution.png
│   ├── 09_recovery_paths.png
│   ├── 10_correlation_heatmap.png
│   ├── 11_recovery_anomaly_2023_11_10.png
│   └── 12_sir_zero_activity.png
└── reports/
    ├── Week_2_Analysis_Report.md
    ├── system_metrics.csv
    └── correlation_matrix.csv
```

## Analytical workflow

1. Load the wide cleaned CSV and reshape it to a tidy date x system table.
2. Verify shape, dtypes, missing values, duplicates, date continuity, negatives, and zero counts.
3. Compute descriptive statistics and distributions per system, keeping units separate.
4. Build unit-free metrics: recovery percentage, activity index, weekend/weekday ratio, and normalized volatility.
5. Aggregate daily and monthly series; derive month-of-year seasonality indexed within each year.
6. Measure COVID impact with the published recovery percentage (no pre-2020 activity exists).
7. Define sustained recovery as a 7-day mean of at least 100 for 14 consecutive days.
8. Analyse similarity with correlation of 7-day normalized activity, and review anomalies.
9. Execute equivalent SQL against the Week 1 schema and run the notebook from a fresh kernel.
10. Publish the report, metric exports, and charts.

## The 12 analytical questions

**A. Transportation system performance**

1. How does ridership performance differ across systems?
2. Which systems have the highest and lowest relative changes over the analysed period?
3. Which systems show the greatest day-to-day volatility?

**B. Time-based analysis**

4. How does daily ridership change over time for each system?
5. What are the monthly trends and which months are consistently higher or lower?
6. Are there meaningful weekday/weekend differences?
7. What recurring seasonal patterns or unusual peaks and drops occur?

**C. COVID-19 impact and recovery**

8. How significantly did COVID-19 affect ridership across systems?
9. How did each system recover relative to its pre-pandemic baseline?
10. When did each system reach or exceed that baseline, if applicable?

**D. Relationships and operational insights**

11. Which systems show similar movement patterns?
12. What unusual patterns, disruptions, or operational signals deserve follow-up?

## Important interpretation rules

- Activity units differ: Subways, Buses, LIRR, Metro-North and SIR are estimated riders; Access-A-Ride is scheduled trips; Bridges and Tunnels is traffic (vehicles). Raw activity is never summed across systems.
- A recovery percentage of 100 means activity matched the comparable 2019 month/day-type day. Values above 100 are retained.
- Zeros are real published values and are kept, especially the 32 Staten Island Railway zero weekends.
- The February 2023 MTA methodology update affected pre-COVID comparison percentages, not activity estimates. Recovery trends around that date must be interpreted with caution.
- Correlation is association only, not causation.

## Execution

Run all commands from the repository root (the folder containing `WEEK ONE` and `WEEK TWO`).

Notebook — fresh kernel, top to bottom:

```bash
jupyter nbconvert --to notebook --execute --inplace "WEEK TWO/python/MTA_Exploratory_Data_Analysis.ipynb"
```

The notebook resolves paths through `analysis_utils.py`; set `MTA_PROJECT_ROOT` if launched from outside the repository. It writes charts to `WEEK TWO/visualizations/` and metric exports to `WEEK TWO/reports/`.

SQL — create/load the Week 1 database first, then run each Week 2 query file:

```bash
createdb mta_ridership
psql -d mta_ridership -v ON_ERROR_STOP=1 -f "WEEK ONE/sql/tables and relationships.sql"
psql -d mta_ridership -v ON_ERROR_STOP=1 -f "WEEK ONE/sql/load.sql"

psql -d mta_ridership -v ON_ERROR_STOP=1 -f "WEEK TWO/sql/daily_monthly_analysis.sql"
psql -d mta_ridership -v ON_ERROR_STOP=1 -f "WEEK TWO/sql/transportation_comparison.sql"
psql -d mta_ridership -v ON_ERROR_STOP=1 -f "WEEK TWO/sql/covid_impact_recovery.sql"
psql -d mta_ridership -v ON_ERROR_STOP=1 -f "WEEK TWO/sql/analytical_queries.sql"
```

On Windows, use the full path to `psql.exe` if it is not on `PATH`. Week 2 SQL is read-only: it adds no tables, columns, or rows.

## Deliverables

- Executed notebook with 14 sections and no cell errors.
- Reusable Python helper module.
- Four SQL analysis files.
- 12 Matplotlib visualizations answering specific questions.
- Final report with executive summary, KPIs, 12 answers, insights, limitations and conclusions.
- Reproducible metric and correlation exports.
