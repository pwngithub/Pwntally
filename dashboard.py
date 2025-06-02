
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import os
from datetime import datetime

st.title("📊 Customer Service Activity Dashboard")

# --- File Upload and Storage ---
UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.sidebar.header("📤 Upload Excel File")
uploaded_file = st.sidebar.file_uploader("Choose an Excel file", type=["xlsx"])

if uploaded_file:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{uploaded_file.name}")
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"File saved: {uploaded_file.name}")
    st.rerun()

# --- Load Most Recent File Automatically ---
available_files = sorted(
    [f for f in os.listdir(UPLOAD_DIR) if f.endswith(".xlsx")],
    reverse=True
)

if not available_files:
    st.warning("No uploaded files yet. Please upload an .xlsx file to continue.")
    st.stop()

latest_file = available_files[0]
latest_file_path = os.path.join(UPLOAD_DIR, latest_file)
st.subheader(f"📂 Analyzing File: `{latest_file}`")

xls = pd.ExcelFile(latest_file_path)
df = xls.parse('Sheet1')

# --- Clean and process ---
df["MRC"] = pd.to_numeric(df["MRC"], errors="coerce")
df["Submission Date"] = pd.to_datetime(df["Submission Date"], errors="coerce")

new_df = df[df["Status"] == "NEW"]
disconnect_df = df[df["Status"] == "Disconnect"]
convert_df = df[df["Status"] == "CONVERT"]
gains_df = df[df["Status"].isin(["NEW", "CONVERT"])]


# --- Filters ---
st.sidebar.header("🔍 Filter Data")
category_options = ["All"] + sorted(df["Category"].dropna().unique().tolist())
selected_category = st.sidebar.selectbox("Category", category_options)
if selected_category != "All":
    df = df[df["Category"] == selected_category]


status_options = ["All"] + sorted(df["Status"].dropna().unique().tolist())
selected_status = st.sidebar.selectbox("Status", status_options)
if selected_status != "All":
    df = df[df["Status"] == selected_status]


reason_options = ["All"] + sorted(df["Reason"].dropna().unique().tolist())
selected_reason = st.sidebar.selectbox("Reason", reason_options)
if selected_reason != "All":
    df = df[df["Reason"] == selected_reason]


# --- Fix Submission Date dtype ---
if "Submission Date" in df.columns:
    df["Submission Date"] = pd.to_datetime(df["Submission Date"], errors="coerce")
    df["Month"] = df["Submission Date"].dt.to_period("M").astype(str)
    month_options = ["All"] + sorted(df["Month"].dropna().unique().tolist())
    selected_month = st.sidebar.selectbox("Submission Month", month_options)
    if selected_month != "All":
        df = df[df["Month"] == selected_month]

# --- Metrics ---




st.header("📌 Key Metrics")
total_new = new_df.shape[0]
total_disconnects = disconnect_df.shape[0]
total_convert = convert_df.shape[0]
mrc_gained = gains_df["MRC"].sum()
mrc_lost = disconnect_df["MRC"].sum()
net_mrc = mrc_gained - mrc_lost

col1, col2, col3 = st.columns(3)
col1.metric("🆕 New Customers", total_new)
col2.metric("🔌 Disconnects", total_disconnects)
col3.metric("💵 Net MRC Change", f"${net_mrc:,.2f}")

# --- Totals by Category ---
st.header("📂 Total Count by Category")
category_summary = df.groupby("Category").agg(Count=("Category", "count")).reset_index()
st.dataframe(category_summary)

# --- Visualizations ---
st.header("📊 Visualizations")

# Pie chart of Status
fig1, ax1 = plt.subplots()
status_counts = df["Status"].value_counts()
status_counts.plot(kind="pie", autopct="%1.1f%%", ax=ax1)
ax1.set_ylabel("")
ax1.set_title("Service Status Breakdown")
st.pyplot(fig1)

# Bar chart of Disconnect Reasons
if not disconnect_df.empty:
    fig2, ax2 = plt.subplots()
    reason_counts = disconnect_df["Reason"].value_counts().sort_values()
    ax2.barh(reason_counts.index, reason_counts.values)
    ax2.set_title("Churn Count by Reason")
    st.pyplot(fig2)

# Bar chart of New Customers by Location
if not new_df.empty:
    fig3, ax3 = plt.subplots()
    new_loc_counts = new_df["Location"].value_counts().sort_values(ascending=False)
    ax3.bar(new_loc_counts.index, new_loc_counts.values)
    ax3.set_title("New Customers by Location")
    ax3.tick_params(axis='x', rotation=90)
    st.pyplot(fig3)
