
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Load Excel file
xls = pd.ExcelFile("March Tally.xlsm")
data = xls.parse('Sheet1')

# Ensure proper types
data["MRC"] = pd.to_numeric(data["MRC"], errors="coerce")
data["Submission Date"] = pd.to_datetime(data["Submission Date"], errors="coerce")

st.title("📊 Enhanced March Customer Activity Dashboard")

# --- Filters ---
st.sidebar.header("🔍 Filters")
# Date Range
min_date, max_date = data["Submission Date"].min(), data["Submission Date"].max()
start_date, end_date = st.sidebar.date_input("Submission Date Range", [min_date, max_date])
filtered_data = data[
    (data["Submission Date"] >= pd.Timestamp(start_date)) &
    (data["Submission Date"] <= pd.Timestamp(end_date))
]

# Employee Filter
employee_options = ["All"] + sorted(filtered_data["Employee"].dropna().unique().tolist())
selected_employee = st.sidebar.selectbox("Employee", employee_options)
if selected_employee != "All":
    filtered_data = filtered_data[filtered_data["Employee"] == selected_employee]

# Location Filter
location_options = ["All"] + sorted(filtered_data["Location"].dropna().unique().tolist())
selected_location = st.sidebar.selectbox("Location", location_options)
if selected_location != "All":
    filtered_data = filtered_data[filtered_data["Location"] == selected_location]

# --- Total Summary ---
st.header("📌 Overall Totals")
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

# --- Upload ---
st.sidebar.header("📤 Upload New Data")
uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsm"])
if uploaded_file:
    st.sidebar.success("File uploaded. (App refresh/reload will be needed to process.)")
