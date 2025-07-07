
import os
import pandas as pd
import streamlit as st
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="Customer Activity Report", layout="wide")
st.markdown("""<div style="text-align:center;"><img src='https://images.squarespace-cdn.com/content/v1/651eb4433b13e72c1034f375/369c5df0-5363-4827-b041-1add0367f447/PBB+long+logo.png?format=1500w' width="600"></div>""", unsafe_allow_html=True)

st.markdown("<h1 style='color:#405C88;'>📊 Monthly Customer Performance Report</h1>", unsafe_allow_html=True)
st.markdown("""
This dashboard presents key metrics and insights into customer churn and growth. 
It analyzes one uploaded file at a time, focusing on churn reasons, MRC impact, and new customer trends.
""")

# --- Ensure upload directory exists ---
UPLOAD_DIR = "uploaded_data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Manage Active File ---
if "current_file" not in st.session_state:
    if "current_file" in st.session_state:
        tmp_path = st.session_state["current_file"]
        if tmp_path.startswith("uploaded_data/tmp_") and os.path.exists(tmp_path): os.remove(tmp_path)
        del st.session_state["current_file"]

uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"], key="file_uploader")

if uploaded_file and not st.session_state.current_file:
    tmp_path = os.path.join(UPLOAD_DIR, f"tmp_{uploaded_file.name}")
    with open(tmp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.session_state.current_file = tmp_path

if st.sidebar.button("🚫 Clear Current File", key="clear_file_button"):
    if "current_file" in st.session_state:
        tmp_path = st.session_state["current_file"]
        if tmp_path.startswith("uploaded_data/tmp_") and os.path.exists(tmp_path): os.remove(tmp_path)
        del st.session_state["current_file"]

if "current_file" not in st.session_state or not st.session_state.current_file:
    st.info("Please upload a file to begin analysis.")
    st.stop()

latest_path = st.session_state.current_file
st.subheader(f"📂 Analyzing: `{os.path.basename(latest_path)}`")

# --- Load data ---

xls = pd.ExcelFile(latest_path)
if "Sheet1" not in xls.sheet_names:
    st.error("The uploaded file does not contain a sheet named 'Sheet1'. Please upload a valid file.")
    st.stop()
df = xls.parse("Sheet1")

expected_cols = ["Submission Date", "Status", "Reason", "Category", "Location"]
missing_cols = [col for col in expected_cols if col not in df.columns]
if missing_cols:
    st.error(f"The uploaded file is missing required columns: {', '.join(missing_cols)}.")
    st.stop()


df["Submission Date"] = pd.to_datetime(df["Submission Date"], errors="coerce")
df = df.dropna(subset=["Submission Date"])
if len(df) > 100000:
    st.warning("The uploaded file has more than 100,000 rows — this may affect performance.")
df["Month"] = df["Submission Date"].dt.to_period("M").astype(str)

# --- KPIs ---
total_customers = len(df)
disconnects = df[df["Status"] == "Disconnect"]
new_customers = df[df["Status"] == "NEW"]
churn_mrc = pd.to_numeric(disconnects["MRC"], errors="coerce").fillna(0).sum()

col1, col2, col3 = st.columns(3)
col1.metric("📈 Total Records", f"{total_customers}")
col2.metric("📉 Churned Customers", f"{len(disconnects)}")
col3.metric("💲 Churn MRC Impact", f"${churn_mrc:,.2f}")

st.markdown("---")

# --- Churn by Reason ---
st.header("Churn Analysis by Reason")
churn_summary = disconnects.groupby("Reason").agg(
    Count=("Reason", "count"),
    Total_MRC=("MRC", lambda x: pd.to_numeric(x, errors="coerce").fillna(0).sum())
).reset_index()
churn_summary = churn_summary.sort_values(by="Count", ascending=False)

st.dataframe(churn_summary, use_container_width=True)

fig_reason = px.bar(
    churn_summary,
    x="Count",
    y="Reason",
    orientation="h",
    title="Churn by Reason (Sorted)",
    color="Count", color_continuous_scale=["#7CB342", "#405C88"],
    height=500
)
st.plotly_chart(fig_reason, use_container_width=True, key="fig_reason")

# --- Churn by Location ---
st.header("Churn by Location (Top 20)")
loc_summary = disconnects.groupby("Location").size().reset_index(name="Count")
loc_summary = loc_summary.sort_values(by="Count", ascending=False).head(20)

fig_location = px.bar(
    loc_summary,
    x="Location",
    y="Count",
    title="Churn by Location (Top 20)",
    color="Count", color_continuous_scale=["#7CB342", "#405C88"]
)
st.plotly_chart(fig_location, use_container_width=True, key="fig_location")

# --- New Customers ---
st.header("New Customer Trends")
new_by_category = new_customers.groupby("Category").size().reset_index(name="Count").sort_values(by="Count", ascending=False)
new_by_location = new_customers.groupby("Location").size().reset_index(name="Count").sort_values(by="Count", ascending=False).head(20)

col4, col5 = st.columns(2)

with col4:
    fig_new_cat = px.bar(
        new_by_category,
        x="Category",
        y="Count",
        title="New Customers by Category",
        color="Count", color_continuous_scale=["#7CB342", "#405C88"]
    )
    st.plotly_chart(fig_new_cat, use_container_width=True, key="fig_new_cat")

with col5:
    fig_new_loc = px.bar(
        new_by_location,
        x="Location",
        y="Count",
        title="New Customers by Location (Top 20)",
        color="Count", color_continuous_scale=["#7CB342", "#405C88"]
    )
    st.plotly_chart(fig_new_loc, use_container_width=True, key="fig_new_loc")

st.markdown("---")
st.caption("<span style='color:#405C88;'>Professional Dashboard generated with ❤️ for Board Review</span>", unsafe_allow_html=True)


# --- Filters ---
if st.sidebar.button("🔄 Reset Filters", key="reset_filters"):
    st.session_state["month_filter"] = "All"
    st.session_state["category_filter"] = "All"
    st.session_state["status_filter"] = "All"
    st.session_state["reason_filter"] = "All"
    st.experimental_rerun()
st.sidebar.header("🔎 Filters")

month_options = ["All"] + sorted(df["Month"].unique())
selected_month = st.sidebar.selectbox("Submission Month", month_options, key="month_filter")
if selected_month != "All":
    df = df[df["Month"] == selected_month]

if "Category" in df.columns:
    cat_options = ["All"] + sorted(df["Category"].dropna().unique())
    selected_cat = st.sidebar.selectbox("Category", cat_options, key="category_filter")
    if selected_cat != "All":
        df = df[df["Category"] == selected_cat]

if "Status" in df.columns:
    status_options = ["All"] + sorted(df["Status"].dropna().unique())
    selected_status = st.sidebar.selectbox("Status", status_options, key="status_filter")
    if selected_status != "All":
        df = df[df["Status"] == selected_status]

if "Reason" in df.columns:
    reason_options = ["All"] + sorted(df["Reason"].dropna().unique())
    selected_reason = st.sidebar.selectbox("Reason", reason_options, key="reason_filter")
    if selected_reason != "All":
        df = df[df["Reason"] == selected_reason]

# --- KPIs ---
total_customers = len(df)
disconnects = df[df["Status"] == "Disconnect"]
new_customers = df[df["Status"] == "NEW"]
churn_mrc = pd.to_numeric(disconnects["MRC"], errors="coerce").fillna(0).sum()

col1, col2, col3 = st.columns(3)
col1.metric("📈 Total Records", f"{total_customers}")
col2.metric("📉 Churned Customers", f"{len(disconnects)}")
col3.metric("💲 Churn MRC Impact", f"${churn_mrc:,.2f}")

st.markdown("---")

# --- Churn by Reason ---
st.header("Churn Analysis by Reason")
churn_summary = disconnects.groupby("Reason").agg(
    Count=("Reason", "count"),
    Total_MRC=("MRC", lambda x: pd.to_numeric(x, errors="coerce").fillna(0).sum())
).reset_index()
churn_summary = churn_summary.sort_values(by="Count", ascending=False)

st.dataframe(churn_summary, use_container_width=True)

fig_reason = px.bar(
    churn_summary,
    x="Count",
    y="Reason",
    orientation="h",
    title="Churn by Reason (Sorted)",
    color="Count",
    height=500,
    color_continuous_scale=["#7CB342", "#405C88"]
)
st.plotly_chart(fig_reason, use_container_width=True, key="fig_reason")

# --- Churn by Location ---
st.header("Churn by Location (Top 20)")
loc_summary = disconnects.groupby("Location").size().reset_index(name="Count")
loc_summary = loc_summary.sort_values(by="Count", ascending=False).head(20)

fig_location = px.bar(
    loc_summary,
    x="Location",
    y="Count",
    title="Churn by Location (Top 20)",
    color="Count",
    color_continuous_scale=["#7CB342", "#405C88"]
)
st.plotly_chart(fig_location, use_container_width=True, key="fig_location")

# --- New Customers ---
st.header("New Customer Trends")
new_by_category = new_customers.groupby("Category").size().reset_index(name="Count").sort_values(by="Count", ascending=False)
new_by_location = new_customers.groupby("Location").size().reset_index(name="Count").sort_values(by="Count", ascending=False).head(20)

col4, col5 = st.columns(2)

with col4:
    fig_new_cat = px.bar(
        new_by_category,
        x="Category",
        y="Count",
        title="New Customers by Category",
        color="Count",
        color_continuous_scale=["#7CB342", "#405C88"]
    )
    st.plotly_chart(fig_new_cat, use_container_width=True, key="fig_new_cat")

with col5:
    fig_new_loc = px.bar(
        new_by_location,
        x="Location",
        y="Count",
        title="New Customers by Location (Top 20)",
        color="Count",
        color_continuous_scale=["#7CB342", "#405C88"]
    )
    st.plotly_chart(fig_new_loc, use_container_width=True, key="fig_new_loc")

st.markdown("---")
st.caption("<span style='color:#405C88;'>Professional Dashboard generated with ❤️ for Board Review</span>", unsafe_allow_html=True)
