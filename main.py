"""
main.py
CDR Analytics System — Main Entry Point
────────────────────────────────────────
Usage:
    python main.py                          # uses default data/sample_cdr.xlsx
    python main.py path/to/your_cdr.xlsx    # your own Excel file
    python main.py path/to/cdr.xlsx --no-ai # skip Claude API, use rule-based insights
"""
import sys
import argparse
from pathlib import Path


def banner():
    print("""
╔══════════════════════════════════════════════════════════╗
║          CDR ANALYTICS SYSTEM  v1.0                     ║
║          Powered by Claude AI  |  @khaledhamdy404       ║
╚══════════════════════════════════════════════════════════╝
""")


def parse_args():
    parser = argparse.ArgumentParser(description="CDR Analytics System")
    parser.add_argument(
        "excel_file",
        nargs="?",
        default="data/sample_cdr.xlsx",
        help="Path to the CDR Excel file (default: data/sample_cdr.xlsx)"
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Skip Claude API and use rule-based insights only"
    )
    parser.add_argument(
        "--charts-dir",
        default="charts",
        help="Directory to save chart images (default: charts/)"
    )
    parser.add_argument(
        "--report-dir",
        default="reports",
        help="Directory to save the PDF report (default: reports/)"
    )
    return parser.parse_args()


def main():
    banner()
    args = parse_args()

    excel_path = args.excel_file
    charts_dir = args.charts_dir
    report_path = str(Path(args.report_dir) / "cdr_report.pdf")

    # ── Step 0: Generate sample data if needed ───────────────────────────────
    if not Path(excel_path).exists() and excel_path == "data/sample_cdr.xlsx":
        print("[~] Sample CDR file not found — generating one now...")
        from generate_sample_data import generate_cdr_data
        Path("data").mkdir(exist_ok=True)
        generate_cdr_data(n=500, output_path=excel_path)

    # ── Step 1: Load & preprocess ────────────────────────────────────────────
    print("\n[1/5] Loading and preprocessing data...")
    from cdr_loader import preprocess
    df = preprocess(excel_path)

    # ── Step 2: Calculate KPIs ───────────────────────────────────────────────
    print("\n[2/5] Calculating KPIs...")
    from cdr_kpis import compute_all_kpis, fmt_duration
    kpis = compute_all_kpis(df)

    # ── Print KPI summary to console ─────────────────────────────────────────
    avm = kpis.get("answered_vs_missed", {})
    missed_pct = avm.get("percentages", {}).get("Missed", 0)
    answered_pct = avm.get("percentages", {}).get("Answered", 0)

    print(f"""
  ┌─────────────────────────────────────────┐
  │  QUICK KPI SNAPSHOT                     │
  ├─────────────────────────────────────────┤
  │  Total Calls       : {kpis['total_calls']:>8,}            │
  │  Total Duration    : {fmt_duration(kpis['total_duration_sec']):>12}        │
  │  Avg Duration      : {kpis['avg_duration_min']:>8} min          │
  │  Missed Calls      : {kpis['missed_calls']:>8,} ({missed_pct}%)       │
  │  Answered Calls    : {avm.get('counts',{}).get('Answered',0):>8,} ({answered_pct}%)      │
  │  Peak Hour         : {kpis.get('busiest_hour',0):>8}:00             │
  └─────────────────────────────────────────┘""")

    # ── Step 3: Generate charts ──────────────────────────────────────────────
    print("\n[3/5] Generating charts...")
    from cdr_charts import generate_all_charts
    chart_paths = generate_all_charts(df, kpis, output_dir=charts_dir)

    # ── Step 4: AI insights ──────────────────────────────────────────────────
    print("\n[4/5] Generating AI insights...")
    from cdr_ai import get_ai_insights, print_insights, _fallback_insights
    if args.no_ai:
        insights = _fallback_insights(kpis)
    else:
        insights = get_ai_insights(kpis, df)
    print_insights(insights)

    # ── Step 5: PDF report ───────────────────────────────────────────────────
    print("\n[5/5] Building PDF report...")
    from cdr_report import generate_pdf_report
    generate_pdf_report(kpis, df, chart_paths, insights, output_path=report_path)

    # ── Done ─────────────────────────────────────────────────────────────────
    print(f"""
╔══════════════════════════════════════════════════════════╗
║  ✅  ANALYSIS COMPLETE                                   ║
╠══════════════════════════════════════════════════════════╣
║  Charts  : {charts_dir}/                                  
║  Report  : {report_path}                
╚══════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    main()
