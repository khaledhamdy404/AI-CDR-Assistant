"""
cdr_report.py
Module 5: Generate a professional PDF report from KPIs, charts, and AI insights.
"""
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Image as RLImage, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Rect
from cdr_kpis import fmt_duration


# ── Colour palette ──────────────────────────────────────────────────────────
C_BG       = colors.HexColor("#0d1117")
C_PANEL    = colors.HexColor("#161b22")
C_ACCENT1  = colors.HexColor("#00d4ff")
C_ACCENT2  = colors.HexColor("#7c3aed")
C_TEXT     = colors.HexColor("#e6edf3")
C_TEXT_DIM = colors.HexColor("#8b949e")
C_WHITE    = colors.white
C_DANGER   = colors.HexColor("#ef4444")
C_SUCCESS  = colors.HexColor("#10b981")
C_WARN     = colors.HexColor("#f59e0b")


def _styles():
    base = getSampleStyleSheet()
    custom = {}

    custom["title"] = ParagraphStyle(
        "title", parent=base["Title"],
        fontSize=26, textColor=C_ACCENT1, alignment=TA_CENTER,
        fontName="Helvetica-Bold", spaceAfter=6
    )
    custom["subtitle"] = ParagraphStyle(
        "subtitle", parent=base["Normal"],
        fontSize=11, textColor=C_TEXT_DIM, alignment=TA_CENTER,
        fontName="Helvetica", spaceAfter=20
    )
    custom["section"] = ParagraphStyle(
        "section", parent=base["Heading1"],
        fontSize=14, textColor=C_ACCENT1,
        fontName="Helvetica-Bold", spaceBefore=18, spaceAfter=8,
        borderPad=4,
    )
    custom["body"] = ParagraphStyle(
        "body", parent=base["Normal"],
        fontSize=10, textColor=C_TEXT,
        fontName="Helvetica", leading=16
    )
    custom["bullet"] = ParagraphStyle(
        "bullet", parent=base["Normal"],
        fontSize=10, textColor=C_TEXT,
        fontName="Helvetica", leading=16,
        leftIndent=14, bulletIndent=0
    )
    custom["kpi_label"] = ParagraphStyle(
        "kpi_label", parent=base["Normal"],
        fontSize=9, textColor=C_TEXT_DIM,
        fontName="Helvetica", alignment=TA_CENTER
    )
    custom["kpi_value"] = ParagraphStyle(
        "kpi_value", parent=base["Normal"],
        fontSize=18, textColor=C_ACCENT1,
        fontName="Helvetica-Bold", alignment=TA_CENTER
    )
    custom["insight"] = ParagraphStyle(
        "insight", parent=base["Normal"],
        fontSize=9.5, textColor=C_TEXT,
        fontName="Helvetica", leading=15,
        backColor=C_PANEL, borderPad=8
    )
    return custom


def _kpi_card_table(kpi_data: list) -> Table:
    """
    kpi_data: list of (label, value) tuples, 3 per row.
    """
    S = _styles()
    rows = []
    for i in range(0, len(kpi_data), 3):
        chunk = kpi_data[i:i+3]
        while len(chunk) < 3:
            chunk.append(("", ""))
        label_row = [Paragraph(label, S["kpi_label"]) for label, _ in chunk]
        value_row = [Paragraph(str(val), S["kpi_value"]) for _, val in chunk]
        rows.append(value_row)
        rows.append(label_row)

    t = Table(rows, colWidths=[5.5 * cm] * 3)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_PANEL),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [C_PANEL, C_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, C_PANEL),
        ("ROUNDEDCORNERS", [4]),
    ]))
    return t


def _branch_table(branch_df: pd.DataFrame) -> Table:
    S = _styles()
    header = ["Branch", "Total Calls", "Missed", "Missed %", "Avg Duration"]
    header_cells = [Paragraph(f"<b>{h}</b>", S["body"]) for h in header]
    rows = [header_cells]
    for _, row in branch_df.iterrows():
        missed_color = C_DANGER if row["MissedRate_%"] > 20 else (C_WARN if row["MissedRate_%"] > 10 else C_SUCCESS)
        rows.append([
            Paragraph(str(row["Branch"]), S["body"]),
            Paragraph(str(int(row["TotalCalls"])), S["body"]),
            Paragraph(str(int(row["MissedCalls"])), S["body"]),
            Paragraph(f'<font color="#{missed_color.hexval()[2:]}">{row["MissedRate_%"]}%</font>', S["body"]),
            Paragraph(f'{row["AvgDuration_min"]} min', S["body"]),
        ])
    t = Table(rows, colWidths=[4.5*cm, 3*cm, 3*cm, 3*cm, 3*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_ACCENT2),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_PANEL, C_BG]),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.5, C_PANEL),
    ]))
    return t


def generate_pdf_report(
    kpis: Dict,
    df: pd.DataFrame,
    chart_paths: Dict[str, str],
    insights: str,
    output_path: str = "reports/cdr_report.pdf"
) -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    S = _styles()
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title="CDR Analytics Report",
        author="CDR Analyzer System",
    )

    story = []
    avm = kpis.get("answered_vs_missed", {})
    missed_pct = avm.get("percentages", {}).get("Missed", 0)
    answered_pct = avm.get("percentages", {}).get("Answered", 0)
    now_str = datetime.now().strftime("%B %d, %Y  %H:%M")

    # ── Cover ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1.5*cm))
    story.append(Paragraph("CDR Analytics Report", S["title"]))
    story.append(Paragraph("Call Detail Records — AI-Powered Analysis", S["subtitle"]))
    story.append(Paragraph(f"Generated: {now_str}", S["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=C_ACCENT1, spaceAfter=20))

    # ── KPI Dashboard ────────────────────────────────────────────────────────
    story.append(Paragraph("KPI Dashboard", S["section"]))
    kpi_data = [
        ("Total Calls", f"{kpis.get('total_calls', 0):,}"),
        ("Total Duration", fmt_duration(kpis.get("total_duration_sec", 0))),
        ("Avg Duration", f"{kpis.get('avg_duration_min', 0)} min"),
        ("Missed Calls", f"{kpis.get('missed_calls', 0):,}"),
        ("Missed Rate", f"{missed_pct}%"),
        ("Answered Rate", f"{answered_pct}%"),
        ("Peak Hour", f"{kpis.get('busiest_hour', 0):02d}:00"),
        ("Peak Calls/hr", str(kpis.get("busiest_hour_count", 0))),
        ("Total Hours", f"{kpis.get('total_duration_hr', 0)} hr"),
    ]
    story.append(_kpi_card_table(kpi_data))
    story.append(Spacer(1, 0.5*cm))

    # ── Charts ───────────────────────────────────────────────────────────────
    chart_titles = {
        "calls_per_hour": "Call Volume by Hour",
        "calls_per_day": "Daily Call Volume",
        "top_extensions": "Top Extensions",
        "call_type_pie": "Call Type Distribution",
        "duration_histogram": "Duration Distribution",
    }
    story.append(Paragraph("Visual Analysis", S["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_PANEL, spaceAfter=8))

    for key, title in chart_titles.items():
        path = chart_paths.get(key, "")
        if path and Path(path).exists():
            story.append(Paragraph(title, S["body"]))
            img = RLImage(path, width=16*cm, height=7*cm, kind="proportional")
            story.append(img)
            story.append(Spacer(1, 0.4*cm))

    # ── Branch Performance ───────────────────────────────────────────────────
    branch_df = kpis.get("calls_per_branch", pd.DataFrame())
    if not branch_df.empty:
        story.append(PageBreak())
        story.append(Paragraph("Branch Performance", S["section"]))
        story.append(_branch_table(branch_df))
        story.append(Spacer(1, 0.5*cm))

    # ── Top Extensions ───────────────────────────────────────────────────────
    top_ext = kpis.get("top_extensions", pd.Series(dtype=int))
    if not top_ext.empty:
        story.append(Paragraph("Top 10 Extensions", S["section"]))
        ext_rows = [[Paragraph("<b>Extension</b>", S["body"]),
                     Paragraph("<b>Call Count</b>", S["body"])]]
        for ext, count in top_ext.items():
            ext_rows.append([Paragraph(str(ext), S["body"]), Paragraph(str(count), S["body"])])
        ext_table = Table(ext_rows, colWidths=[8*cm, 8*cm])
        ext_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), C_ACCENT2),
            ("TEXTCOLOR", (0, 0), (-1, 0), C_WHITE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_PANEL, C_BG]),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.5, C_PANEL),
        ]))
        story.append(ext_table)
        story.append(Spacer(1, 0.5*cm))

    # ── AI Insights ──────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("AI-Generated Insights", S["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_PANEL, spaceAfter=8))

    # Split insights into paragraphs and render cleanly
    for line in insights.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 0.2*cm))
            continue
        # Bold headings
        if line.startswith("#") or line.startswith("**") or line.startswith("═"):
            clean = line.strip("#* ═─")
            if clean:
                story.append(Paragraph(f"<b>{clean}</b>", S["section"]))
        elif line.startswith("•") or line.startswith("-") or line.startswith("*"):
            clean = line.lstrip("•-* ")
            story.append(Paragraph(f"• {clean}", S["bullet"]))
        else:
            story.append(Paragraph(line, S["body"]))

    # ── Footer note ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_PANEL))
    story.append(Paragraph(
        "Generated by CDR Analytics System | Powered by Claude AI",
        ParagraphStyle("footer", parent=S["body"], fontSize=8, textColor=C_TEXT_DIM, alignment=TA_CENTER)
    ))

    # Build with dark background
    def _dark_page(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(C_BG)
        canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        canvas.restoreState()

    doc.build(story, onFirstPage=_dark_page, onLaterPages=_dark_page)
    print(f"[✓] PDF report saved: {output_path}")
    return output_path
