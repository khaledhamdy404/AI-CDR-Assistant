"""
cdr_kpis.py
Module 2: Calculate all KPIs from the preprocessed CDR DataFrame.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any


def total_calls(df: pd.DataFrame) -> int:
    return len(df)


def total_duration_seconds(df: pd.DataFrame) -> float:
    return df["Duration_sec"].sum() if "Duration_sec" in df.columns else 0


def average_duration_seconds(df: pd.DataFrame) -> float:
    answered = df[df["Status"] == "Answered"] if "Status" in df.columns else df
    return answered["Duration_sec"].mean() if "Duration_sec" in df.columns and len(answered) > 0 else 0


def missed_calls_count(df: pd.DataFrame) -> int:
    if "Status" not in df.columns:
        return 0
    return int((df["Status"].str.lower() == "missed").sum())


def answered_vs_missed(df: pd.DataFrame) -> Dict[str, Any]:
    if "Status" not in df.columns:
        return {}
    counts = df["Status"].value_counts().to_dict()
    total = len(df)
    ratios = {k: round(v / total * 100, 2) for k, v in counts.items()}
    return {"counts": counts, "percentages": ratios}


def peak_hours(df: pd.DataFrame, top_n: int = 3) -> pd.Series:
    """Returns calls-per-hour Series, sorted by hour."""
    if "Hour" not in df.columns:
        return pd.Series(dtype=int)
    hourly = df.groupby("Hour").size().reindex(range(0, 24), fill_value=0)
    return hourly


def top_extensions(df: pd.DataFrame, n: int = 10) -> pd.Series:
    if "Extension" not in df.columns:
        return pd.Series(dtype=int)
    return df["Extension"].value_counts().head(n)


def calls_per_branch(df: pd.DataFrame) -> pd.DataFrame:
    if "Branch" not in df.columns:
        return pd.DataFrame()
    branch_stats = df.groupby("Branch").agg(
        TotalCalls=("Branch", "count"),
        MissedCalls=("Status", lambda x: (x.str.lower() == "missed").sum()),
        AvgDuration_sec=("Duration_sec", "mean"),
        TotalDuration_sec=("Duration_sec", "sum"),
    ).reset_index()
    branch_stats["MissedRate_%"] = (
        branch_stats["MissedCalls"] / branch_stats["TotalCalls"] * 100
    ).round(2)
    branch_stats["AvgDuration_min"] = (branch_stats["AvgDuration_sec"] / 60).round(2)
    return branch_stats.sort_values("TotalCalls", ascending=False)


def calls_per_day(df: pd.DataFrame) -> pd.Series:
    if "Date" not in df.columns:
        return pd.Series(dtype=int)
    return df.groupby("Date").size().sort_index()


def call_type_distribution(df: pd.DataFrame) -> pd.Series:
    if "CallType" not in df.columns:
        return pd.Series(dtype=int)
    return df["CallType"].value_counts()


def duration_stats(df: pd.DataFrame) -> Dict[str, float]:
    if "Duration_sec" not in df.columns:
        return {}
    s = df["Duration_sec"]
    return {
        "min_sec": float(s.min()),
        "max_sec": float(s.max()),
        "mean_sec": float(s.mean()),
        "median_sec": float(s.median()),
        "std_sec": float(s.std()),
        "p95_sec": float(s.quantile(0.95)),
    }


def compute_all_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Master function — returns a dict with every KPI.
    Call this once and pass the result to the reporting/AI modules.
    """
    kpis = {}
    kpis["total_calls"] = total_calls(df)
    kpis["total_duration_sec"] = total_duration_seconds(df)
    kpis["total_duration_min"] = round(kpis["total_duration_sec"] / 60, 2)
    kpis["total_duration_hr"] = round(kpis["total_duration_sec"] / 3600, 2)
    kpis["avg_duration_sec"] = round(average_duration_seconds(df), 2)
    kpis["avg_duration_min"] = round(kpis["avg_duration_sec"] / 60, 2)
    kpis["missed_calls"] = missed_calls_count(df)
    kpis["answered_vs_missed"] = answered_vs_missed(df)
    kpis["peak_hours"] = peak_hours(df)
    kpis["top_extensions"] = top_extensions(df, n=10)
    kpis["calls_per_branch"] = calls_per_branch(df)
    kpis["calls_per_day"] = calls_per_day(df)
    kpis["call_type_dist"] = call_type_distribution(df)
    kpis["duration_stats"] = duration_stats(df)

    # Busiest hour(s)
    if not kpis["peak_hours"].empty:
        kpis["busiest_hour"] = int(kpis["peak_hours"].idxmax())
        kpis["busiest_hour_count"] = int(kpis["peak_hours"].max())

    print("[✓] KPI calculation complete.")
    return kpis


def fmt_duration(seconds: float) -> str:
    """Format seconds into Xh Ym Zs string."""
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    parts = []
    if h:
        parts.append(f"{h}h")
    if m:
        parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts) or "0s"
