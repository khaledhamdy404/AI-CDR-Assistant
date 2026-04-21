"""
CDR Analytics Dashboard — Production Version
=============================================
Upgrade over baseline: error handling, spinner, branding, professional UI.
Core logic is unchanged — only usability and robustness improved.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import traceback

# ── Page config (must be first Streamlit call) ─────────────────────────────
st.set_page_config(
    page_title="CDR Analytics Dashboard",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS — clean, professional, enterprise-grade ─────────────────────
st.markdown("""
<style>
    /* ── Fonts & base ── */
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }

    /* ── App background ── */
    .stApp {
        background: #F4F6F9;
    }

    /* ── Header banner ── */
    .brand-header {
        background: linear-gradient(135deg, #0F2B5B 0%, #1A4A8A 60%, #1565C0 100%);
        border-radius: 12px;
        padding: 28px 36px;
        margin-bottom: 28px;
        display: flex;
        align-items: center;
        gap: 20px;
        box-shadow: 0 4px 20px rgba(15,43,91,0.25);
    }
    .brand-logo {
        font-size: 3rem;
        line-height: 1;
    }
    .brand-text h1 {
        color: #FFFFFF;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.3px;
    }
    .brand-text p {
        color: #90CAF9;
        font-size: 0.9rem;
        margin: 4px 0 0 0;
        font-weight: 300;
    }

    /* ── Section headings ── */
    .section-title {
        font-size: 1rem;
        font-weight: 600;
        color: #0F2B5B;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        padding-bottom: 8px;
        border-bottom: 2px solid #1565C0;
        margin: 24px 0 16px 0;
    }

    /* ── KPI cards ── */
    .kpi-card {
        background: #FFFFFF;
        border-radius: 10px;
        padding: 20px 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
        border-left: 4px solid #1565C0;
        height: 100%;
    }
    .kpi-card.green  { border-left-color: #2E7D32; }
    .kpi-card.amber  { border-left-color: #F57F17; }
    .kpi-card.red    { border-left-color: #C62828; }
    .kpi-card.purple { border-left-color: #6A1B9A; }
    .kpi-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: #78909C;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #0F2B5B;
        font-family: 'IBM Plex Mono', monospace;
        line-height: 1.1;
    }
    .kpi-sub {
        font-size: 0.78rem;
        color: #90A4AE;
        margin-top: 4px;
    }

    /* ── Info / instruction box ── */
    .info-box {
        background: #E3F2FD;
        border: 1px solid #90CAF9;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 20px;
        color: #0D47A1;
        font-size: 0.88rem;
        line-height: 1.6;
    }
    .info-box strong { color: #0F2B5B; }

    /* ── Chart containers ── */
    .chart-card {
        background: #FFFFFF;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin-bottom: 16px;
    }

    /* ── Status badges ── */
    .badge-success {
        background: #E8F5E9; color: #1B5E20;
        border-radius: 20px; padding: 4px 12px;
        font-size: 0.78rem; font-weight: 600;
        display: inline-block;
    }
    .badge-error {
        background: #FFEBEE; color: #B71C1C;
        border-radius: 20px; padding: 4px 12px;
        font-size: 0.78rem; font-weight: 600;
        display: inline-block;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: #0F2B5B;
    }
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stMultiSelect label {
        color: #CFD8DC !important;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #FFFFFF !important;
    }

    /* ── Divider ── */
    hr { border-color: #E0E7EF; margin: 24px 0; }

    /* ── Upload area ── */
    [data-testid="stFileUploader"] {
        background: #FFFFFF;
        border-radius: 10px;
        padding: 8px;
    }

    /* ── Dataframe ── */
    .stDataFrame { border-radius: 8px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS — adjust to match your actual Excel column names
# ══════════════════════════════════════════════════════════════════════════════
REQUIRED_COLUMNS = {
    "caller":    ["Caller", "caller", "CALLER", "From", "A_Number"],
    "callee":    ["Callee", "callee", "CALLEE", "To",   "B_Number"],
    "duration":  ["Duration", "duration", "DURATION", "Call Duration", "dur"],
    "datetime":  ["DateTime", "datetime", "Date Time", "Call Date", "StartTime", "Timestamp"],
    "call_type": ["CallType", "call_type", "Type", "Direction", "Call Type"],
}

CHART_COLORS = ["#1565C0", "#2E7D32", "#F57F17", "#6A1B9A", "#C62828", "#00838F"]


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def resolve_column(df: pd.DataFrame, aliases: list[str]) -> str | None:
    """Return the first alias found in df.columns, or None."""
    for alias in aliases:
        if alias in df.columns:
            return alias
    return None


def resolve_all_columns(df: pd.DataFrame) -> dict[str, str] | None:
    """
    Map logical column names → actual column names in df.
    Returns None and shows an error if any required column is missing.
    """
    mapping = {}
    missing = []
    for logical, aliases in REQUIRED_COLUMNS.items():
        col = resolve_column(df, aliases)
        if col:
            mapping[logical] = col
        else:
            missing.append(f"**{logical}** (tried: {', '.join(aliases)})")

    if missing:
        st.error(
            "⚠️ **Missing required columns.** The uploaded file is missing:\n\n"
            + "\n".join(f"- {m}" for m in missing)
            + "\n\nPlease check your file or contact your system administrator."
        )
        return None
    return mapping


def load_excel(file) -> pd.DataFrame | None:
    """Safe Excel loader with detailed error messages."""
    try:
        df = pd.read_excel(file, engine="openpyxl")
        if df.empty:
            st.error("❌ The uploaded file is empty. Please upload a file that contains data.")
            return None
        return df
    except Exception as exc:
        err_type = type(exc).__name__
        if "openpyxl" in str(exc).lower() or "zipfile" in str(exc).lower():
            st.error(
                "❌ **Invalid Excel file.** The file could not be read. "
                "Make sure you are uploading a valid `.xlsx` file (not `.xls`, `.csv`, or a renamed file)."
            )
        else:
            st.error(f"❌ **Unexpected error while reading file:** `{err_type}: {exc}`")
        return None


def fmt_duration(seconds: float) -> str:
    """Format seconds → HH:MM:SS string."""
    try:
        s = int(seconds)
        return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"
    except Exception:
        return "—"


def kpi_card(label: str, value: str, sub: str = "", color: str = "") -> str:
    cls = f"kpi-card {color}".strip()
    return f"""
    <div class="{cls}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {'<div class="kpi-sub">' + sub + '</div>' if sub else ''}
    </div>"""


# ══════════════════════════════════════════════════════════════════════════════
# BRANDING HEADER
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="brand-header">
    <div class="brand-logo">📞</div>
    <div class="brand-text">
        <h1>CDR Analytics Dashboard</h1>
        <p>Call Detail Records — Reporting &amp; Intelligence Platform &nbsp;|&nbsp; Internal Use Only</p>
    </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# INSTRUCTIONS FOR NON-TECHNICAL USERS
# ══════════════════════════════════════════════════════════════════════════════

with st.expander("📋  How to use this dashboard  (click to expand)", expanded=False):
    st.markdown("""
    <div class="info-box">
    <strong>Step-by-step guide:</strong><br><br>
    1. &nbsp;📁 &nbsp;<strong>Prepare your file:</strong> Export your CDR data as an Excel file (<code>.xlsx</code>)
       from your telecom system. Make sure it includes columns for caller, callee, duration, date/time, and call type.<br><br>
    2. &nbsp;⬆️ &nbsp;<strong>Upload:</strong> Click <em>"Browse files"</em> in the sidebar on the left and select your Excel file.<br><br>
    3. &nbsp;🔍 &nbsp;<strong>Filter (optional):</strong> Use the sidebar controls to filter by date range or call type.<br><br>
    4. &nbsp;📊 &nbsp;<strong>Explore:</strong> The dashboard will automatically calculate KPIs and generate charts.<br><br>
    5. &nbsp;💾 &nbsp;<strong>Export:</strong> Use the <em>Download filtered data</em> button in the sidebar to save your results.<br><br>
    <strong>Need help?</strong> Contact your IT administrator or the analytics team.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — upload + filters
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## ⚙️ Controls")
    st.markdown("---")

    uploaded_file = st.file_uploader(
        "📁 Upload CDR Excel File",
        type=["xlsx"],
        help="Upload a valid .xlsx CDR export file.",
    )

    st.markdown("---")
    st.markdown("### 🔽 Filters")
    st.caption("Filters are enabled after a file is loaded.")

    date_filter   = st.empty()
    type_filter   = st.empty()

    st.markdown("---")
    download_slot = st.empty()

    st.markdown("---")
    st.markdown(
        "<p style='color:#546E7A;font-size:0.75rem;'>CDR Analytics v2.0<br>© 2024 Your Company</p>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════

if uploaded_file is None:
    # ── Idle / welcome state ──────────────────────────────────────────────
    st.markdown('<div class="section-title">📂 Getting Started</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(kpi_card("Total Calls", "—", "Upload a file to begin"), unsafe_allow_html=True)
    with col2:
        st.markdown(kpi_card("Total Duration", "—", "Upload a file to begin", "green"), unsafe_allow_html=True)
    with col3:
        st.markdown(kpi_card("Unique Numbers", "—", "Upload a file to begin", "amber"), unsafe_allow_html=True)

    st.info("👈  Use the sidebar to upload your CDR Excel file.")
    st.stop()


# ── File was uploaded — process it ───────────────────────────────────────────
try:
    with st.spinner("🔄  Reading and validating your file…"):
        df_raw = load_excel(uploaded_file)

    if df_raw is None:
        st.stop()  # load_excel already showed the error

    with st.spinner("🔍  Detecting columns and preparing data…"):
        col_map = resolve_all_columns(df_raw)

    if col_map is None:
        st.stop()  # resolve_all_columns already showed the error

    # ── Rename to logical names for uniform downstream processing ──
    df = df_raw.rename(columns={v: k for k, v in col_map.items()})

    # ── Parse datetime safely ─────────────────────────────────────
    with st.spinner("📅  Parsing dates…"):
        try:
            df["datetime"] = pd.to_datetime(df["datetime"], infer_datetime_format=True, errors="coerce")
            bad_dates = df["datetime"].isna().sum()
            if bad_dates > 0:
                st.warning(f"⚠️  {bad_dates} row(s) had unparseable dates and will be excluded from time-based charts.")
        except Exception as e:
            st.warning(f"⚠️  Could not parse date column: {e}. Time-based charts may be unavailable.")

    # ── Parse duration safely ──────────────────────────────────────
    df["duration"] = pd.to_numeric(df["duration"], errors="coerce").fillna(0)

    # ── Sidebar FILTERS (now that we have real data) ───────────────
    with date_filter:
        valid_dates = df["datetime"].dropna()
        if not valid_dates.empty:
            min_d = valid_dates.min().date()
            max_d = valid_dates.max().date()
            selected_dates = st.date_input(
                "📅 Date Range",
                value=(min_d, max_d),
                min_value=min_d,
                max_value=max_d,
            )
        else:
            selected_dates = None

    with type_filter:
        call_types = sorted(df["call_type"].dropna().unique().tolist())
        selected_types = st.multiselect(
            "📞 Call Type",
            options=call_types,
            default=call_types,
        )

    # ── Apply filters ──────────────────────────────────────────────
    df_filtered = df.copy()

    if selected_dates and len(selected_dates) == 2:
        start_dt = pd.Timestamp(selected_dates[0])
        end_dt   = pd.Timestamp(selected_dates[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df_filtered = df_filtered[
            (df_filtered["datetime"] >= start_dt) & (df_filtered["datetime"] <= end_dt)
        ]

    if selected_types:
        df_filtered = df_filtered[df_filtered["call_type"].isin(selected_types)]

    if df_filtered.empty:
        st.warning("⚠️  No records match the selected filters. Please adjust the date range or call types.")
        st.stop()

    # ── Download button ────────────────────────────────────────────
    with download_slot:
        csv_bytes = df_filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="💾 Download Filtered Data",
            data=csv_bytes,
            file_name=f"CDR_filtered_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
        )

    # ══════════════════════════════════════════════════════════════════════
    # SUCCESS BANNER
    # ══════════════════════════════════════════════════════════════════════
    st.success(
        f"✅  File loaded successfully — **{len(df_filtered):,}** records "
        f"({len(df_raw):,} total, {len(df_raw)-len(df_filtered):,} filtered out)"
    )

    # ══════════════════════════════════════════════════════════════════════
    # KPI SECTION
    # ══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-title">📊 Key Performance Indicators</div>', unsafe_allow_html=True)

    total_calls    = len(df_filtered)
    total_sec      = df_filtered["duration"].sum()
    avg_sec        = df_filtered["duration"].mean()
    unique_callers = df_filtered["caller"].nunique()
    unique_callees = df_filtered["callee"].nunique()
    longest_call   = df_filtered["duration"].max()

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.markdown(kpi_card("Total Calls", f"{total_calls:,}", "All selected records"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("Total Duration", fmt_duration(total_sec), "HH:MM:SS", "green"), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card("Avg Duration", fmt_duration(avg_sec), "per call", "amber"), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card("Unique Callers", f"{unique_callers:,}", "distinct numbers", "purple"), unsafe_allow_html=True)
    with c5:
        st.markdown(kpi_card("Unique Callees", f"{unique_callees:,}", "distinct numbers"), unsafe_allow_html=True)
    with c6:
        st.markdown(kpi_card("Longest Call", fmt_duration(longest_call), "single call", "red"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # CHARTS — ROW 1
    # ══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-title">📈 Call Volume Analysis</div>', unsafe_allow_html=True)

    chart_col1, chart_col2 = st.columns([3, 2])

    # ── Calls over time ────────────────────────────────────────────
    with chart_col1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        df_time = df_filtered.dropna(subset=["datetime"]).copy()
        if not df_time.empty:
            df_time["date"] = df_time["datetime"].dt.date
            daily = df_time.groupby("date").size().reset_index(name="calls")
            fig = px.area(
                daily, x="date", y="calls",
                title="📅 Daily Call Volume",
                color_discrete_sequence=["#1565C0"],
            )
            fig.update_layout(
                plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
                font_family="IBM Plex Sans",
                title_font_size=14, title_font_color="#0F2B5B",
                xaxis_title="", yaxis_title="Calls",
                margin=dict(l=10, r=10, t=40, b=10),
                hovermode="x unified",
            )
            fig.update_traces(fill="tozeroy", line_color="#1565C0", fillcolor="rgba(21,101,192,0.15)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📅 Date data unavailable for this chart.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Call type breakdown ────────────────────────────────────────
    with chart_col2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        type_counts = df_filtered["call_type"].value_counts().reset_index()
        type_counts.columns = ["call_type", "count"]
        fig2 = px.pie(
            type_counts, names="call_type", values="count",
            title="📞 Call Type Distribution",
            color_discrete_sequence=CHART_COLORS,
            hole=0.45,
        )
        fig2.update_layout(
            plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
            font_family="IBM Plex Sans",
            title_font_size=14, title_font_color="#0F2B5B",
            margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        )
        fig2.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # CHARTS — ROW 2
    # ══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-title">👥 Top Callers &amp; Callees</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        top_callers = (
            df_filtered.groupby("caller")
            .agg(total_calls=("caller", "count"), total_dur=("duration", "sum"))
            .nlargest(10, "total_calls")
            .reset_index()
        )
        fig3 = px.bar(
            top_callers, x="total_calls", y="caller",
            orientation="h",
            title="📤 Top 10 Callers by Volume",
            color="total_dur",
            color_continuous_scale=["#BBDEFB", "#1565C0"],
            labels={"total_calls": "Calls", "caller": "", "total_dur": "Total Sec"},
        )
        fig3.update_layout(
            plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
            font_family="IBM Plex Sans",
            title_font_size=14, title_font_color="#0F2B5B",
            yaxis=dict(autorange="reversed"),
            margin=dict(l=10, r=10, t=40, b=10),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        top_callees = (
            df_filtered.groupby("callee")
            .agg(total_calls=("callee", "count"), total_dur=("duration", "sum"))
            .nlargest(10, "total_calls")
            .reset_index()
        )
        fig4 = px.bar(
            top_callees, x="total_calls", y="callee",
            orientation="h",
            title="📥 Top 10 Callees by Volume",
            color="total_dur",
            color_continuous_scale=["#C8E6C9", "#2E7D32"],
            labels={"total_calls": "Calls", "callee": "", "total_dur": "Total Sec"},
        )
        fig4.update_layout(
            plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
            font_family="IBM Plex Sans",
            title_font_size=14, title_font_color="#0F2B5B",
            yaxis=dict(autorange="reversed"),
            margin=dict(l=10, r=10, t=40, b=10),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig4, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # CHARTS — ROW 3 (Hourly heatmap)
    # ══════════════════════════════════════════════════════════════════════
    df_time2 = df_filtered.dropna(subset=["datetime"]).copy()
    if not df_time2.empty:
        st.markdown('<div class="section-title">🕐 Hourly &amp; Weekly Patterns</div>', unsafe_allow_html=True)
        df_time2["hour"]    = df_time2["datetime"].dt.hour
        df_time2["weekday"] = df_time2["datetime"].dt.day_name()

        weekday_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        heat = (
            df_time2.groupby(["weekday","hour"])
            .size().reset_index(name="calls")
        )
        heat["weekday"] = pd.Categorical(heat["weekday"], categories=weekday_order, ordered=True)
        heat = heat.sort_values(["weekday","hour"])

        fig5 = px.density_heatmap(
            heat, x="hour", y="weekday", z="calls",
            title="🌡️ Call Heatmap — Hour of Day × Day of Week",
            color_continuous_scale="Blues",
            labels={"hour": "Hour of Day", "weekday": "", "calls": "Calls"},
        )
        fig5.update_layout(
            plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
            font_family="IBM Plex Sans",
            title_font_size=14, title_font_color="#0F2B5B",
            margin=dict(l=10, r=10, t=40, b=10),
            xaxis=dict(tickmode="linear", tick0=0, dtick=1),
        )
        st.plotly_chart(fig5, use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════
    # RAW DATA PREVIEW
    # ══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-title">🗃️ Data Preview</div>', unsafe_allow_html=True)
    with st.expander(f"Show raw records ({len(df_filtered):,} rows)", expanded=False):
        st.dataframe(
            df_filtered.head(500),
            use_container_width=True,
            height=320,
        )
        if len(df_filtered) > 500:
            st.caption("⚠️  Preview limited to first 500 rows. Use the Download button for the full dataset.")

except Exception as unexpected:
    # ── Last-resort catch — app will never crash to a blank screen ──────
    st.error(
        "❌ **An unexpected error occurred while processing your file.**\n\n"
        "Please try uploading the file again or contact your IT administrator "
        "with the error details below."
    )
    with st.expander("🔧 Technical details (for IT support)"):
        st.code(traceback.format_exc(), language="python")
