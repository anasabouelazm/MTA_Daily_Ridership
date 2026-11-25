# Week 3 Forecasting Report — MTA Daily Ridership

## Executive Summary

Week 3 produced a reproducible daily forecasting pipeline for all seven MTA transportation systems. The sole modelling input is the Week 1 cleaned CSV (1,706 days, 2020-03-01 to 2024-10-31). Each system was forecast independently because the units differ: estimated riders, scheduled trips and vehicles were never combined.

Seven models were evaluated: four baselines (Naive, SeasonalNaive, MovingAverage7, Drift), two statistical models (ETS, SARIMA), and one scikit-learn gradient-boosting model (HistGBM). All models were compared on identical chronological rolling origins — 6 weekly-spaced origins for the 7-day horizon and 4 monthly-spaced origins for the 30-day horizon — giving 490 successful backtest rows. The final 60 days were held out and used only after model selection.

Key results:

- ETS was selected for 5 of 7 systems at the 7-day horizon and 4 of 7 at the 30-day horizon; HistGBM was selected for Bridges and Tunnels; SeasonalNaive remained best for Subways (h=7), Buses (h=30) and Staten Island Railway (h=30).
- Advanced models beat seasonal naive on backtest MASE for 6 of 7 systems at h=7 and 5 of 7 at h=30.
- Selected-model validation MASE ranged from 0.312 to 0.779 at h=7 and from 0.610 to 1.172 at h=30.
- On the held-out test window, selected-model MASE averaged 0.700 and WAPE averaged 4.11%.
- The 30-day forecasts for 2024-11-01 to 2024-11-30 are close to the last 30 observed days: system-level mean changes range from -2.83% to +0.22%.
- Empirical 80% prediction intervals are indicative only: backtest coverage averaged 59.2% at h=7 and 67.6% at h=30, below the nominal 80%.

## What was forecast and why

The target is daily activity for each transportation system: subway, bus, LIRR, Metro-North and SIR estimated ridership; Access-A-Ride scheduled trips; and Bridges and Tunnels traffic. Forecasting supports short-term service planning and performance monitoring. Recovery percentage was deliberately not used as a target because it is a comparison metric affected by the February 2023 methodology refresh and the 2023-11-10 one-day anomaly identified in Week 2.

## Data preparation decisions

- Parsed `Date` and sorted chronologically.
- Verified 1,706 consecutive daily observations, no duplicate dates, no missing values and no negative activity.
- Retained all 32 Staten Island Railway zero-activity weekend days; they are genuine source values.
- Did not cap or remove recovery values above 100 because recovery was not used in modelling.
- Did not delete COVID-era extremes or the February 2021 Bridges and Tunnels low; these are structural features of the history.
- Forecast each system independently and report all metrics in that system's own units or as unit-free ratios.

## Important time series patterns

- All systems show a deep 2020 trough followed by an uneven recovery, so a single global trend model would be inappropriate.
- Weekly seasonality is strong: for example, Subways lag-7 autocorrelation is 0.93, and weekend/weekday activity ratios from Week 2 range from 0.93 (Bridges and Tunnels) to 0.27 (SIR).
- Month-of-year effects are visible: autumn and March are generally strong for transit modes, while Bridges and Tunnels peaks in summer.
- SIR is intermittent with legitimate weekend zeros, giving it the highest relative volatility.
- The COVID period inflates early-history volatility, which affects MASE denominators for backtests that include 2020 training data.

## Models evaluated

| Model | Description |
|---|---|
| Naive | Repeat the last observed value |
| SeasonalNaive | Repeat the value from the same weekday last week (lag 7) |
| MovingAverage7 | Repeat the mean of the last 7 observations |
| Drift | Extend the full-history linear drift from the last value |
| ETS | Holt-Winters, additive trend and weekly seasonality, damped trend |
| SARIMA | ARIMA `(1,1,1)` with seasonal `(0,0,1,7)`, no constant |
| HistGBM | Recursive gradient boosting with lag 1/7/14/28, rolling mean/std and calendar features |

HistGBM features are built from shifted past values only; the rolling window never includes the target day. The random seed is fixed at 42. All forecasts are clipped at zero.

## Validation methodology

- **Development window:** all observations before the final 60 days.
- **Backtest origins:** 6 origins spaced 7 days apart for h=7; 4 origins spaced 30 days apart for h=30. Every origin leaves a full forecast window inside the development period.
- **Final test:** last 30 days for h=30 and last 7 days for h=7, evaluated only after model selection.
- **Selection metric:** mean MASE across backtest origins. Supporting metrics: MAE, RMSE, WAPE, sMAPE.
- **No random splits.** No future observations are used in training features.

A total of 490 backtest rows were produced (7 systems x 2 horizons x 10 origins x 7 models), all successful.

## Model performance

### Selected models — validation backtests

| Horizon | System | Selected model | MAE | RMSE | WAPE | sMAPE | MASE | MASE gain vs SeasonalNaive |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 7 | Subways | SeasonalNaive | 69,160 | 85,729 | 0.0231 | 2.736 | 0.339 | 0.0% |
| 7 | Buses | ETS | 29,232 | 33,697 | 0.0286 | 2.948 | 0.312 | +17.2% |
| 7 | LIRR | ETS | 8,383 | 10,220 | 0.0401 | 4.426 | 0.773 | +8.9% |
| 7 | Metro-North | ETS | 7,575 | 8,806 | 0.0436 | 4.746 | 0.779 | +9.9% |
| 7 | Access-A-Ride | ETS | 600 | 715 | 0.0192 | 2.004 | 0.356 | +17.2% |
| 7 | Bridges and Tunnels | HistGBM | 21,719 | 28,164 | 0.0229 | 2.310 | 0.475 | +21.7% |
| 7 | Staten Island Railway | ETS | 205 | 235 | 0.0387 | 4.401 | 0.347 | +19.6% |
| 30 | Subways | ETS | 153,744 | 273,788 | 0.0483 | 5.148 | 0.753 | +13.3% |
| 30 | Buses | SeasonalNaive | 57,720 | 93,512 | 0.0541 | 5.671 | 0.610 | 0.0% |
| 30 | LIRR | ETS | 12,540 | 20,373 | 0.0604 | 6.643 | 1.172 | +10.1% |
| 30 | Metro-North | ETS | 10,395 | 18,274 | 0.0579 | 6.271 | 1.083 | +17.7% |
| 30 | Access-A-Ride | ETS | 1,196 | 2,553 | 0.0388 | 4.312 | 0.712 | +9.2% |
| 30 | Bridges and Tunnels | HistGBM | 30,622 | 45,189 | 0.0320 | 3.280 | 0.667 | +18.0% |
| 30 | Staten Island Railway | SeasonalNaive | 434 | 733 | 0.0780 | 8.502 | 0.730 | 0.0% |

A MASE above 1 means the model is worse than the in-sample seasonal-naive scale. LIRR (1.172) and Metro-North (1.083) still beat the out-of-sample seasonal-naive baseline on the same backtest windows, which is why they were selected; this distinction is important when reading the table.

### Held-out test evaluation

Selected-model test MASE ranged from 0.441 to 1.018 with a mean of 0.700. Test WAPE ranged from 2.19% to 7.07% with a mean of 4.11%. The 30-day test MASE was 0.879 for Subways, 0.721 for Buses, 0.658 for LIRR, 1.018 for Metro-North, 0.672 for Access-A-Ride, 0.757 for Bridges and Tunnels, and 0.798 for SIR. These figures were not used for model selection.

### Prediction interval coverage

| Horizon | Coverage range | Mean coverage |
|---|---:|---:|
| 7 days | 42.9% – 100.0% | 59.2% |
| 30 days | 50.0% – 93.3% | 67.6% |

Coverage is below the nominal 80% for most pairs, so the intervals should be treated as indicative ranges, not reliable probabilistic bounds. LIRR intervals were too wide (100% at h=7, 93.3% at h=30); Subways h=7 covered only 42.9%.

## Best model per system (30-day forecast)

| System | Unit | Selected model | Validation MASE | Forecast mean | Change vs last 30 days |
|---|---|---|---:|---:|---:|
| Subways | estimated riders | ETS | 0.753 | 3,643,892 | +0.07% |
| Buses | estimated riders | SeasonalNaive | 0.610 | 1,288,410 | +0.17% |
| LIRR | estimated riders | ETS | 1.172 | 223,803 | -2.05% |
| Metro-North | estimated riders | ETS | 1.083 | 203,787 | -0.35% |
| Access-A-Ride | scheduled trips | ETS | 0.712 | 33,692 | +0.22% |
| Bridges and Tunnels | vehicles | HistGBM | 0.667 | 922,527 | -2.83% |
| Staten Island Railway | estimated riders | SeasonalNaive | 0.730 | 6,562 | -1.40% |

The forecast period is 2024-11-01 to 2024-11-30 for all systems.

## Forecast results

The forecasts are intentionally conservative: all seven system-level mean changes are within ±3% of the most recent 30-day mean. This is consistent with a mature recovery phase in which weekly seasonality dominates short-horizon dynamics. The largest modelled decline is Bridges and Tunnels (-2.83%), where HistGBM captured a slight downward movement from the recent traffic level. The largest increase is Access-A-Ride (+0.22%), essentially flat.

Per-system forecast files include the date, step, point forecast, lower 80% and upper 80% columns. Intervals were constructed from the empirical 10th and 90th percentiles of the selected model's backtest residuals.

## Uncertainty and limitations

- Only about 4.7 years of daily history are available, and the first year is dominated by COVID disruption.
- The February 2023 methodology change affects comparison percentages, not activity; it does not justify removing any activity observations.
- LIRR and Metro-North are modelled estimates; Bridges and Tunnels traffic is preliminary; Access-A-Ride measures scheduled trips, not completed rides.
- SARIMA was evaluated but not selected for any system.
- Prediction intervals are not well calibrated; coverage was below 80% on average.
- No holiday calendar, weather, fare or service-change covariates were available, so forecasts are purely autoregressive/calendar-based.
- Correlation between systems is not treated as causation.

## Practical conclusions and recommendations

1. Use the 7-day forecasts with weekly seasonal structure for operational planning; they show the lowest MASE (mean 0.483).
2. Treat 30-day forecasts as directional guidance only, especially for LIRR and Metro-North where MASE exceeds 1.
3. Refresh forecasts as new observations arrive; the model metadata file records the data snapshot, selected models and library versions.
4. Monitor realised MASE against the seasonal-naive baseline and re-select if a model stops beating it.
5. Investigate and improve interval calibration before using the intervals for capacity or risk commitments.

## Reproducibility

All results are generated by `WEEK THREE/python/MTA_Time_Series_Forecasting.ipynb` from the repo root. The utility module contains reusable loading, validation, diagnostics, models, metrics, backtesting and forecasting functions. `WEEK THREE/python/test_forecasting_utils.py` contains 10 passing regression tests. No Week 1 or Week 2 files were modified.
