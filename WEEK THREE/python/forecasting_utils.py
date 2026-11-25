"""Reusable time-series forecasting helpers for MTA Week 3.

The module deliberately reuses Week 2's validated project-root detection and
cleaned-data loader. Activity is forecast independently per transportation
system because the units differ. Recovery percentage is never a forecast target.
"""

from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Configuration and paths (reuse Week 2 utilities)
# ---------------------------------------------------------------------------
def _import_week2_utils():
    env_root = os.environ.get("MTA_PROJECT_ROOT")
    start = Path(env_root) if env_root else Path.cwd()
    for candidate in (start, *start.parents):
        utils_file = candidate / "WEEK TWO" / "python" / "analysis_utils.py"
        if utils_file.is_file():
            sys.path.insert(0, str(utils_file.parent))
            import analysis_utils as week2_utils

            return week2_utils
    raise FileNotFoundError(
        "Could not find WEEK TWO/python/analysis_utils.py. Run from inside the "
        "repository or set MTA_PROJECT_ROOT to the project root."
    )


w2 = _import_week2_utils()

PROJECT_ROOT = w2.PROJECT_ROOT
WEEK3_DIR = PROJECT_ROOT / "WEEK THREE"
REPORT_DIR = WEEK3_DIR / "reports"
FORECAST_DIR = WEEK3_DIR / "forecasts"
MODELS_DIR = WEEK3_DIR / "models"
VIZ_DIR = WEEK3_DIR / "visualizations"
for _directory in (REPORT_DIR, FORECAST_DIR, MODELS_DIR, VIZ_DIR):
    _directory.mkdir(parents=True, exist_ok=True)

SEED = 42
SEASONAL_PERIOD = 7
HORIZONS = (7, 30)
TEST_SIZE = 60
BACKTEST_WINDOWS = {7: 6, 30: 4}
BACKTEST_STEP = {7: 7, 30: 30}
LAGS = (1, 7, 14, 28)
ROLLING_WINDOWS = (7, 14, 28)
SYSTEM_NAMES = w2.SYSTEM_NAMES
SYSTEM_UNITS = w2.SYSTEM_UNITS

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


# ---------------------------------------------------------------------------
# Data loading and validation
# ---------------------------------------------------------------------------
def load_daily_series() -> dict[str, pd.Series]:
    """Load one clean daily activity Series per transportation system."""
    wide = w2.load_cleaned()
    series = {}
    for cfg in w2.TRANSPORT_CONFIG:
        s = pd.Series(
            wide[cfg["activity"]].to_numpy(dtype="float64"),
            index=pd.DatetimeIndex(wide["Date"]),
            name=cfg["name"],
        )
        series[cfg["name"]] = s.sort_index()
    return series


def validate_series(series: pd.Series, name: str) -> dict:
    """Validate structure and values; fail loudly on contract violations."""
    dates = pd.DatetimeIndex(series.index)
    expected = pd.date_range(dates.min(), dates.max(), freq="D")
    report = {
        "transport": name,
        "rows": len(series),
        "date_min": dates.min(),
        "date_max": dates.max(),
        "calendar_days": len(expected),
        "gap_days": int(len(expected.difference(dates))),
        "duplicate_dates": int(dates.duplicated().sum()),
        "missing_values": int(series.isna().sum()),
        "negative_values": int((series < 0).sum()),
        "zero_values": int((series == 0).sum()),
    }
    assert report["gap_days"] == 0, f"{name}: date gaps found"
    assert report["duplicate_dates"] == 0, f"{name}: duplicate dates found"
    assert report["missing_values"] == 0, f"{name}: missing values found"
    assert report["negative_values"] == 0, f"{name}: negative activity found"
    return report


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------
def seasonal_naive_scale(train: pd.Series, m: int = SEASONAL_PERIOD) -> float:
    """In-sample seasonal-naive MAE used as the MASE denominator (train only)."""
    values = np.asarray(train, dtype="float64")
    if len(values) <= m:
        return np.nan
    return float(np.mean(np.abs(values[m:] - values[:-m])))


def autocorrelations(series: pd.Series, lags=(1, 7, 14, 28, 365)) -> dict:
    """Simple Pearson autocorrelations at requested lags."""
    values = np.asarray(series, dtype="float64")
    out = {}
    for lag in lags:
        if lag < len(values):
            out[f"acf_lag_{lag}"] = float(np.corrcoef(values[lag:], values[:-lag])[0, 1])
        else:
            out[f"acf_lag_{lag}"] = np.nan
    return out


def series_diagnostics(series: pd.Series) -> dict:
    """Per-system diagnostics that directly inform model choices."""
    values = np.asarray(series, dtype="float64")
    result = {
        "transport": series.name,
        "days": len(values),
        "mean": float(np.mean(values)),
        "std": float(np.std(values, ddof=1)),
        "cv": float(np.std(values, ddof=1) / np.mean(values)),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "zero_days": int((values == 0).sum()),
        "snaive_scale": seasonal_naive_scale(series),
    }
    result.update(autocorrelations(series))
    recent = series.loc["2023-11-01":]
    covid = series.loc["2020-03-01":"2020-05-31"]
    result["covid_mean"] = float(covid.mean()) if len(covid) else np.nan
    result["recent_mean"] = float(recent.mean()) if len(recent) else np.nan
    return result


# ---------------------------------------------------------------------------
# Metrics (zero-safe; MAPE is intentionally not used)
# ---------------------------------------------------------------------------
def compute_metrics(actual, forecast, train) -> dict:
    """MAE, RMSE, WAPE, sMAPE and MASE for one forecast window."""
    y = np.asarray(actual, dtype="float64")
    f = np.asarray(forecast, dtype="float64")
    if y.shape != f.shape:
        raise ValueError("actual and forecast must have the same length")
    err = y - f
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err**2)))
    denominator = float(np.sum(np.abs(y)))
    wape = float(np.sum(np.abs(err)) / denominator) if denominator > 0 else np.nan

    smape_den = np.abs(y) + np.abs(f)
    smape_terms = np.zeros_like(smape_den, dtype="float64")
    nonzero = smape_den > 0
    smape_terms[nonzero] = 200 * np.abs(err[nonzero]) / smape_den[nonzero]
    smape_terms[(~nonzero) & (np.abs(err) > 0)] = np.nan
    smape = float(np.nanmean(smape_terms))

    scale = seasonal_naive_scale(pd.Series(np.asarray(train, dtype="float64")))
    mase = float(mae / scale) if scale and np.isfinite(scale) and scale > 0 else np.nan
    return {"MAE": mae, "RMSE": rmse, "WAPE": wape, "sMAPE": smape, "MASE": mase}


# ---------------------------------------------------------------------------
# Baseline models
# ---------------------------------------------------------------------------
def forecast_naive(train: pd.Series, horizon: int, future_dates=None) -> np.ndarray:
    return np.full(horizon, float(train.iloc[-1]))


def forecast_seasonal_naive(train: pd.Series, horizon: int, future_dates=None) -> np.ndarray:
    values = np.asarray(train, dtype="float64")
    if len(values) < SEASONAL_PERIOD:
        return np.full(horizon, float(values.mean()))
    return np.array([values[-SEASONAL_PERIOD + (i % SEASONAL_PERIOD)] for i in range(horizon)])


def forecast_moving_average(train: pd.Series, horizon: int, future_dates=None) -> np.ndarray:
    return np.full(horizon, float(train.tail(7).mean()))


def forecast_drift(train: pd.Series, horizon: int, future_dates=None) -> np.ndarray:
    values = np.asarray(train, dtype="float64")
    if len(values) < 2:
        return np.full(horizon, float(values[-1]))
    slope = (values[-1] - values[0]) / (len(values) - 1)
    return values[-1] + slope * np.arange(1, horizon + 1)


# ---------------------------------------------------------------------------
# Advanced models
# ---------------------------------------------------------------------------
def forecast_ets(train: pd.Series, horizon: int, future_dates=None) -> np.ndarray:
    """Holt-Winters with additive trend/seasonality and weekly period."""
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    model = ExponentialSmoothing(
        np.asarray(train, dtype="float64"),
        trend="add",
        seasonal="add",
        seasonal_periods=SEASONAL_PERIOD,
        damped_trend=True,
    ).fit(optimized=True, use_brute=False)
    return np.asarray(model.forecast(horizon), dtype="float64")


def forecast_arima(train: pd.Series, horizon: int, future_dates=None) -> np.ndarray:
    """Compact SARIMA: (1,1,1) x (0,0,1,7), no constant."""
    from statsmodels.tsa.arima.model import ARIMA

    model = ARIMA(
        np.asarray(train, dtype="float64"),
        order=(1, 1, 1),
        seasonal_order=(0, 0, 1, SEASONAL_PERIOD),
        trend="n",
    ).fit()
    return np.asarray(model.forecast(horizon), dtype="float64")


def _feature_frame(history: pd.Series) -> pd.DataFrame:
    """Build lag, rolling and calendar features using past values only."""
    frame = pd.DataFrame({"y": np.asarray(history, dtype="float64")}, index=history.index)
    features = pd.DataFrame(index=frame.index)
    for lag in LAGS:
        features[f"lag_{lag}"] = frame["y"].shift(lag)
    past = frame["y"].shift(1)
    for window in ROLLING_WINDOWS:
        features[f"roll_mean_{window}"] = past.rolling(window, min_periods=window).mean()
    features["roll_std_7"] = past.rolling(7, min_periods=7).std()

    index = pd.DatetimeIndex(history.index)
    features["dayofweek"] = index.dayofweek
    features["dayofmonth"] = index.day
    features["month"] = index.month
    features["dayofyear"] = index.dayofyear
    features["weekofyear"] = index.isocalendar().week.astype(int).to_numpy()
    features["is_weekend"] = (index.dayofweek >= 5).astype(int)
    return features


def forecast_ml(train: pd.Series, horizon: int, future_dates=None) -> np.ndarray:
    """Recursive HistGradientBoosting forecast with leakage-safe features."""
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.pipeline import Pipeline

    if future_dates is None:
        raise ValueError("forecast_ml requires future_dates")
    feature_all = _feature_frame(train)
    usable = feature_all.notna().all(axis=1)
    X_train = feature_all.loc[usable]
    y_train = train.loc[usable]
    if len(X_train) == 0:
        raise ValueError("no usable training rows for ML model")
    model = Pipeline(
        [("regressor", HistGradientBoostingRegressor(random_state=SEED, max_iter=200, learning_rate=0.05))]
    )
    model.fit(X_train, y_train)

    full_index = train.index.append(pd.DatetimeIndex(future_dates))
    history = pd.Series(np.nan, index=full_index, dtype="float64")
    history.loc[train.index] = np.asarray(train, dtype="float64")
    predictions = []
    for date in pd.DatetimeIndex(future_dates):
        row = _feature_frame(history).loc[[date]]
        if row.isna().any(axis=1).any():
            raise ValueError(f"incomplete feature row for {date}")
        pred = float(model.predict(row)[0])
        predictions.append(pred)
        history.loc[date] = pred
    return np.asarray(predictions, dtype="float64")


def safe_forecast(predictions) -> np.ndarray:
    """Clip physically impossible negative activity forecasts to zero."""
    return np.clip(np.asarray(predictions, dtype="float64"), 0.0, None)


def model_registry(include_advanced: bool = True) -> dict[str, Callable]:
    models = {
        "Naive": forecast_naive,
        "SeasonalNaive": forecast_seasonal_naive,
        "MovingAverage7": forecast_moving_average,
        "Drift": forecast_drift,
    }
    if include_advanced:
        models.update({"ETS": forecast_ets, "SARIMA": forecast_arima, "HistGBM": forecast_ml})
    return models


# ---------------------------------------------------------------------------
# Time-respecting evaluation
# ---------------------------------------------------------------------------
def make_origins(series: pd.Series, horizon: int, n_windows: int | None = None) -> list[pd.Timestamp]:
    """Rolling origins strictly before the held-out final TEST_SIZE days."""
    n_windows = n_windows or BACKTEST_WINDOWS[horizon]
    dev_end = len(series) - TEST_SIZE - 1
    last_origin = dev_end - horizon
    step = BACKTEST_STEP[horizon]
    origins = [last_origin - step * i for i in range(n_windows)][::-1]
    if origins[0] < 60:
        raise ValueError("not enough history for requested backtest windows")
    return [pd.Timestamp(series.index[pos]) for pos in origins]


def backtest_series(
    series: pd.Series,
    horizon: int,
    models: dict[str, Callable] | None = None,
    origins: list[pd.Timestamp] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Backtest all models on identical chronological origins."""
    models = models or model_registry()
    origins = origins or make_origins(series, horizon)
    summary_rows, residual_rows = [], []
    for origin in origins:
        pos = series.index.get_loc(origin)
        train = series.iloc[: pos + 1]
        actual = series.iloc[pos + 1 : pos + 1 + horizon]
        if len(actual) != horizon:
            continue
        for name, fn in models.items():
            try:
                pred = safe_forecast(fn(train, horizon, actual.index))
            except Exception as exc:  # keep the backtest moving; record the failure
                summary_rows.append(
                    {
                        "transport": series.name,
                        "model": name,
                        "horizon": horizon,
                        "origin": origin,
                        "status": f"FAILED: {type(exc).__name__}",
                    }
                )
                continue
            metrics = compute_metrics(actual.values, pred, train.values)
            summary_rows.append(
                {
                    "transport": series.name,
                    "model": name,
                    "horizon": horizon,
                    "origin": origin,
                    "status": "OK",
                    **metrics,
                }
            )
            for step, (date, observed, predicted) in enumerate(
                zip(actual.index, actual.values, pred), start=1
            ):
                residual_rows.append(
                    {
                        "transport": series.name,
                        "model": name,
                        "horizon": horizon,
                        "origin": origin,
                        "step": step,
                        "date": date,
                        "residual": float(observed - predicted),
                    }
                )
    return pd.DataFrame(summary_rows), pd.DataFrame(residual_rows)


def evaluate_final_test(
    series: pd.Series,
    horizon: int,
    models: dict[str, Callable],
) -> pd.DataFrame:
    """Evaluate once on the last `horizon` days after model selection."""
    train = series.iloc[:-horizon]
    actual = series.iloc[-horizon:]
    rows = []
    for name, fn in models.items():
        try:
            pred = safe_forecast(fn(train, horizon, actual.index))
        except Exception as exc:
            rows.append({"transport": series.name, "model": name, "horizon": horizon,
                         "status": f"FAILED: {type(exc).__name__}"})
            continue
        rows.append(
            {
                "transport": series.name,
                "model": name,
                "horizon": horizon,
                "status": "OK",
                "train_end": train.index[-1],
                "test_start": actual.index[0],
                "test_end": actual.index[-1],
                **compute_metrics(actual.values, pred, train.values),
            }
        )
    return pd.DataFrame(rows)


def aggregate_backtest(backtest_df: pd.DataFrame) -> pd.DataFrame:
    """Mean metrics per system/model/horizon across successful origins."""
    df = backtest_df[backtest_df["status"] == "OK"].copy()
    grouped = (
        df.groupby(["transport", "model", "horizon"], as_index=False)
        .agg(MAE=("MAE", "mean"), RMSE=("RMSE", "mean"), WAPE=("WAPE", "mean"),
             sMAPE=("sMAPE", "mean"), MASE=("MASE", "mean"), origins=("origin", "count"))
    )
    baseline = grouped[grouped["model"] == "SeasonalNaive"][
        ["transport", "horizon", "MASE"]
    ].rename(columns={"MASE": "seasonal_naive_MASE"})
    grouped = grouped.merge(baseline, on=["transport", "horizon"], how="left")
    grouped["MASE_improvement_pct"] = 100 * (
        1 - grouped["MASE"] / grouped["seasonal_naive_MASE"]
    )
    return grouped.sort_values(["transport", "horizon", "MASE"]).reset_index(drop=True)


def select_models(aggregated: pd.DataFrame) -> pd.DataFrame:
    """Select lowest-mean-MASE model per system and horizon (backtests only)."""
    selected = aggregated.sort_values("MASE").groupby(["transport", "horizon"], as_index=False).head(1)
    selected = selected.rename(columns={"model": "selected_model"}).copy()
    selected["selected"] = True
    return selected[
        ["transport", "horizon", "selected_model", "MASE", "MASE_improvement_pct"]
    ].reset_index(drop=True)


def residual_intervals(
    residuals: pd.DataFrame,
    transport: str,
    model: str,
    horizon: int,
    level: float = 0.80,
) -> tuple[float, float, float]:
    """Empirical additive interval from backtest residuals (lower, centre, upper)."""
    sub = residuals[
        (residuals["transport"] == transport)
        & (residuals["model"] == model)
        & (residuals["horizon"] == horizon)
    ]["residual"].dropna().to_numpy()
    if len(sub) < 10:
        return (0.0, 0.0, 0.0)
    alpha = (1 - level) / 2
    return (float(np.quantile(sub, alpha)), 0.0, float(np.quantile(sub, 1 - alpha)))


def interval_coverage(
    actual: np.ndarray, forecast: np.ndarray, lower_shift: float, upper_shift: float
) -> float:
    """Share of test observations inside the additive residual interval."""
    y = np.asarray(actual, dtype="float64")
    f = np.asarray(forecast, dtype="float64")
    return float(np.mean((y >= f + lower_shift) & (y <= f + upper_shift)))


def final_forecast(
    series: pd.Series,
    model_name: str,
    horizon: int,
    models: dict[str, Callable] | None = None,
) -> pd.DataFrame:
    """Refit the selected model on all observations and forecast future dates."""
    models = models or model_registry()
    future_dates = pd.date_range(series.index[-1] + pd.Timedelta(days=1), periods=horizon, freq="D")
    prediction = safe_forecast(models[model_name](series, horizon, future_dates))
    frame = pd.DataFrame(
        {
            "transport": series.name,
            "date": future_dates,
            "point_forecast": prediction,
            "step": np.arange(1, horizon + 1),
        }
    )
    return frame


def attach_intervals(forecast: pd.DataFrame, shifts: tuple[float, float, float]) -> pd.DataFrame:
    lower, centre, upper = shifts
    out = forecast.copy()
    out["lower_80"] = np.maximum(out["point_forecast"] + lower + centre, 0.0)
    out["upper_80"] = np.maximum(out["point_forecast"] + upper + centre, 0.0)
    return out


def slug(name: str) -> str:
    return name.lower().replace(" ", "_").replace("-", "_")
