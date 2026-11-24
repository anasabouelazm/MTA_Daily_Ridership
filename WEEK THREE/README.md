# MTA Daily Ridership — Week 3 Time Series Forecasting

Week 3 builds a reproducible daily forecasting pipeline for the seven MTA transportation systems. It follows Week 1's validated cleaned dataset and Week 2's findings: each system is modelled independently because units differ, recovery percentage is not a forecasting target, zero activity is never treated as missing, and the February 2023 methodology change applies to comparison percentages rather than activity estimates.

## Objectives

- Forecast daily activity 30 days beyond the last observation (2024-10-31).
- Evaluate the shorter 7-day horizon as well.
- Establish naive, weekly seasonal-naive, moving-average and drift baselines before advanced models.
- Backtest with chronological rolling origins and a held-out final test period.
- Compare models using MAE, RMSE, WAPE, sMAPE and MASE; use MASE as the primary selection metric.
- Produce empirical 80% prediction intervals and check their coverage.
- Identify which systems have genuinely predictable daily patterns.

## Tools and technologies

- Python 3.13.5
- pandas 2.3.3, NumPy 2.3.1, Matplotlib 3.11.2
- scikit-learn 1.9.1 (`HistGradientBoostingRegressor`, `Pipeline`)
- statsmodels 0.15.0 (`ExponentialSmoothing`, `ARIMA`)
- SciPy 1.18.1, joblib 1.6.0 (transitive dependencies)
- Jupyter / `nbconvert` for fresh-kernel execution
- pytest 8.x for utility tests

No additional project dependencies were added to source control; the two installed libraries above are the only new runtime requirements.

## Data sources

- `WEEK ONE/MTA_Daily_Ridership_Cleaned.csv` — the sole modelling input.
- `WEEK TWO/python/analysis_utils.py` — reused for project-root detection, system configuration and verified column meanings.
- `WEEK TWO/reports/Week_2_Analysis_Report.md` — context for weekly/annual seasonality, COVID impact, the 2023-11-10 recovery anomaly and the 32 SIR zero weekends.

No Week 1 or Week 2 file is modified.

## Folder structure

```text
WEEK THREE/
├── README.md
├── python/
│   ├── MTA_Time_Series_Forecasting.ipynb
│   ├── forecasting_utils.py
│   └── test_forecasting_utils.py
├── reports/
│   ├── Week_3_Forecasting_Report.md
│   ├── backtesting_results.csv
│   ├── model_comparison.csv
│   ├── test_evaluation.csv
│   ├── interval_coverage.csv
│   └── forecast_summary.csv
├── models/
│   └── model_metadata.json
├── forecasts/
│   └── <system>_30day_forecast.csv        (7 files)
└── visualizations/
    └── diagnostic / comparison / forecast PNG files
```

## Analytical workflow

1. Load the cleaned CSV and build one daily series per system.
2. Validate gap-free daily frequency, unique dates, non-negative values and retained zeros.
3. Plot daily series with 7- and 30-day rolling means; inspect weekly/monthly seasonality and ACF/PACF.
4. Split chronologically: development history, rolling-origin backtests, and a final untouched 60-day test set.
5. Backtest 7 models on 6 weekly origins (h=7) and 4 monthly origins (h=30) per system.
6. Aggregate MASE across origins and select the best model per system and horizon using validation data only.
7. Evaluate the selected models once on the held-out test window.
8. Refit selected models on all history and forecast 2024-11-01 to 2024-11-30 with empirical residual intervals.

## Models evaluated

| Family | Models |
|---|---|
| Baselines | Naive, SeasonalNaive (lag 7), MovingAverage7, Drift |
| Statistical | ETS / Holt-Winters (additive trend + weekly seasonality), SARIMA `(1,1,1) x (0,0,1,7)` |
| Machine learning | HistGBM with lag 1/7/14/28, rolling mean/std 7/14/28 and calendar features |

All lag and rolling features use shifted past values only; multi-step HistGBM forecasts are recursive. Forecasts are clipped at zero. Random seed 42 is used for the ML model.

## Validation design

- Development window ends 60 days before 2024-10-31.
- Backtest origins for h=7 are 7 days apart (6 origins); for h=30 they are 30 days apart (4 origins).
- Every model and system uses identical origins.
- Final test: last 30 days for h=30 and last 7 days for h=7, evaluated only after selection.
- MASE denominator is the in-sample weekly seasonal-naive MAE computed from observations available at each origin.
- MAPE is intentionally not used because some systems have zero activity days.

## Metrics

- **MAE** — average absolute error in the system's own units.
- **RMSE** — penalises large misses more heavily.
- **WAPE** — total absolute error divided by total actual; robust to zeros.
- **sMAPE** — symmetric relative error, zero-safe.
- **MASE** — MAE divided by the training seasonal-naive scale; values below 1 beat the in-sample seasonal-naive benchmark.

## Execution

Run all commands from the repository root (the folder containing `WEEK ONE`, `WEEK TWO` and `WEEK THREE`).

```bash
python -m pytest "WEEK THREE/python/test_forecasting_utils.py" -q
jupyter nbconvert --to notebook --execute --inplace "WEEK THREE/python/MTA_Time_Series_Forecasting.ipynb"
```

The notebook resolves paths through `forecasting_utils.py`, which reuses Week 2's root detection. Set `MTA_PROJECT_ROOT` if launching from outside the repository.

## Deliverables

- Executed 14-section notebook and reusable utility module.
- Utility test suite (10 tests).
- Five report CSVs, seven per-system forecast CSVs, one metadata JSON.
- Seventeen visualizations covering diagnostics, baselines, model comparison, residuals and forecasts.
- Final forecasting report with executive summary, methodology, results and limitations.

## Interpretation cautions

- Prediction intervals are empirical residual-quantile ranges, not guaranteed bounds; backtest coverage was below the nominal 80% for most system/horizon pairs.
- LIRR and Metro-North are modelled estimates; Bridges and Tunnels is preliminary traffic; Access-A-Ride counts scheduled trips.
- COVID-era volatility inflates in-sample MASE denominators for early origins; recent backtests are more representative of current conditions.
- Correlation and co-movement do not imply causation.
