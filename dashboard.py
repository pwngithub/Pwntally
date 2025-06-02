
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.title("📊 Customer Service Activity Dashboard")

# File uploader
st.sidebar.header("📤 Upload Excel File")
uploaded_file = st.sidebar.file_uploader("Choose an Excel file", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
else:
    xls = pd.ExcelFile("1-6-2025.xlsx")

df = xls.parse('Sheet1')

# Clean and convert
df["MRC"] = pd.to_numeric(df["MRC"], errors="coerce")
df["Submission Date"] = pd.to_datetime(df["Submission Date"], errors="coerce")

# Filtered data
new_df = df[df["Status"] == "NEW"]
disconnect_df = df[df["Status"] == "Disconnect"]
convert_df = df[df["Status"] == "CONVERT"]
gains_df = df[df["Status"].isin(["NEW", "CONVERT"])]

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
