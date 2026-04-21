"""
cdr_ai.py
Module 4: AI-powered insights using Claude API.
Generates natural-language analysis, anomaly detection, and branch comparison.
"""
import json
import re
from typing import Dict, Any
import pandas as pd
from cdr_kpis import fmt_duration


def _build_kpi_summary(kpis: Dict) -> str:
    """Convert KPIs into a clean text block to feed to Claude."""
    avm = kpis.get("answered_vs_missed", {})
    missed_pct = avm.get("percentages", {}).get("Missed", 0)
    answered_pct = avm.get("percentages", {}).get("Answered", 0)

    branch_df: pd.DataFrame = kpis.get("calls_per_branch", pd.DataFrame())
    branch_text = ""
    if not branch_df.empty:
        branch_text = "Branch Performance:\n"
        for _, row in branch_df.iterrows():
            branch_text += (
                f"  • {row['Branch']}: {int(row['TotalCalls'])} calls, "
                f"{row['MissedRate_%']}% missed, "
                f"avg duration {row['AvgDuration_min']} min\n"
            )

    top_ext = kpis.get("top_extensions", pd.Series(dtype=int))
    top_ext_text = ""
    if not top_ext.empty:
        top_ext_text = "Top Extensions by call volume:\n"
        for ext, count in top_ext.items():
            top_ext_text += f"  • Extension {ext}: {count} calls\n"

    hourly = kpis.get("peak_hours", pd.Series(dtype=int))
    peak_hours_text = ""
    if not hourly.empty:
        top3 = hourly.nlargest(3)
        peak_hours_text = "Peak hours: " + ", ".join(
            [f"{int(h):02d}:00 ({int(v)} calls)" for h, v in top3.items()]
        )

    summary = f"""
CDR Analytics Summary
─────────────────────
Total Calls: {kpis.get('total_calls', 0):,}
Total Duration: {fmt_duration(kpis.get('total_duration_sec', 0))} ({kpis.get('total_duration_hr', 0)} hours)
Average Duration (answered): {kpis.get('avg_duration_min', 0)} minutes
Missed Calls: {kpis.get('missed_calls', 0):,} ({missed_pct}%)
Answered Calls: {avm.get('counts', {}).get('Answered', 0):,} ({answered_pct}%)
Busiest Hour: {kpis.get('busiest_hour', 'N/A'):02}:00 ({kpis.get('busiest_hour_count', 0)} calls)

{peak_hours_text}

{branch_text}
{top_ext_text}
""".strip()
    return summary


def get_ai_insights(kpis: Dict, df: pd.DataFrame) -> str:
    """
    Call Claude API to generate insights from the KPI summary.
    Returns a formatted string with insights.
    """
    try:
        import anthropic
    except ImportError:
        return _fallback_insights(kpis)

    kpi_summary = _build_kpi_summary(kpis)

    prompt = f"""You are a senior telecom analyst reviewing CDR (Call Detail Records) data for a business.
    
Here is the KPI summary:

{kpi_summary}

Please provide:
1. **Executive Summary** (2-3 sentences)
2. **Key Findings** (3-5 bullet points with specific numbers)
3. **Anomalies Detected** (flag anything unusual — high missed call rates, extreme peaks, underperforming branches)
4. **Peak Usage Pattern** (describe when the system is busiest and what that means operationally)
5. **Branch Performance Comparison** (rank branches, identify best/worst performers, suggest actions)
6. **Actionable Recommendations** (3-5 specific, practical suggestions)

Be concise, data-driven, and business-focused. Use the actual numbers from the summary."""

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        insights = response.content[0].text
        print("[✓] AI insights generated via Claude API.")
        return insights
    except Exception as e:
        print(f"[!] Claude API call failed: {e}")
        return _fallback_insights(kpis)


def _fallback_insights(kpis: Dict) -> str:
    """
    Rule-based insights when the Claude API is unavailable.
    Provides useful analysis without any external dependency.
    """
    lines = ["═" * 60, "  AI INSIGHTS (Rule-Based)", "═" * 60, ""]

    total = kpis.get("total_calls", 0)
    missed = kpis.get("missed_calls", 0)
    avg_min = kpis.get("avg_duration_min", 0)
    busiest_h = kpis.get("busiest_hour", None)
    avm = kpis.get("answered_vs_missed", {})
    missed_pct = avm.get("percentages", {}).get("Missed", 0)

    lines.append("📋 Executive Summary")
    lines.append(f"   The system handled {total:,} total calls with an average answered duration of {avg_min} minutes.")

    lines.append("\n🔍 Key Findings")
    lines.append(f"   • Total calls processed: {total:,}")
    lines.append(f"   • Missed call rate: {missed_pct}% ({missed:,} calls)")
    lines.append(f"   • Average call duration: {avg_min} min")
    if busiest_h is not None:
        lines.append(f"   • Peak hour: {busiest_h:02d}:00")

    lines.append("\n⚠️  Anomalies")
    if missed_pct > 20:
        lines.append(f"   ‼️  HIGH MISSED CALL RATE: {missed_pct}% exceeds the 20% threshold.")
        lines.append("      Investigate staffing levels and call routing during peak hours.")
    elif missed_pct > 10:
        lines.append(f"   ⚠️  Elevated missed call rate: {missed_pct}%. Consider adding capacity.")
    else:
        lines.append(f"   ✅  Missed call rate ({missed_pct}%) is within acceptable range.")

    if avg_min > 15:
        lines.append(f"   ⚠️  Long average duration ({avg_min} min). Review escalation procedures.")

    branch_df: pd.DataFrame = kpis.get("calls_per_branch", pd.DataFrame())
    if not branch_df.empty:
        lines.append("\n🏢 Branch Performance")
        best = branch_df.iloc[0]
        worst = branch_df.iloc[-1]
        lines.append(f"   🥇 Highest volume: {best['Branch']} ({int(best['TotalCalls'])} calls, {best['MissedRate_%']}% missed)")
        if len(branch_df) > 1:
            lines.append(f"   🔴 Lowest volume: {worst['Branch']} ({int(worst['TotalCalls'])} calls, {worst['MissedRate_%']}% missed)")
        high_missed = branch_df[branch_df["MissedRate_%"] > 20]
        for _, row in high_missed.iterrows():
            lines.append(f"   ‼️  {row['Branch']}: {row['MissedRate_%']}% missed rate — needs attention")

    lines.append("\n💡 Recommendations")
    if missed_pct > 10:
        lines.append("   1. Review call routing during peak hours to reduce missed calls.")
    lines.append("   2. Schedule staff training and breaks during low-traffic windows.")
    if busiest_h is not None:
        lines.append(f"   3. Ensure maximum staffing around {busiest_h:02d}:00 (peak hour).")
    lines.append("   4. Set up automated callbacks for all missed calls.")
    lines.append("   5. Review branches with >20% missed rate for capacity issues.")

    lines.append("\n" + "═" * 60)
    return "\n".join(lines)


def print_insights(insights: str) -> None:
    """Pretty-print insights to the console."""
    print("\n")
    print(insights)
    print("\n")
