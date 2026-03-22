from datetime import datetime

from utils.validators import REQUIRED_COLUMNS, find_missing_columns, normalize_dates
from utils.kpi_logic import calculate_kpis, month_series
from utils.risk_engine import THRESHOLDS, risk_scoring, insight_engine

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="QualiSight", page_icon="✅", layout="wide")


# -----------------------------
# Helpers
# -----------------------------
def load_file(uploaded_file) -> pd.DataFrame:
    if uploaded_file.name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    return pd.read_excel(uploaded_file)


@st.cache_data
def convert_df(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def plot_pareto(df: pd.DataFrame, category_col: str, title: str):
    if df.empty or category_col not in df.columns:
        st.info(f"No data available for {title}.")
        return

    counts = df[category_col].astype(str).value_counts().reset_index()
    counts.columns = [category_col, "count"]
    counts["cum_pct"] = counts["count"].cumsum() / counts["count"].sum() * 100

    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    ax1.bar(counts[category_col], counts["count"])
    ax1.set_ylabel("Count")
    ax1.set_xlabel(category_col.replace("_", " ").title())
    ax1.set_title(title)
    ax1.tick_params(axis="x", rotation=45)

    ax2 = ax1.twinx()
    ax2.plot(counts[category_col], counts["cum_pct"], marker="o")
    ax2.set_ylabel("Cumulative %")
    ax2.set_ylim(0, 110)

    st.pyplot(fig)


def plot_trend(series_df: pd.DataFrame, x_col: str, y_col: str, title: str):
    if series_df.empty:
        st.info(f"No data available for {title}.")
        return

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(series_df[x_col], series_df[y_col], marker="o")
    ax.set_title(title)
    ax.set_xlabel("Month")
    ax.set_ylabel(y_col.replace("_", " ").title())
    ax.tick_params(axis="x", rotation=45)
    st.pyplot(fig)


def demo_data() -> dict[str, pd.DataFrame]:
    complaints = pd.DataFrame({
        "complaint_id": ["C1", "C2", "C3", "C4"],
        "date": ["2026-01-02", "2026-01-11", "2026-02-06", "2026-02-18"],
        "product": ["Pump", "Pump", "Sensor", "Catheter"],
        "defect_category": ["Leak", "Leak", "Label", "Seal"],
        "severity": [4, 3, 2, 5],
        "root_cause": ["Seal fit", "Seal fit", "Print mismatch", "Handling"],
        "status": ["Closed", "Open", "Closed", "Open"],
    })

    ncm = pd.DataFrame({
        "ncm_id": ["N1", "N2", "N3", "N4", "N5"],
        "date": ["2026-01-03", "2026-01-09", "2026-01-25", "2026-02-09", "2026-02-20"],
        "line": ["L1", "L1", "L2", "L2", "L1"],
        "defect_category": ["Seal", "Seal", "Scratch", "Label", "Seal"],
        "severity": [5, 4, 2, 2, 4],
        "root_cause": ["Setup", "Setup", "Handling", "Artwork", "Setup"],
        "capa_linked": ["Y", "Y", "N", "N", "Y"],
        "status": ["Open", "Closed", "Open", "Closed", "Open"],
    })

    capa = pd.DataFrame({
        "capa_id": ["CA1", "CA2", "CA3"],
        "opened_date": ["2026-01-05", "2026-01-15", "2026-02-01"],
        "target_close_date": ["2026-01-20", "2026-02-10", "2026-02-20"],
        "closed_date": ["2026-01-18", None, None],
        "root_cause": ["Setup", "Seal fit", "Artwork"],
        "status": ["Closed", "Open", "Open"],
        "effectiveness": ["Effective", "Pending", "Pending"],
    })

    supplier = pd.DataFrame({
        "supplier_id": ["S1", "S1", "S2", "S3", "S2"],
        "lot_id": ["L001", "L002", "L003", "L004", "L005"],
        "received_qty": [10000, 12000, 8000, 7500, 8200],
        "defect_qty": [15, 18, 30, 8, 21],
        "defect_category": ["Seal", "Seal", "Label", "Particulate", "Label"],
        "scar_days": [12, 10, 21, 6, 18],
        "status": ["Approved", "Approved", "Escalated", "Approved", "Open"],
    })

    batch_release = pd.DataFrame({
        "batch_id": ["B1", "B2", "B3", "B4"],
        "date": ["2026-01-04", "2026-01-18", "2026-02-03", "2026-02-21"],
        "reviewer": ["A", "A", "B", "C"],
        "missing_fields": [0, 2, 4, 1],
        "deviation_flag": ["No", "Yes", "Yes", "No"],
        "approval_time_hours": [8, 16, 34, 10],
        "release_status": ["Released", "Released", "Hold", "Released"],
    })

    return {
        "complaints": complaints,
        "ncm": ncm,
        "capa": capa,
        "supplier": supplier,
        "batch_release": batch_release,
    }


# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("QualiSight")
st.sidebar.caption("Interactive Quality KPI, CAPA and Batch Release Intelligence Tool")
with st.expander("About this tool / How to use"):
    st.markdown("""
**What this tool does**
- Converts complaint, non-conformance, CAPA, supplier quality, and batch release records into quality KPIs and risk insights.
- Helps quality teams identify recurring defects, overdue actions, supplier risks, and release-readiness issues.

**How to use**
1. Upload one or more CSV/XLSX files from the sidebar, or enable demo data.
2. Apply optional filters such as product, line, supplier, or date range.
3. Review KPIs in the **Overview** tab.
4. Use **Trends & Pareto** to identify recurring defect categories.
5. Use **Supplier Quality** to review supplier risk scorecards.
6. Use **Batch Release** to identify high-risk batches and release delays.
7. Use **Data & Export** to inspect filtered data and download results.

**Who this is for**
- Quality Engineers
- Supplier Quality Engineers
- Manufacturing Quality teams
- Batch Release / documentation review teams
""")
    
st.sidebar.subheader("1) Upload files")
uploads = {}
for key, req_cols in REQUIRED_COLUMNS.items():
    uploads[key] = st.sidebar.file_uploader(
        f"Upload {key.replace('_', ' ').title()} file",
        type=["csv", "xlsx"],
        key=f"upload_{key}",
        help=f"Required columns: {', '.join(req_cols)}",
    )

use_demo = st.sidebar.checkbox("Use demo data", value=True)

data = demo_data() if use_demo else {}
validation_messages = []

for key, file in uploads.items():
    if file is not None:
        df = load_file(file)
        missing_cols = find_missing_columns(df, REQUIRED_COLUMNS[key])
        if missing_cols:
            validation_messages.append(f"{key.title()}: missing columns -> {', '.join(missing_cols)}")
        else:
            data[key] = df

st.sidebar.subheader("2) Filters")

selected_product = []
selected_line = []
selected_supplier = []

if "complaints" in data and "product" in data["complaints"].columns:
    selected_product = st.sidebar.multiselect(
        "Product",
        options=sorted(data["complaints"]["product"].dropna().unique())
    )

if "ncm" in data and "line" in data["ncm"].columns:
    selected_line = st.sidebar.multiselect(
        "Line",
        options=sorted(data["ncm"]["line"].dropna().unique())
    )

if "supplier" in data and "supplier_id" in data["supplier"].columns:
    selected_supplier = st.sidebar.multiselect(
        "Supplier",
        options=sorted(data["supplier"]["supplier_id"].dropna().unique())
    )

date_range = st.sidebar.date_input("Date Range", [])


# -----------------------------
# Main UI
# -----------------------------
st.title("QualiSight")
st.caption("Quality KPI, CAPA, Supplier Quality and Batch Release Intelligence for regulated manufacturing")

if validation_messages:
    for msg in validation_messages:
        st.error(msg)

if not data:
    st.warning("Upload at least one valid dataset or enable demo data in the sidebar.")
    st.stop()

for name, df in data.items():
    date_candidates = [c for c in df.columns if "date" in c.lower()]
    data[name] = normalize_dates(df, date_candidates)

# -----------------------------
# Apply Filters
# -----------------------------
if selected_product and "complaints" in data:
    data["complaints"] = data["complaints"][
        data["complaints"]["product"].isin(selected_product)
    ]

if selected_line and "ncm" in data:
    data["ncm"] = data["ncm"][
        data["ncm"]["line"].isin(selected_line)
    ]

if selected_supplier and "supplier" in data:
    data["supplier"] = data["supplier"][
        data["supplier"]["supplier_id"].isin(selected_supplier)
    ]

if len(date_range) == 2:
    start_date = pd.to_datetime(date_range[0])
    end_date = pd.to_datetime(date_range[1])

    for key in data:
        if "date" in data[key].columns:
            data[key] = data[key][
                (data[key]["date"] >= start_date) &
                (data[key]["date"] <= end_date)
            ]

kpis = calculate_kpis(data)
insights = insight_engine(data, kpis)
supplier_risk, batch_risk = risk_scoring(data)

overview_tab, trends_tab, supplier_tab, batch_tab, data_tab = st.tabs([
    "Overview", "Trends & Pareto", "Supplier Quality", "Batch Release", "Data & Export"
])

with overview_tab:
    cols = st.columns(4)
    metric_items = list(kpis.items())
    for i, (label, value) in enumerate(metric_items):
        col = cols[i % 4]
        if pd.isna(value):
            col.metric(label, "N/A")
        elif "Rate" in label:
            col.metric(label, f"{value:.1%}")
        elif "PPM" in label:
            col.metric(label, f"{value:,.0f}")
        elif "hrs" in label:
            col.metric(label, f"{value:.1f}")
        else:
            col.metric(label, f"{value:,.0f}")

    st.subheader("Priority insights")
    for insight in insights:
        st.write(f"- {insight}")

    st.subheader("Quick action heatmap")
    action_df = pd.DataFrame([
        ["Supplier PPM", kpis.get("Supplier PPM"), THRESHOLDS["supplier_ppm_high"]],
        ["Repeat NCM Rate", kpis.get("Repeat NCM Rate"), THRESHOLDS["repeat_ncm_high"]],
        ["Overdue CAPA Rate", kpis.get("Overdue CAPA Rate"), THRESHOLDS["capa_overdue_high"]],
        ["Batch Release TAT (hrs)", kpis.get("Batch Release TAT (hrs)"), THRESHOLDS["batch_delay_hours"]],
    ], columns=["metric", "current", "threshold"])
    action_df["status"] = np.where(action_df["current"] > action_df["threshold"], "Review", "Monitor")
    st.dataframe(action_df, use_container_width=True)

with trends_tab:
    c1, c2 = st.columns(2)
    with c1:
        plot_pareto(data.get("ncm", pd.DataFrame()), "defect_category", "Pareto of Non-Conformance Categories")
    with c2:
        plot_pareto(data.get("supplier", pd.DataFrame()), "defect_category", "Pareto of Supplier Defect Categories")

    t1, t2 = st.columns(2)
    with t1:
        complaints_trend = month_series(data.get("complaints", pd.DataFrame()), "date", "complaints")
        plot_trend(complaints_trend, "month", "complaints", "Monthly Complaint Trend")
    with t2:
        ncm_trend = month_series(data.get("ncm", pd.DataFrame()), "date", "ncm")
        plot_trend(ncm_trend, "month", "ncm", "Monthly NCM Trend")

with supplier_tab:
    st.subheader("Supplier Risk Scorecard")
    if supplier_risk.empty:
        st.info("Upload valid supplier data to see supplier scorecards.")
    else:
        st.dataframe(supplier_risk, use_container_width=True)
        top5 = supplier_risk.head(5).copy()
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.bar(top5["supplier_id"].astype(str), top5["risk_score"])
        ax.set_title("Top 5 Supplier Risk Scores")
        ax.set_xlabel("Supplier")
        ax.set_ylabel("Risk Score")
        st.pyplot(fig)

with batch_tab:
    st.subheader("Batch Release Risk Review")
    if batch_risk.empty:
        st.info("Upload valid batch release data to see release-readiness risk flags.")
    else:
        st.dataframe(batch_risk, use_container_width=True)
        high_risk = batch_risk[batch_risk["risk_flag"] == "High"]
        st.write(f"High-risk batch count: **{len(high_risk)}**")

with data_tab:
    st.subheader("Uploaded datasets")
    selected_dataset = st.selectbox("Choose dataset", list(data.keys()))
    st.dataframe(data[selected_dataset], use_container_width=True)
    st.download_button(
        label="Download selected dataset as CSV",
        data=convert_df(data[selected_dataset]),
        file_name=f"{selected_dataset}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )