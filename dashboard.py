import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time

# ─────────────────────────────────────────────
#  GLOBAL CONFIG
# ─────────────────────────────────────────────
SHEET_ID = "1daMj8z3OC_c-knuEs_5zHs3LiUAgyUXOJndDYzPt_OY"

st.set_page_config(page_title="GP Onboarding", page_icon="📊", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

/* ── Base ── */
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #06080f; color: #e8eaf0; }
section[data-testid="stSidebar"] {
    background: #0b0e1a !important;
    border-right: 1px solid #1c2236;
}

/* ── Sidebar text ── */
[data-testid="stSidebar"] * { color: #c9cfe0 !important; }

/* ── Headings ── */
h1 { font-size: 1.9rem !important; font-weight: 700 !important;
     color: #e8eaf0 !important; letter-spacing: -0.5px; }
h2 { font-size: 1.25rem !important; font-weight: 600 !important;
     color: #c4cade !important; }
h3 { font-size: 1rem !important; font-weight: 500 !important;
     color: #9aa5be !important; }
p, span, label, div { color: #c9cfe0 !important; }

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: #0e1220;
    border: 1px solid #1e2640;
    border-radius: 12px;
    padding: 18px 20px !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Space Mono', monospace !important;
    font-size: 2rem !important;
    color: #5ee7d0 !important;
    font-weight: 700 !important;
}
[data-testid="stMetricLabel"] { color: #6b7897 !important; font-size: 0.78rem !important; text-transform: uppercase; letter-spacing: 0.08em; }
[data-testid="stMetricDelta"] { font-size: 0.85rem !important; }

/* ── Section divider ── */
hr { border: none; border-top: 1px solid #1a2035; margin: 1.5rem 0; }

/* ── Download button ── */
.stDownloadButton > button {
    background: #111827;
    border: 1px solid #2a3550;
    color: #9eb3d4 !important;
    border-radius: 8px;
    font-size: 0.82rem;
}
.stDownloadButton > button:hover {
    border-color: #5ee7d0;
    color: #5ee7d0 !important;
}

/* ── Refresh button ── */
.stButton > button {
    background: linear-gradient(135deg, #1a2a4a, #0f1d35);
    border: 1px solid #2e4470;
    color: #7eb8e8 !important;
    border-radius: 8px;
    font-size: 0.82rem;
    padding: 6px 16px;
}
.stButton > button:hover {
    border-color: #5ee7d0;
    color: #5ee7d0 !important;
    background: linear-gradient(135deg, #1d3050, #132540);
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid #1a2540;
    border-radius: 10px;
    overflow: hidden;
}

/* ── Section label ── */
.section-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #4a5578 !important;
    margin-bottom: 4px;
}
.section-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #c4cade !important;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid #1a2540;
}

/* ── Auto-refresh badge ── */
.refresh-badge {
    display: inline-block;
    background: #0e1a2e;
    border: 1px solid #1e3050;
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 0.75rem;
    color: #5ab4d4 !important;
    font-family: 'Space Mono', monospace;
}

/* ── Selectbox / multiselect ── */
[data-baseweb="select"] { background: #0e1220 !important; border-color: #1e2640 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  CHART THEME HELPER
# ─────────────────────────────────────────────
CHART_BG   = "#07090f"
GRID_COLOR = "rgba(255,255,255,0.04)"
FONT_COLOR = "#9aa5be"
ACCENT1    = "#5ee7d0"
ACCENT2    = "#7b8ff5"
ACCENT3    = "#f7be68"

def dark_layout(**kwargs):
    base = dict(
        template="plotly_dark",
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        font=dict(family="DM Sans", color=FONT_COLOR, size=12),
        margin=dict(t=50, b=40, l=40, r=20),
    )
    base.update(kwargs)
    return base

# ─────────────────────────────────────────────
#  LOAD DATA
# ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data():
    MAIN_GID = "0"
    QC_GID   = "1797653496"
    main_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={MAIN_GID}"
    qc_url   = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={QC_GID}"

    df_main = pd.read_csv(main_url)
    try:
        df_qc = pd.read_csv(qc_url)
    except Exception as e:
        df_qc = pd.DataFrame()
        st.error(f"QC sheet not loading: {e}")

    df_main.columns = df_main.columns.str.strip()
    if not df_qc.empty:
        df_qc.columns = df_qc.columns.str.strip()

    if "Timestamp" in df_main.columns:
        df_main["Timestamp"] = pd.to_datetime(df_main["Timestamp"], errors="coerce")
        df_main["Date"]      = df_main["Timestamp"].dt.date

    if "QC Status" in df_qc.columns:
        df_qc["QC Status"] = df_qc["QC Status"].astype(str).str.lower().str.strip()

    return df_main, df_qc

df_main, df_qc = load_data()

# ─────────────────────────────────────────────
#  AUTO-REFRESH LOGIC
# ─────────────────────────────────────────────
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

AUTO_REFRESH_SEC = 300   # 5 minutes

elapsed = time.time() - st.session_state.last_refresh
if elapsed >= AUTO_REFRESH_SEC:
    st.cache_data.clear()
    st.session_state.last_refresh = time.time()
    st.rerun()

remaining = int(AUTO_REFRESH_SEC - elapsed)

# ─────────────────────────────────────────────
#  SIDEBAR NAV
# ─────────────────────────────────────────────
st.sidebar.markdown("## GP Onboarding")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigate", ["Dashboard", "CPOC Performance", "Raw Data"], label_visibility="collapsed")

# Auto-refresh controls in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown(f'<span class="refresh-badge">Auto-refresh in {remaining}s</span>', unsafe_allow_html=True)
if st.sidebar.button("Refresh Now"):
    st.cache_data.clear()
    st.session_state.last_refresh = time.time()
    st.rerun()
st.sidebar.caption(f"Last refreshed: {pd.Timestamp.now().strftime('%H:%M:%S')}")


# ═══════════════════════════════════════════════
#  DASHBOARD PAGE
# ═══════════════════════════════════════════════
if page == "Dashboard":
    df = df_main.copy()

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Filters**")

    district = st.sidebar.selectbox("District", ["All"] + sorted(df["District"].dropna().unique()))
    if district != "All":
        df = df[df["District"] == district]

    acs = sorted(df["Assembly Constituency"].dropna().unique())
    selected_ac = st.sidebar.multiselect("Assembly Constituency", acs, default=acs[:1])
    if not selected_ac:
        st.warning("Select at least 1 Assembly Constituency.")
        st.stop()
    df = df[df["Assembly Constituency"].isin(selected_ac)]

    df_qc_filtered = df_qc.copy()
    if not df_qc_filtered.empty:
        if "District" in df_qc_filtered.columns and district != "All":
            df_qc_filtered = df_qc_filtered[df_qc_filtered["District"] == district]
        if "Assembly Constituency" in df_qc_filtered.columns:
            df_qc_filtered = df_qc_filtered[df_qc_filtered["Assembly Constituency"].isin(selected_ac)]

    # ── KPIs ──────────────────────────────────
    total  = len(df)
    male   = len(df[df["Gender"] == "Male"])   if "Gender" in df.columns else 0
    female = len(df[df["Gender"] == "Female"]) if "Gender" in df.columns else 0

    if "QC Status" in df_qc_filtered.columns:
        valid   = (df_qc_filtered["QC Status"] == "valid").sum()
        invalid = (df_qc_filtered["QC Status"] == "invalid").sum()
    else:
        valid = invalid = 0

    validation_rate = (valid / (valid + invalid) * 100) if (valid + invalid) else 0

    st.title("GP Onboarding Dashboard")
    st.markdown('<p class="section-label">Overview — Key Performance Indicators</p>', unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Onboarded", f"{total:,}")
    c2.metric("Male", f"{male:,}")
    c3.metric("Female", f"{female:,}")
    c4.metric("Validated", f"{valid:,}")
    c5.metric("Validation Rate", f"{validation_rate:.1f}%")

    st.markdown("---")

    # ── QC Summary + Gauge ─────────────────────
    col_a, col_b = st.columns([1.2, 1])
    with col_a:
        st.markdown('<p class="section-title">QC Verification Summary</p>', unsafe_allow_html=True)
        qc_df = pd.DataFrame({
            "Status": ["Valid", "Invalid", "Pending"],
            "Count":  [valid, invalid, max(0, total - valid - invalid)]
        })
        st.dataframe(
            qc_df.style
                .background_gradient(subset=["Count"], cmap="Blues")
                .format({"Count": "{:,}"}),
            use_container_width=True, hide_index=True
        )

    with col_b:
        st.markdown('<p class="section-title">Validation Gauge</p>', unsafe_allow_html=True)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=validation_rate,
            delta={"reference": 80, "suffix": "%"},
            number={"suffix": "%", "font": {"size": 32, "color": ACCENT1}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": FONT_COLOR},
                "bar": {"color": ACCENT1, "thickness": 0.3},
                "bgcolor": "#0e1220",
                "bordercolor": "#1e2640",
                "steps": [
                    {"range": [0, 50],  "color": "#1a0e14"},
                    {"range": [50, 80], "color": "#0e1a20"},
                    {"range": [80, 100],"color": "#0e201a"},
                ],
                "threshold": {"line": {"color": ACCENT3, "width": 3}, "value": 80},
            }
        ))
        fig_gauge.update_layout(**dark_layout(height=220, margin=dict(t=20, b=10, l=30, r=30)))
        st.plotly_chart(fig_gauge, use_container_width=True)

    st.markdown("---")

    # ── Daily Trend ────────────────────────────
    if "Date" in df.columns:
        st.markdown('<p class="section-title">Daily Onboarding Trend</p>', unsafe_allow_html=True)
        trend = df.groupby("Date").size().reset_index(name="Count")

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=trend["Date"], y=trend["Count"],
            name="Daily Count",
            marker=dict(
                color=trend["Count"],
                colorscale=[[0, "#1a3a4a"], [1, ACCENT1]],
                line=dict(width=0),
            ),
            text=trend["Count"], textposition="outside",
            textfont=dict(color=ACCENT1, size=11),
        ))
        fig_trend.add_trace(go.Scatter(
            x=trend["Date"], y=trend["Count"],
            mode="lines", name="Trend",
            line=dict(color=ACCENT3, width=2, dash="dot"),
            opacity=0.7,
        ))
        fig_trend.update_layout(
            **dark_layout(height=340, showlegend=True),
            xaxis=dict(showgrid=False, title=""),
            yaxis=dict(gridcolor=GRID_COLOR, title="GPs Onboarded"),
            bargap=0.3,
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        st.markdown("---")

    # ── GPN Category ──────────────────────────
    if "GPN Category" in df_qc_filtered.columns:
        st.markdown('<p class="section-title">GPN Category Distribution</p>', unsafe_allow_html=True)
        gpn_cat = df_qc_filtered["GPN Category"].value_counts().reset_index()
        gpn_cat.columns = ["Category", "Count"]

        col1, col2 = st.columns(2)
        with col1:
            fig_gpn_bar = go.Figure(go.Bar(
                x=gpn_cat["Category"], y=gpn_cat["Count"],
                text=gpn_cat["Count"], textposition="outside",
                textfont=dict(color=ACCENT2, size=12, family="Space Mono"),
                marker=dict(
                    color=gpn_cat["Count"],
                    colorscale=[[0, "#1a1f3a"], [1, ACCENT2]],
                    line=dict(width=0),
                ),
            ))
            fig_gpn_bar.update_layout(
                **dark_layout(height=320),
                title="Count by Category",
                xaxis=dict(showgrid=False),
                yaxis=dict(gridcolor=GRID_COLOR),
                bargap=0.35,
            )
            st.plotly_chart(fig_gpn_bar, use_container_width=True)

        with col2:
            fig_gpn_pie = px.pie(
                gpn_cat, names="Category", values="Count",
                hole=0.55,
                color_discrete_sequence=[ACCENT1, ACCENT2, ACCENT3, "#e27adf", "#f77b72"],
            )
            fig_gpn_pie.update_traces(
                textinfo="percent+label",
                textfont_size=11,
            )
            fig_gpn_pie.update_layout(
                **dark_layout(height=320),
                title="Share by Category",
                showlegend=False,
            )
            st.plotly_chart(fig_gpn_pie, use_container_width=True)

        st.markdown("---")

    # ── GPN Call Verification ─────────────────
    if "GPN Call Verification Status" in df_qc_filtered.columns:
        st.markdown('<p class="section-title">GPN Call Verification Status</p>', unsafe_allow_html=True)
        gpn_ver = (
            df_qc_filtered["GPN Call Verification Status"]
            .astype(str).str.strip().str.title()
            .value_counts().reset_index()
        )
        gpn_ver.columns = ["Status", "Count"]

        col1, col2 = st.columns([1.3, 1])
        with col1:
            fig_ver_bar = go.Figure(go.Bar(
                x=gpn_ver["Status"], y=gpn_ver["Count"],
                text=gpn_ver["Count"], textposition="outside",
                textfont=dict(color=ACCENT1, size=12),
                marker=dict(
                    color=[ACCENT1, "#f77b72", ACCENT3, ACCENT2][:len(gpn_ver)],
                    line=dict(width=0),
                ),
            ))
            fig_ver_bar.update_layout(
                **dark_layout(height=300),
                xaxis=dict(showgrid=False),
                yaxis=dict(gridcolor=GRID_COLOR),
                bargap=0.4,
            )
            st.plotly_chart(fig_ver_bar, use_container_width=True)

        with col2:
            fig_ver_pie = px.pie(
                gpn_ver, names="Status", values="Count", hole=0.55,
                color_discrete_sequence=[ACCENT1, "#f77b72", ACCENT3, ACCENT2],
            )
            fig_ver_pie.update_traces(textinfo="percent+label", textfont_size=11)
            fig_ver_pie.update_layout(**dark_layout(height=300), showlegend=False)
            st.plotly_chart(fig_ver_pie, use_container_width=True)

        st.markdown("---")

    # ── FA Meeting Status ─────────────────────
    if "FA Meeting Status" in df_qc_filtered.columns:
        st.markdown('<p class="section-title">FA Meeting Status</p>', unsafe_allow_html=True)
        fa = df_qc_filtered["FA Meeting Status"].value_counts().reset_index()
        fa.columns = ["Status", "Count"]

        col1, col2 = st.columns([1.3, 1])
        with col1:
            fig_fa_bar = go.Figure(go.Bar(
                x=fa["Status"], y=fa["Count"],
                text=fa["Count"], textposition="outside",
                textfont=dict(color=ACCENT3, size=12),
                marker=dict(
                    color=fa["Count"],
                    colorscale=[[0, "#2a1f0e"], [1, ACCENT3]],
                    line=dict(width=0),
                ),
            ))
            fig_fa_bar.update_layout(
                **dark_layout(height=300),
                xaxis=dict(showgrid=False),
                yaxis=dict(gridcolor=GRID_COLOR),
                bargap=0.4,
            )
            st.plotly_chart(fig_fa_bar, use_container_width=True)

        with col2:
            fig_fa_pie = px.pie(
                fa, names="Status", values="Count", hole=0.55,
                color_discrete_sequence=[ACCENT3, ACCENT1, ACCENT2, "#e27adf"],
            )
            fig_fa_pie.update_traces(textinfo="percent+label", textfont_size=11)
            fig_fa_pie.update_layout(**dark_layout(height=300), showlegend=False)
            st.plotly_chart(fig_fa_pie, use_container_width=True)

        st.markdown("---")

    # ── Occupation Summary (% bar) ─────────────
    occ_col = "Occupation" if "Occupation" in df.columns else ("AU" if "AU" in df.columns else None)
    if occ_col:
        st.markdown('<p class="section-title">Occupation Breakdown</p>', unsafe_allow_html=True)
        df[occ_col] = df[occ_col].astype(str).str.strip()
        occ = df[occ_col].value_counts().reset_index()
        occ.columns = ["Occupation", "Count"]
        occ["Percentage"] = (occ["Count"] / occ["Count"].sum() * 100).round(1)
        occ_sorted = occ.sort_values("Percentage")

        col1, col2 = st.columns([1, 1.6])
        with col1:
            st.dataframe(
                occ[["Occupation", "Count", "Percentage"]]
                    .style
                    .format({"Percentage": "{:.1f}%", "Count": "{:,}"})
                    .background_gradient(subset=["Percentage"], cmap="YlGnBu"),
                use_container_width=True, hide_index=True
            )
            st.download_button(
                "Download Occupation Data",
                occ.to_csv(index=False), "occupation_summary.csv"
            )

        with col2:
            fig_occ = go.Figure(go.Bar(
                y=occ_sorted["Occupation"],
                x=occ_sorted["Percentage"],
                orientation="h",
                text=[f"{v:.1f}%" for v in occ_sorted["Percentage"]],
                textposition="outside",
                textfont=dict(color=ACCENT1, size=11, family="Space Mono"),
                marker=dict(
                    color=occ_sorted["Percentage"],
                    colorscale=[[0, "#0e2a22"], [0.5, "#1a5040"], [1, ACCENT1]],
                    line=dict(width=0),
                ),
            ))
            fig_occ.update_layout(
                **dark_layout(height=max(280, len(occ_sorted) * 36)),
                xaxis=dict(
                    title="Share (%)",
                    gridcolor=GRID_COLOR,
                    ticksuffix="%",
                ),
                yaxis=dict(showgrid=False, title=""),
                bargap=0.3,
            )
            st.plotly_chart(fig_occ, use_container_width=True)

    st.markdown("---")
    st.download_button("Download Filtered Data", df.to_csv(index=False), "filtered_data.csv")


# ═══════════════════════════════════════════════
#  CPOC PERFORMANCE PAGE
# ═══════════════════════════════════════════════
elif page == "CPOC Performance":
    st.title("CPOC Performance")

    @st.cache_data(ttl=60)
    def fetch_live_data(url):
        df = pd.read_csv(url, skiprows=2, header=None)
        df = df.iloc[:, :8]
        df.columns = [
            "CPOC", "Total GP", "Total QCd", "Valid", "Invalid",
            "Today Total QCd", "Today Valid", "Today Invalid"
        ]
        df["CPOC"] = df["CPOC"].astype(str).str.strip()
        df = df[~df["CPOC"].str.lower().isin(["nan", "none", ""])]
        df["Total GP"] = pd.to_numeric(df["Total GP"], errors="coerce").fillna(0)
        df = df[df["Total GP"] > 0]
        for col in df.columns[1:]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
        return df

    QC_SUMMARY_GID = "1456730729"
    qc_summary_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={QC_SUMMARY_GID}"

    col_r1, col_r2 = st.columns([1, 5])
    with col_r1:
        if st.button("Refresh Data"):
            st.cache_data.clear()
            st.session_state.last_refresh = time.time()
            st.rerun()
    with col_r2:
        elapsed_cpoc = int(time.time() - st.session_state.last_refresh)
        st.markdown(
            f'<span class="refresh-badge">Last refreshed {elapsed_cpoc}s ago &nbsp;·&nbsp; auto-refresh in {max(0, AUTO_REFRESH_SEC - elapsed_cpoc)}s</span>',
            unsafe_allow_html=True
        )

    try:
        df_cpoc_summary = fetch_live_data(qc_summary_url)
    except Exception as e:
        st.error(f"Connection Error: {e}")
        df_cpoc_summary = pd.DataFrame()

    required_cols = {"CPOC", "Valid", "Invalid", "Total QCd", "Total GP",
                     "Today Total QCd", "Today Valid", "Today Invalid"}
    if not df_cpoc_summary.empty and not required_cols.issubset(df_cpoc_summary.columns):
        st.error(f"Sheet schema mismatch. Expected: {required_cols}")
        df_cpoc_summary = pd.DataFrame()

    if not df_cpoc_summary.empty:
        total_mask = df_cpoc_summary["CPOC"].str.contains("Total", case=False)
        total_data = df_cpoc_summary[total_mask]

        # ── KPIs ──
        if not total_data.empty:
            row  = total_data.iloc[0]
            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Total GP",    f"{row['Total GP']:,}")
            k2.metric("Total QC'd",  f"{row['Total QCd']:,}")
            k3.metric("Valid",       f"{row['Valid']:,}")
            k4.metric("Invalid",     f"{row['Invalid']:,}")
            v_rate = (row["Valid"] / row["Total QCd"] * 100) if row["Total QCd"] > 0 else 0
            k5.metric("Validation %", f"{v_rate:.1f}%")

        st.markdown("---")

        # ── Styled Table ──
        st.markdown('<p class="section-title">CPOC Detail Table</p>', unsafe_allow_html=True)

        header_values = [
            ["<b>CPOC</b>", "<b>CPOC</b>"],
            ["<b>Basic</b>", "<b>Total GP</b>"],
            ["<b>Verification</b>", "<b>Total QC'd</b>"],
            ["<b>Verification</b>", "<b>Valid</b>"],
            ["<b>Verification</b>", "<b>Invalid</b>"],
            ["<b>Today</b>", "<b>QC'd</b>"],
            ["<b>Today</b>", "<b>Valid</b>"],
            ["<b>Today</b>", "<b>Invalid</b>"],
        ]
        cell_values = [df_cpoc_summary[col].tolist() for col in df_cpoc_summary.columns]

        fig_table = go.Figure(data=[go.Table(
            columnwidth=[160, 80, 90, 80, 80, 80, 80, 80],
            header=dict(
                values=header_values,
                fill_color=[["#0d1628", "#0a1f3a"]] * 8,
                font=dict(color="white", size=11, family="DM Sans"),
                align="center",
                line_color="#1e2a40",
                height=28,
            ),
            cells=dict(
                values=cell_values,
                fill_color=[
                    ["#0e1220"] * len(df_cpoc_summary),
                    ["#0e1220"] * len(df_cpoc_summary),
                    ["#101825"] * len(df_cpoc_summary),
                    ["#0d2018"] * len(df_cpoc_summary),  # Valid — green tint
                    ["#201018"] * len(df_cpoc_summary),  # Invalid — red tint
                    ["#101825"] * len(df_cpoc_summary),
                    ["#0d2018"] * len(df_cpoc_summary),
                    ["#201018"] * len(df_cpoc_summary),
                ],
                font=dict(
                    color=["#c9cfe0", "#c9cfe0", "#c9cfe0",
                           "#5ee7d0", "#f77b72",
                           "#c9cfe0", "#5ee7d0", "#f77b72"],
                    size=12, family="Space Mono",
                ),
                align="center",
                line_color="#1a2236",
                height=28,
            ),
        )])
        fig_table.update_layout(margin=dict(l=0, r=0, b=10, t=10), height=600,
                                paper_bgcolor=CHART_BG)
        st.plotly_chart(fig_table, use_container_width=True)

        # ── Bar Chart ──
        st.markdown("---")
        df_charts = df_cpoc_summary[~total_mask].copy()
        st.markdown('<p class="section-title">Individual CPOC Performance</p>', unsafe_allow_html=True)

        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            name="Valid", x=df_charts["CPOC"], y=df_charts["Valid"],
            text=df_charts["Valid"], textposition="outside",
            textfont=dict(color=ACCENT1, size=12, family="Space Mono"),
            marker=dict(color=ACCENT1, opacity=0.85, line=dict(width=0)),
            hovertemplate="<b>%{x}</b><br>Valid: <b>%{y}</b><extra></extra>",
        ))
        fig_bar.add_trace(go.Bar(
            name="Invalid", x=df_charts["CPOC"], y=df_charts["Invalid"],
            text=df_charts["Invalid"], textposition="outside",
            textfont=dict(color="#f77b72", size=12, family="Space Mono"),
            marker=dict(color="#f77b72", opacity=0.85, line=dict(width=0)),
            hovertemplate="<b>%{x}</b><br>Invalid: <b>%{y}</b><extra></extra>",
        ))
        avg_valid = int(df_charts["Valid"].mean()) if len(df_charts) else 0
        fig_bar.add_hline(
            y=avg_valid, line_dash="dot",
            line_color="rgba(94,231,208,0.35)",
            annotation_text=f"Avg Valid: {avg_valid}",
            annotation_position="top right",
            annotation_font=dict(color=ACCENT1, size=11),
        )
        fig_bar.update_layout(
            **dark_layout(height=420),
            barmode="group", bargap=0.28, bargroupgap=0.06,
            xaxis=dict(showgrid=False, title="CPOC", tickfont=dict(size=11)),
            yaxis=dict(gridcolor=GRID_COLOR, title="Count"),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1,
                font=dict(size=12, color=FONT_COLOR),
                bgcolor="rgba(0,0,0,0)",
            ),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # ── Today's performance ──
        st.markdown("---")
        st.markdown('<p class="section-title">Today\'s Activity</p>', unsafe_allow_html=True)
        fig_today = go.Figure()
        fig_today.add_trace(go.Bar(
            name="Today Valid", x=df_charts["CPOC"], y=df_charts["Today Valid"],
            text=df_charts["Today Valid"], textposition="outside",
            textfont=dict(color=ACCENT2, size=11),
            marker=dict(color=ACCENT2, opacity=0.85, line=dict(width=0)),
        ))
        fig_today.add_trace(go.Bar(
            name="Today Invalid", x=df_charts["CPOC"], y=df_charts["Today Invalid"],
            text=df_charts["Today Invalid"], textposition="outside",
            textfont=dict(color=ACCENT3, size=11),
            marker=dict(color=ACCENT3, opacity=0.85, line=dict(width=0)),
        ))
        fig_today.update_layout(
            **dark_layout(height=360),
            barmode="group", bargap=0.3, bargroupgap=0.06,
            xaxis=dict(showgrid=False, title="CPOC"),
            yaxis=dict(gridcolor=GRID_COLOR, title="Count"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                        font=dict(size=12), bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig_today, use_container_width=True)

        # ── Downloads ──
        st.markdown("---")
        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button(
                "Download Full CPOC Summary",
                df_cpoc_summary.to_csv(index=False),
                "cpoc_summary.csv", "text/csv",
                use_container_width=True,
            )
        with dl2:
            st.download_button(
                "Download Performance Data",
                df_charts[["CPOC", "Valid", "Invalid", "Total QCd"]].to_csv(index=False),
                "cpoc_performance.csv", "text/csv",
                use_container_width=True,
            )
    else:
        st.warning("No data found in the QC Summary tab.")


# ═══════════════════════════════════════════════
#  RAW DATA PAGE
# ═══════════════════════════════════════════════
elif page == "Raw Data":
    st.title("Raw Data Explorer")

    tab1, tab2 = st.tabs(["Main Data", "QC Data"])

    with tab1:
        st.caption(f"{len(df_main):,} records")
        st.dataframe(df_main, use_container_width=True)
        st.download_button("Download Main Data", df_main.to_csv(index=False), "main.csv")

    with tab2:
        st.caption(f"{len(df_qc):,} records")
        st.dataframe(df_qc, use_container_width=True)
        st.download_button("Download QC Data", df_qc.to_csv(index=False), "qc.csv")