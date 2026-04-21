"""
cdr_loader.py
Module 1: Load and preprocess CDR data from Excel.
"""
import pandas as pd
import numpy as np
from pathlib import Path


# ─────────────────────────────────────────────
# COLUMN ALIASES  — map common CDR column names
# to the internal standard names used here.
# Edit this dict to match YOUR Excel headers.
# ─────────────────────────────────────────────
COLUMN_MAP = {
    # DateTime variants
    "datetime": "DateTime",
    "date_time": "DateTime",
    "call_datetime": "DateTime",
    "call date": "DateTime",
    "date": "DateTime",
    "time": "DateTime",

    # Extension
    "ext": "Extension",
    "extension": "Extension",
    "exten": "Extension",
    "src": "Extension",
    "source": "Extension",
    "caller_extension": "Extension",

    # Duration
    "duration": "Duration_sec",
    "duration_sec": "Duration_sec",
    "billsec": "Duration_sec",
    "call_duration": "Duration_sec",
    "duration (sec)": "Duration_sec",
    "duration(s)": "Duration_sec",

    # Call type / disposition
    "calltype": "CallType",
    "call_type": "CallType",
    "type": "CallType",
    "disposition": "CallType",
    "status": "Status",
    "call_status": "Status",

    # Branch
    "branch": "Branch",
    "site": "Branch",
    "location": "Branch",
    "office": "Branch",

    # Numbers
    "callernumber": "CallerNumber",
    "caller": "CallerNumber",
    "src_number": "CallerNumber",
    "from": "CallerNumber",
    "calleenumber": "CalleeNumber",
    "callee": "CalleeNumber",
    "dst_number": "CalleeNumber",
    "to": "CalleeNumber",
    "dst": "CalleeNumber",
}


def load_excel(path: str) -> pd.DataFrame:
    """Load CDR data from an Excel file (.xlsx or .xls)."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Excel file not found: {path}")

    df = pd.read_excel(path, engine="openpyxl")
    print(f"[+] Loaded {len(df):,} rows × {len(df.columns)} columns from '{p.name}'")
    return df


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to internal standard names using COLUMN_MAP."""
    rename = {}
    for col in df.columns:
        key = col.strip().lower().replace(" ", "_")
        if key in COLUMN_MAP:
            rename[col] = COLUMN_MAP[key]
        elif col.strip().lower() in COLUMN_MAP:
            rename[col] = COLUMN_MAP[col.strip().lower()]
    if rename:
        df = df.rename(columns=rename)
        print(f"[+] Renamed columns: {rename}")
    return df


def parse_datetime(df: pd.DataFrame) -> pd.DataFrame:
    """Parse the DateTime column and extract time features."""
    if "DateTime" not in df.columns:
        # Try to combine separate Date + Time columns
        if "Date" in df.columns and "Time" in df.columns:
            df["DateTime"] = pd.to_datetime(
                df["Date"].astype(str) + " " + df["Time"].astype(str),
                errors="coerce"
            )
            print("[+] Combined 'Date' + 'Time' into 'DateTime'")
        else:
            print("[!] No DateTime column found — time-based KPIs will be skipped.")
            return df

    df["DateTime"] = pd.to_datetime(df["DateTime"], errors="coerce")
    invalid = df["DateTime"].isna().sum()
    if invalid:
        print(f"[!] {invalid} rows had unparseable DateTime — set to NaT")

    df["Hour"] = df["DateTime"].dt.hour
    df["DayOfWeek"] = df["DateTime"].dt.day_name()
    df["Date"] = df["DateTime"].dt.date
    df["Month"] = df["DateTime"].dt.to_period("M").astype(str)
    return df


def fix_duration(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure Duration_sec is numeric and non-negative."""
    if "Duration_sec" not in df.columns:
        # If start/end time columns exist, compute duration
        if "StartTime" in df.columns and "EndTime" in df.columns:
            df["StartTime"] = pd.to_datetime(df["StartTime"], errors="coerce")
            df["EndTime"] = pd.to_datetime(df["EndTime"], errors="coerce")
            df["Duration_sec"] = (df["EndTime"] - df["StartTime"]).dt.total_seconds()
            print("[+] Computed Duration_sec from StartTime / EndTime")
        else:
            df["Duration_sec"] = 0
            print("[!] No duration column found — defaulting to 0")
    else:
        df["Duration_sec"] = pd.to_numeric(df["Duration_sec"], errors="coerce").fillna(0)
        df["Duration_sec"] = df["Duration_sec"].clip(lower=0)

    df["Duration_min"] = (df["Duration_sec"] / 60).round(2)
    return df


def infer_status(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure a 'Status' column exists (Answered / Missed)."""
    if "Status" not in df.columns:
        if "CallType" in df.columns:
            df["Status"] = df["CallType"].apply(
                lambda x: "Missed" if str(x).lower() in ("missed", "no answer", "busy", "failed") else "Answered"
            )
            print("[+] Inferred 'Status' from 'CallType'")
        elif "Duration_sec" in df.columns:
            df["Status"] = df["Duration_sec"].apply(
                lambda d: "Missed" if d == 0 else "Answered"
            )
            print("[+] Inferred 'Status' from Duration_sec (0 = Missed)")
        else:
            df["Status"] = "Unknown"
    else:
        # Normalize
        df["Status"] = df["Status"].str.strip().str.title()
    return df


def handle_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values across the dataframe."""
    before = df.isnull().sum().sum()
    df["Extension"] = df["Extension"].fillna("Unknown") if "Extension" in df.columns else "Unknown"
    df["Branch"] = df["Branch"].fillna("Unknown") if "Branch" in df.columns else "Unknown"
    df["CallType"] = df["CallType"].fillna("Unknown") if "CallType" in df.columns else "Unknown"
    after = df.isnull().sum().sum()
    print(f"[+] Filled missing values ({before} → {after} nulls remaining)")
    return df


def preprocess(path: str) -> pd.DataFrame:
    """
    Full preprocessing pipeline.
    Returns a clean, enriched DataFrame ready for KPI calculation.
    """
    df = load_excel(path)
    df = normalize_columns(df)
    df = parse_datetime(df)
    df = fix_duration(df)
    df = infer_status(df)
    df = handle_missing(df)
    print(f"[✓] Preprocessing complete. Shape: {df.shape}")
    return df
