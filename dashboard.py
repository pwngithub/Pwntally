
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import os
from datetime import datetime

st.title("📊 Monthly Customer Activity Dashboard")

# --- File Upload & Persistence ---
UPLOAD_DIR = "uploaded_data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.sidebar.header("📤 Upload New Monthly File")
uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsm"])

if uploaded_file:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{uploaded_file.name}")
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success(f"Saved: {save_path}")

# List uploaded files
available_files = sorted([f for f in os.listdir(UPLOAD_DIR) if f.endswith(".xlsm")], reverse=True)
selected_file = st.sidebar.selectbox("📂 Select file to analyze", available_files)

if not selected_file:
    st.warning("Please upload and select a file to continue.")
    st.stop()

xls = pd.ExcelFile(os.path.join(UPLOAD_DIR, selected_file))
data = xls.parse('Sheet1')

# --- Data Prep ---
data["MRC"] = pd.to_numeric(data["MRC"], errors="coerce")
data["Submission Date"] = pd.to_datetime(data["Submission Date"], errors="coerce")

# --- Filters ---
st.sidebar.header("🔍 Filters")
min_date, max_date = data["Submission Date"].min(), data["Submission Date"].max()
start_date, end_date = st.sidebar.date_input("Submission Date Range", [min_date, max_date])
filtered_data = data[
    (data["Submission Date"] >= pd.Timestamp(start_date)) &
    (data["Submission Date"] <= pd.Timestamp(end_date))
]

# Status Filter
status_options = ["All"] + sorted(filtered_data["Status"].dropna().unique().tolist())
selected_status = st.sidebar.selectbox("Status", status_options)
if selected_status != "All":
    filtered_data = filtered_data[filtered_data["Status"] == selected_status]

# Reason Filter
reason_options = ["All"] + sorted(filtered_data["Reason"].dropna().unique().tolist())
selected_reason = st.sidebar.selectbox("Reason", reason_options)
if selected_reason != "All":
    filtered_data = filtered_data[filtered_data["Reason"] == selected_reason]

# Customer Name Search
customer_search = st.sidebar.text_input("Search Customer Name")
if customer_search:
    filtered_data = filtered_data[filtered_data["Customer Name"].str.contains(customer_search, case=False, na=False)]

# --- Total Summary ---
st.header(f"📌 Overall Totals – {selected_file}")
total_summary = filtered_data.groupby("Status").agg(Count=("Status", "count")).reset_index()
total_mrc = filtered_data["MRC"].sum()
st.dataframe(total_summary)
st.metric("Total MRC", f"${total_mrc:,.2f}")

# --- Churn Summary ---
st.header("⚠️ Churn Summary by Reason")
churn_df = filtered_data[filtered_data["Status"] == "Disconnect"]
churn_summary = churn_df.groupby("Reason").agg(Count=("Reason", "count")).reset_index()
churn_total_mrc = churn_df["MRC"].sum()
st.dataframe(churn_summary)
st.metric("Churn Total MRC", f"${churn_total_mrc:,.2f}")

# --- Churn by Location ---
st.header("📍 Churn by Location")
loc_summary = churn_df.groupby("Location").agg(Count=("Location", "count")).sort_values(by="Count", ascending=False).reset_index()
st.dataframe(loc_summary)

# --- Visualizations ---
st.header("📊 Visualizations")

fig1, ax1 = plt.subplots()
ax1.barh(churn_summary["Reason"], churn_summary["Count"])
ax1.set_title("Churn Count by Reason")
st.pyplot(fig1)

fig2, ax2 = plt.subplots()
ax2.bar(loc_summary["Location"], loc_summary["Count"])
ax2.set_title("Churn Count by Location")
ax2.tick_params(axis='x', rotation=90)
st.pyplot(fig2)

fig3, ax3 = plt.subplots()
category_counts = filtered_data["Status"].value_counts()
category_counts.plot(kind="pie", autopct='%1.1f%%', ax=ax3)
ax3.set_ylabel("")
ax3.set_title("Customer Status Breakdown")
st.pyplot(fig3)

# --- Trend Chart ---
st.header("📈 Daily Activity Trend")
daily_trend = filtered_data.groupby(["Submission Date", "Status"]).size().unstack(fill_value=0)
st.line_chart(daily_trend)
