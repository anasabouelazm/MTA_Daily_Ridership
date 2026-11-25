"""Fast regression tests for Week 3 forecasting utilities.

Run from the repository root with: python -m pytest "WEEK THREE/python/test_forecasting_utils.py" -q
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

MODULE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(MODULE_DIR))

import forecasting_utils as fu  # noqa: E402


def test_project_root_from_module_directory(monkeypatch):
    monkeypatch.delenv("MTA_PROJECT_ROOT", raising=False)
    monkeypatch.chdir(MODULE_DIR)
    assert fu.PROJECT_ROOT.name == "MTA Project"
    assert fu.WEEK3_DIR.name == "WEEK THREE"


def test_project_root_from_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("MTA_PROJECT_ROOT", str(fu.PROJECT_ROOT))
    monkeypatch.chdir(tmp_path)
    code = (
        f"import sys; sys.path.insert(0, r'{MODULE_DIR}'); "
        "import forecasting_utils as f; print(f.PROJECT_ROOT)"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=tmp_path, capture_output=True, text=True, check=True
    )
    assert result.stdout.strip().endswith("MTA Project")


def test_invalid_environment_root_is_rejected(tmp_path):
    env = os.environ.copy()
    env["MTA_PROJECT_ROOT"] = str(tmp_path)
    code = (
        f"import sys; sys.path.insert(0, r'{MODULE_DIR}'); "
        "import forecasting_utils"
    )
    result = subprocess.run([sys.executable, "-c", code], cwd=tmp_path, env=env, capture_output=True, text=True)
    assert result.returncode != 0
    assert "MTA_PROJECT_ROOT" in result.stderr


def test_validate_series_retains_zeros_but_rejects_gaps():
    index = pd.date_range("2024-01-01", periods=10, freq="D")
    values = np.array([1, 0, 2, 3, 4, 5, 6, 7, 8, 9], dtype="float64")
    series = pd.Series(values, index=index, name="Test")
    report = fu.validate_series(series, "Test")
    assert report["zero_values"] == 1
    assert report["missing_values"] == 0

    gapped = series.drop(index[3])
    with pytest.raises(AssertionError, match="date gaps"):
        fu.validate_series(gapped, "Test")


def test_seasonal_naive_baseline_uses_lag_seven():
    values = np.arange(14, dtype="float64") + 100
    series = pd.Series(values, index=pd.date_range("2024-01-01", periods=14, freq="D"))
    prediction = fu.forecast_seasonal_naive(series, 3)
    np.testing.assert_array_equal(prediction, np.array([values[-7], values[-6], values[-5]]))
    assert fu.seasonal_naive_scale(series) == pytest.approx(7.0)


def test_metrics_are_zero_safe():
    train = pd.Series(np.arange(30, dtype="float64") + 100)
    actual = np.array([0.0, 10.0, 20.0])
    forecast = np.array([0.0, 10.0, 10.0])
    metrics = fu.compute_metrics(actual, forecast, train.values)
    assert np.isfinite(metrics["sMAPE"])
    assert metrics["MAE"] == pytest.approx(10 / 3)
    assert np.isnan(fu.compute_metrics(np.zeros(3), np.zeros(3), train.values)["WAPE"])


def test_features_exclude_current_target():
    index = pd.date_range("2024-01-01", periods=40, freq="D")
    series = pd.Series(np.arange(40, dtype="float64") + 100, index=index)
    features_before = fu._feature_frame(series).iloc[-1]
    modified = series.copy()
    modified.iloc[-1] = 999999
    features_after = fu._feature_frame(modified).iloc[-1]
    for column in ["lag_1", "lag_7", "lag_14", "lag_28", "roll_mean_7", "roll_std_7"]:
        assert features_before[column] == pytest.approx(features_after[column])
    assert features_before["lag_1"] == pytest.approx(series.iloc[-2])


def test_origins_are_strictly_before_final_test():
    series = fu.load_daily_series()["Subways"]
    test_start = series.index[len(series) - fu.TEST_SIZE]
    for horizon in fu.HORIZONS:
        origins = fu.make_origins(series, horizon)
        assert len(origins) == fu.BACKTEST_WINDOWS[horizon]
        assert all(origin < test_start for origin in origins)
        assert all(origin + pd.Timedelta(days=horizon) < test_start for origin in origins)


def test_all_models_return_nonnegative_finite_forecasts():
    series = fu.load_daily_series()["Subways"].iloc[-500:]
    future = pd.date_range(series.index[-1] + pd.Timedelta(days=1), periods=7, freq="D")
    for name, fn in fu.model_registry().items():
        prediction = fu.safe_forecast(fn(series, 7, future))
        assert prediction.shape == (7,)
        assert np.all(np.isfinite(prediction))
        assert np.all(prediction >= 0)


def test_final_forecast_dates_follow_history():
    series = fu.load_daily_series()["Staten Island Railway"]
    frame = fu.final_forecast(series, "SeasonalNaive", 30)
    assert frame["date"].min() == series.index[-1] + pd.Timedelta(days=1)
    assert frame["date"].max() == series.index[-1] + pd.Timedelta(days=30)
    assert len(frame) == 30
