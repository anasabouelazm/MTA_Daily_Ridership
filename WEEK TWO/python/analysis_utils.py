"""Reusable analysis helpers for MTA Week 2.

All functions read the Week 1 cleaned CSV only. They never modify source values.
Units are kept at the transportation-system level, so measures with different
units are never summed or compared as if they were the same quantity.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Paths and configuration
# ---------------------------------------------------------------------------
def _has_project_layout(root: Path) -> bool:
    """Return True when root contains the Week 1 and Week 2 project folders."""
    return (
        (root / "WEEK ONE" / "python").is_dir()
        and (root / "WEEK ONE" / "database").is_dir()
        and (root / "WEEK TWO" / "python").is_dir()
    )


def find_project_root(start: Path) -> Path:
    """Return the repository root containing the WEEK ONE and WEEK TWO folders."""
    for candidate in (start, *start.parents):
        if _has_project_layout(candidate):
            return candidate
    raise FileNotFoundError(
        "Could not locate the project root. Run from inside the repository "
        "or set MTA_PROJECT_ROOT."
    )


_env_root = os.environ.get("MTA_PROJECT_ROOT")
if _env_root:
    PROJECT_ROOT = Path(_env_root).expanduser().resolve()
    if not _has_project_layout(PROJECT_ROOT):
        raise FileNotFoundError(
            f"MTA_PROJECT_ROOT is not a valid project root: {PROJECT_ROOT}"
        )
else:
    PROJECT_ROOT = find_project_root(Path.cwd())
WEEK1_DIR = PROJECT_ROOT / "WEEK ONE"
WEEK2_DIR = PROJECT_ROOT / "WEEK TWO"
CLEANED_PATH = WEEK1_DIR / "MTA_Daily_Ridership_Cleaned.csv"
VIZ_DIR = WEEK2_DIR / "visualizations"

EARLY_START = pd.Timestamp("2020-03-01")
EARLY_END = pd.Timestamp("2020-04-30")
FIRST_12_START = pd.Timestamp("2020-03-01")
FIRST_12_END = pd.Timestamp("2021-02-28")
LATE_START = pd.Timestamp("2023-11-01")
LATE_END = pd.Timestamp("2024-10-31")
METHODOLOGY_DATE = pd.Timestamp("2023-02-01")

# Verified against MTA_data_dictionary.csv and WEEK ONE/database/dim_transportation.csv.
TRANSPORT_CONFIG = [
    {
        "id": 1,
        "name": "Subways",
        "activity": "Subways: Total Estimated Ridership",
        "pct": "Subways: % of Comparable Pre-Pandemic Day",
        "measure": "Estimated Ridership",
        "unit": "estimated riders",
        "family": "ridership",
    },
    {
        "id": 2,
        "name": "Buses",
        "activity": "Buses: Total Estimated Ridership",
        "pct": "Buses: % of Comparable Pre-Pandemic Day",
        "measure": "Estimated Ridership",
        "unit": "estimated riders",
        "family": "ridership",
    },
    {
        "id": 3,
        "name": "LIRR",
        "activity": "LIRR: Total Estimated Ridership",
        "pct": "LIRR: % of Comparable Pre-Pandemic Day",
        "measure": "Estimated Ridership",
        "unit": "estimated riders",
        "family": "ridership",
    },
    {
        "id": 4,
        "name": "Metro-North",
        "activity": "Metro-North: Total Estimated Ridership",
        "pct": "Metro-North: % of Comparable Pre-Pandemic Day",
        "measure": "Estimated Ridership",
        "unit": "estimated riders",
        "family": "ridership",
    },
    {
        "id": 5,
        "name": "Access-A-Ride",
        "activity": "Access-A-Ride: Total Scheduled Trips",
        "pct": "Access-A-Ride: % of Comparable Pre-Pandemic Day",
        "measure": "Scheduled Trips",
        "unit": "scheduled trips",
        "family": "trips",
    },
    {
        "id": 6,
        "name": "Bridges and Tunnels",
        "activity": "Bridges and Tunnels: Total Traffic",
        "pct": "Bridges and Tunnels: % of Comparable Pre-Pandemic Day",
        "measure": "Traffic",
        "unit": "vehicles",
        "family": "traffic",
    },
    {
        "id": 7,
        "name": "Staten Island Railway",
        "activity": "Staten Island Railway: Total Estimated Ridership",
        "pct": "Staten Island Railway: % of Comparable Pre-Pandemic Day",
        "measure": "Estimated Ridership",
        "unit": "estimated riders",
        "family": "ridership",
    },
]

SYSTEM_NAMES = [item["name"] for item in TRANSPORT_CONFIG]
SYSTEM_UNITS = {item["name"]: item["unit"] for item in TRANSPORT_CONFIG}
SYSTEM_FAMILIES = {item["name"]: item["family"] for item in TRANSPORT_CONFIG}


# ---------------------------------------------------------------------------
# Loading and reshaping
# ---------------------------------------------------------------------------
def load_cleaned() -> pd.DataFrame:
    """Load the Week 1 cleaned dataset with Date parsed, values unchanged."""
    df = pd.read_csv(CLEANED_PATH, parse_dates=["Date"])
    return df.sort_values("Date").reset_index(drop=True)


def build_long(wide: pd.DataFrame) -> pd.DataFrame:
    """Convert the 15-column wide table to one row per date x system."""
    frames = []
    for cfg in TRANSPORT_CONFIG:
        frames.append(
            pd.DataFrame(
                {
                    "date": wide["Date"],
                    "transport_id": cfg["id"],
                    "transport": cfg["name"],
                    "activity": wide[cfg["activity"]],
                    "recovery_pct": wide[cfg["pct"]],
                    "measure": cfg["measure"],
                    "unit": cfg["unit"],
                    "unit_family": cfg["family"],
                }
            )
        )
    long = pd.concat(frames, ignore_index=True)
    return long.sort_values(["transport_id", "date"]).reset_index(drop=True)


def quality_report(wide: pd.DataFrame) -> dict:
    """Return reproducible data-quality facts about the wide dataset."""
    dates = pd.to_datetime(wide["Date"])
    expected = pd.date_range(dates.min(), dates.max(), freq="D")
    numeric = wide.select_dtypes(include="number")
    return {
        "rows": len(wide),
        "columns": wide.shape[1],
        "date_min": dates.min(),
        "date_max": dates.max(),
        "calendar_days": len(expected),
        "gap_days": int(len(expected.difference(pd.DatetimeIndex(dates)))),
        "missing_values": int(wide.isna().sum().sum()),
        "duplicate_rows": int(wide.duplicated().sum()),
        "duplicate_dates": int(dates.duplicated().sum()),
        "negative_values": int((numeric < 0).sum().sum()),
        "zero_activity_rows": {
            cfg["name"]: int((wide[cfg["activity"]] == 0).sum())
            for cfg in TRANSPORT_CONFIG
        },
        "dtypes": {col: str(dtype) for col, dtype in wide.dtypes.items()},
    }


# ---------------------------------------------------------------------------
# Aggregations
# ---------------------------------------------------------------------------
def monthly_summary(long: pd.DataFrame) -> pd.DataFrame:
    """Monthly mean activity and recovery by system (units kept per system)."""
    out = long.assign(month=long["date"].dt.to_period("M")).copy()
    out = (
        out.groupby(["transport", "month"], as_index=False)
        .agg(
            activity_mean=("activity", "mean"),
            activity_median=("activity", "median"),
            recovery_mean=("recovery_pct", "mean"),
            days=("activity", "size"),
        )
    )
    out["month_start"] = out["month"].dt.to_timestamp()
    return out.sort_values(["transport", "month_start"]).reset_index(drop=True)


def day_type_summary(long: pd.DataFrame) -> pd.DataFrame:
    """Weekday/weekend means by system, with zeros retained."""
    out = long.assign(
        day_type=np.where(long["date"].dt.dayofweek < 5, "Weekday", "Weekend")
    )
    out = (
        out.groupby(["transport", "day_type"], as_index=False)
        .agg(
            mean_activity=("activity", "mean"),
            median_activity=("activity", "median"),
            mean_recovery=("recovery_pct", "mean"),
            days=("activity", "size"),
        )
    )
    return out.sort_values(["transport", "day_type"]).reset_index(drop=True)


def seasonality_index(long: pd.DataFrame) -> pd.DataFrame:
    """Mean activity by calendar month, indexed to each year's own mean (100).

    Indexing within each year removes much of the 2020-2024 recovery trend, so
    recurring month-of-year effects are easier to see. Zeros are retained.
    """
    out = long.copy()
    out["year"] = out["date"].dt.year
    out["month_num"] = out["date"].dt.month
    year_mean = out.groupby(["transport", "year"])["activity"].transform("mean")
    out["activity_index"] = 100 * out["activity"] / year_mean
    season = (
        out.groupby(["transport", "month_num"])["activity_index"]
        .mean()
        .unstack("month_num")
        .reindex(SYSTEM_NAMES)
    )
    season.columns = [
        pd.Timestamp(2020, int(month), 1).strftime("%b") for month in season.columns
    ]
    return season


def day_of_month_pattern(long: pd.DataFrame) -> pd.DataFrame:
    """Mean recovery percentage by system and weekday name."""
    out = long.assign(day_name=long["date"].dt.day_name()).copy()
    out = (
        out.groupby(["transport", "day_name"], as_index=False)
        .agg(mean_recovery=("recovery_pct", "mean"), mean_activity=("activity", "mean"))
    )
    order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    out["day_name"] = pd.Categorical(out["day_name"], categories=order, ordered=True)
    return out.sort_values(["transport", "day_name"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# System-level metrics
# ---------------------------------------------------------------------------
def _period_mask(dates: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
    return (dates >= start) & (dates <= end)


def system_metrics(long: pd.DataFrame) -> pd.DataFrame:
    """Compute comparable, unit-free metrics for each transportation system."""
    rows = []
    for cfg in TRANSPORT_CONFIG:
        sub = long[long["transport"] == cfg["name"]].sort_values("date").copy()
        mean_activity = sub["activity"].mean()

        early = sub[_period_mask(sub["date"], EARLY_START, EARLY_END)]
        first12 = sub[_period_mask(sub["date"], FIRST_12_START, FIRST_12_END)]
        late = sub[_period_mask(sub["date"], LATE_START, LATE_END)]

        roll7 = sub["recovery_pct"].rolling(7, min_periods=7).mean()
        above = roll7 >= 100
        # First day of a 14-day run: the rolling sum at t+13 covers t..t+13.
        forward_run = (above.rolling(14).sum() == 14).shift(-13)
        sustained = above & forward_run
        crossing = sub.loc[sustained, "date"]
        crossing_date = crossing.min() if not crossing.empty else pd.NaT

        daily_above = sub["recovery_pct"] >= 100
        first_daily_100 = sub.loc[daily_above, "date"]
        first_roll7_100 = sub.loc[above, "date"]
        flags = daily_above.to_numpy()
        longest_streak = 0
        current_streak = 0
        for flag in flags:
            current_streak = current_streak + 1 if flag else 0
            longest_streak = max(longest_streak, current_streak)

        rel_change = sub["activity"].diff() / mean_activity

        above100 = sub[sub["recovery_pct"] > 100]
        max_idx = sub["recovery_pct"].idxmax()
        min_idx = sub["recovery_pct"].idxmin()

        rows.append(
            {
                "transport": cfg["name"],
                "measure": cfg["measure"],
                "unit": cfg["unit"],
                "unit_family": cfg["family"],
                "days": len(sub),
                "mean_activity": mean_activity,
                "median_activity": sub["activity"].median(),
                "std_activity": sub["activity"].std(),
                "cv_activity": sub["activity"].std() / mean_activity,
                "daily_change_volatility": rel_change.std(),
                "early_recovery_mean": early["recovery_pct"].mean(),
                "early_recovery_min": early["recovery_pct"].min(),
                "full_recovery_min": sub["recovery_pct"].min(),
                "full_recovery_min_date": sub.loc[min_idx, "date"],
                "full_recovery_mean": sub["recovery_pct"].mean(),
                "first12_activity_mean": first12["activity"].mean(),
                "late_activity_mean": late["activity"].mean(),
                "period_change_pct": (
                    late["activity"].mean() / first12["activity"].mean() - 1
                )
                * 100,
                "late_recovery_mean": late["recovery_pct"].mean(),
                "sustained_100_date": crossing_date,
                "first_daily_100_date": (
                    first_daily_100.min() if not first_daily_100.empty else pd.NaT
                ),
                "first_roll7_100_date": (
                    first_roll7_100.min() if not first_roll7_100.empty else pd.NaT
                ),
                "longest_daily_100_streak": longest_streak,
                "late_share_above_100_pct": 100
                * (late["recovery_pct"] > 100).mean(),
                "days_above_100": len(above100),
                "share_above_100_pct": 100 * len(above100) / len(sub),
                "max_recovery": sub.loc[max_idx, "recovery_pct"],
                "max_recovery_date": sub.loc[max_idx, "date"],
                "zero_activity_days": int((sub["activity"] == 0).sum()),
            }
        )
    return pd.DataFrame(rows).set_index("transport").loc[SYSTEM_NAMES].reset_index()


# ---------------------------------------------------------------------------
# Relationships and anomalies
# ---------------------------------------------------------------------------
def correlation_analysis(long: pd.DataFrame) -> dict:
    """Correlations from unit-free versions of the activity series.

    Level correlation uses Spearman rank correlation of raw daily activity.
    Smoothed correlation uses Pearson correlation of 7-day means of activity
    divided by each system's own mean. Change correlation uses Pearson
    correlation of daily activity changes divided by each system's own mean.
    Correlation is association only, not causation.
    """
    levels = long.pivot(index="date", columns="transport", values="activity")
    spearman_levels = levels.corr(method="spearman")

    norm = long.copy()
    system_mean = norm.groupby("transport")["activity"].transform("mean")
    norm["activity_index"] = norm["activity"] / system_mean
    norm["rolling7_index"] = norm.groupby("transport")["activity_index"].transform(
        lambda s: s.rolling(7, min_periods=7).mean()
    )
    norm["daily_rel_change"] = norm.groupby("transport")["activity"].transform(
        lambda s: s.diff() / s.mean()
    )

    smoothed = norm.pivot(index="date", columns="transport", values="rolling7_index")
    changes = norm.pivot(index="date", columns="transport", values="daily_rel_change")
    pearson_smoothed = smoothed.corr()
    pearson_changes = changes.corr()

    return {
        "spearman_levels": spearman_levels.reindex(
            index=SYSTEM_NAMES, columns=SYSTEM_NAMES
        ),
        "pearson_smoothed": pearson_smoothed.reindex(
            index=SYSTEM_NAMES, columns=SYSTEM_NAMES
        ),
        "pearson_changes": pearson_changes.reindex(
            index=SYSTEM_NAMES, columns=SYSTEM_NAMES
        ),
    }


def anomaly_summary(long: pd.DataFrame) -> pd.DataFrame:
    """Largest positive and negative daily activity observations per system."""
    rows = []
    for cfg in TRANSPORT_CONFIG:
        sub = long[long["transport"] == cfg["name"]].sort_values("date")
        mean_activity = sub["activity"].mean()
        for kind, frame in (("high", sub.nlargest(3, "activity")), ("low", sub.nsmallest(3, "activity"))):
            for _, row in frame.iterrows():
                rows.append(
                    {
                        "transport": cfg["name"],
                        "kind": kind,
                        "date": row["date"],
                        "activity": row["activity"],
                        "recovery_pct": row["recovery_pct"],
                        "pct_of_system_mean": 100 * row["activity"] / mean_activity,
                    }
                )
    return pd.DataFrame(rows)


def methodology_window(long: pd.DataFrame) -> pd.DataFrame:
    """Same-calendar-month recovery means around the February 2023 change."""
    out = long.copy()
    months = out["date"].dt.to_period("M")
    pre = (months >= pd.Period("2022-02", "M")) & (months <= pd.Period("2023-01", "M"))
    post = (months >= pd.Period("2023-02", "M")) & (months <= pd.Period("2024-01", "M"))
    pre_frame = out[pre].groupby("transport", as_index=False).agg(
        pre_recovery=("recovery_pct", "mean"), pre_activity=("activity", "mean")
    )
    post_frame = out[post].groupby("transport", as_index=False).agg(
        post_recovery=("recovery_pct", "mean"), post_activity=("activity", "mean")
    )
    merged = pre_frame.merge(post_frame, on="transport")
    merged["recovery_pp_change"] = merged["post_recovery"] - merged["pre_recovery"]
    merged["activity_pct_change"] = (
        merged["post_activity"] / merged["pre_activity"] - 1
    ) * 100
    return merged.set_index("transport").loc[SYSTEM_NAMES].reset_index()


# ---------------------------------------------------------------------------
# Plotting style
# ---------------------------------------------------------------------------
def configure_plotting() -> None:
    """Apply one consistent Matplotlib style for all Week 2 charts."""
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "figure.figsize": (12, 6),
            "figure.dpi": 110,
            "savefig.dpi": 160,
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "axes.grid": True,
            "grid.alpha": 0.3,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "legend.frameon": False,
        }
    )


SYSTEM_COLORS = {
    "Subways": "#1f77b4",
    "Buses": "#ff7f0e",
    "LIRR": "#2ca02c",
    "Metro-North": "#9467bd",
    "Access-A-Ride": "#8c564b",
    "Bridges and Tunnels": "#17becf",
    "Staten Island Railway": "#d62728",
}
