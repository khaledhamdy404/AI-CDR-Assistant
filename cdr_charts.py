"""
cdr_charts.py
Module 3: Generate and save all charts using matplotlib / seaborn.
"""
import matplotlib
matplotlib.use("Agg")  # headless rendering — no display needed
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any

# ── Global style ──────────────────────────────
PALETTE = {
    "bg": "#0d1117",
    "panel": "#161b22",
    "accent1": "#00d4ff",
    "accent2": "#7c3aed",
    "accent3": "#10b981",
    "accent4": "#f59e0b",
    "danger": "#ef4444",
    "text": "#e6edf3",
    "grid": "#30363d",
}

def _apply_dark_style(fig, ax_list):
    fig.patch.set_facecolor(PALETTE["bg"])
    for ax in (ax_list if isinstance(ax_list, (list, tuple)) else [ax_list]):
        ax.set_facecolor(PALETTE["panel"])
        ax.tick_params(colors=PALETTE["text"], labelsize=9)
        ax.xaxis.label.set_color(PALETTE["text"])
        ax.yaxis.label.set_color(PALETTE["text"])
        ax.title.set_color(PALETTE["text"])
        for spine in ax.spines.values():
            spine.set_edgecolor(PALETTE["grid"])
        ax.grid(color=PALETTE["grid"], linestyle="--", linewidth=0.5, alpha=0.7)


def chart_calls_per_hour(kpis: Dict, output_dir: str) -> str:
    """Line chart: Calls per hour (0-23)."""
    hourly = kpis.get("peak_hours", pd.Series(dtype=int))
    if hourly.empty:
        return ""

    fig, ax = plt.subplots(figsize=(12, 5))
    _apply_dark_style(fig, ax)

    hours = list(hourly.index)
    counts = list(hourly.values)

    ax.plot(hours, counts, color=PALETTE["accent1"], linewidth=2.5, zorder=3)
    ax.fill_between(hours, counts, alpha=0.18, color=PALETTE["accent1"])

    # Mark peak
    peak_h = int(hourly.idxmax())
    peak_v = int(hourly.max())
    ax.annotate(
        f"Peak: {peak_h:02d}:00\n({peak_v} calls)",
        xy=(peak_h, peak_v),
        xytext=(peak_h + 1.5, peak_v * 0.85),
        color=PALETTE["accent4"],
        fontsize=9,
        arrowprops=dict(arrowstyle="->", color=PALETTE["accent4"]),
    )

    ax.set_xticks(range(0, 24))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(24)], rotation=45, ha="right", fontsize=7)
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Number of Calls")
    ax.set_title("📞  Call Volume by Hour", fontsize=14, pad=12)

    plt.tight_layout()
    path = str(Path(output_dir) / "01_calls_per_hour.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[+] Chart saved: {path}")
    return path


def chart_calls_per_day(kpis: Dict, output_dir: str) -> str:
    """Bar chart: Calls per calendar day."""
    daily = kpis.get("calls_per_day", pd.Series(dtype=int))
    if daily.empty:
        return ""

    fig, ax = plt.subplots(figsize=(14, 5))
    _apply_dark_style(fig, ax)

    dates = [str(d) for d in daily.index]
    counts = list(daily.values)
    colors = [PALETTE["accent2"] if c >= np.percentile(counts, 80) else PALETTE["accent1"] for c in counts]

    bars = ax.bar(range(len(dates)), counts, color=colors, width=0.7)

    # Show only every Nth label to avoid overlap
    step = max(1, len(dates) // 20)
    ax.set_xticks(range(0, len(dates), step))
    ax.set_xticklabels([dates[i] for i in range(0, len(dates), step)], rotation=45, ha="right", fontsize=7)
    ax.set_xlabel("Date")
    ax.set_ylabel("Number of Calls")
    ax.set_title("📅  Daily Call Volume", fontsize=14, pad=12)

    # Rolling average overlay
    if len(counts) >= 7:
        rolling = pd.Series(counts).rolling(7, center=True).mean()
        ax.plot(range(len(counts)), rolling, color=PALETTE["accent4"], linewidth=2, label="7-day avg", zorder=5)
        ax.legend(facecolor=PALETTE["panel"], labelcolor=PALETTE["text"], fontsize=9)

    plt.tight_layout()
    path = str(Path(output_dir) / "02_calls_per_day.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[+] Chart saved: {path}")
    return path


def chart_top_extensions(kpis: Dict, output_dir: str) -> str:
    """Horizontal bar chart: Top 10 extensions by call count."""
    top_ext = kpis.get("top_extensions", pd.Series(dtype=int))
    if top_ext.empty:
        return ""

    fig, ax = plt.subplots(figsize=(10, 6))
    _apply_dark_style(fig, ax)

    labels = [str(x) for x in top_ext.index]
    values = list(top_ext.values)

    bar_colors = sns.color_palette("cool", len(labels))
    bars = ax.barh(labels[::-1], values[::-1], color=bar_colors[::-1])

    for bar, val in zip(bars, values[::-1]):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", color=PALETTE["text"], fontsize=9)

    ax.set_xlabel("Number of Calls")
    ax.set_title("🏆  Top 10 Extensions by Call Volume", fontsize=14, pad=12)
    ax.grid(axis="x")

    plt.tight_layout()
    path = str(Path(output_dir) / "03_top_extensions.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[+] Chart saved: {path}")
    return path


def chart_call_type_pie(kpis: Dict, output_dir: str) -> str:
    """Donut / pie chart: Call type distribution."""
    dist = kpis.get("call_type_dist", pd.Series(dtype=int))
    if dist.empty:
        return ""

    fig, ax = plt.subplots(figsize=(8, 8))
    fig.patch.set_facecolor(PALETTE["bg"])
    ax.set_facecolor(PALETTE["bg"])

    colors = [PALETTE["accent1"], PALETTE["accent2"], PALETTE["accent3"], PALETTE["accent4"], PALETTE["danger"]]
    wedge_props = dict(width=0.5, edgecolor=PALETTE["bg"], linewidth=2)

    wedges, texts, autotexts = ax.pie(
        dist.values,
        labels=dist.index,
        autopct="%1.1f%%",
        colors=colors[:len(dist)],
        startangle=140,
        wedgeprops=wedge_props,
        textprops={"color": PALETTE["text"]},
    )
    for at in autotexts:
        at.set_fontsize(10)
        at.set_color(PALETTE["bg"])

    ax.set_title("📊  Call Type Distribution", fontsize=14, pad=20, color=PALETTE["text"])

    plt.tight_layout()
    path = str(Path(output_dir) / "04_call_type_pie.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[+] Chart saved: {path}")
    return path


def chart_duration_histogram(df: pd.DataFrame, output_dir: str) -> str:
    """Histogram: Call duration distribution (answered calls only)."""
    if "Duration_sec" not in df.columns:
        return ""

    answered = df[(df["Status"] == "Answered") & (df["Duration_sec"] > 0)]["Duration_sec"] / 60
    if answered.empty:
        return ""

    fig, ax = plt.subplots(figsize=(10, 5))
    _apply_dark_style(fig, ax)

    # Clip extreme outliers for display
    p99 = answered.quantile(0.99)
    clipped = answered.clip(upper=p99)

    ax.hist(clipped, bins=40, color=PALETTE["accent3"], edgecolor=PALETTE["bg"], alpha=0.85)

    mean_val = answered.mean()
    median_val = answered.median()
    ax.axvline(mean_val, color=PALETTE["accent4"], linestyle="--", linewidth=1.5, label=f"Mean: {mean_val:.1f} min")
    ax.axvline(median_val, color=PALETTE["danger"], linestyle="--", linewidth=1.5, label=f"Median: {median_val:.1f} min")

    ax.set_xlabel("Call Duration (minutes)")
    ax.set_ylabel("Number of Calls")
    ax.set_title("⏱️  Call Duration Distribution", fontsize=14, pad=12)
    ax.legend(facecolor=PALETTE["panel"], labelcolor=PALETTE["text"], fontsize=9)

    plt.tight_layout()
    path = str(Path(output_dir) / "05_duration_histogram.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[+] Chart saved: {path}")
    return path


def generate_all_charts(df: pd.DataFrame, kpis: Dict, output_dir: str = "charts") -> Dict[str, str]:
    """Generate all charts and return a dict of {name: filepath}."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    paths = {}
    paths["calls_per_hour"] = chart_calls_per_hour(kpis, output_dir)
    paths["calls_per_day"] = chart_calls_per_day(kpis, output_dir)
    paths["top_extensions"] = chart_top_extensions(kpis, output_dir)
    paths["call_type_pie"] = chart_call_type_pie(kpis, output_dir)
    paths["duration_histogram"] = chart_duration_histogram(df, output_dir)
    print(f"[✓] All charts saved to '{output_dir}/'")
    return {k: v for k, v in paths.items() if v}  # remove empty paths
