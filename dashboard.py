
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Load Excel file
xls = pd.ExcelFile("March Tally.xlsm")
data = xls.parse('Sheet1')

# Ensure MRC is numeric
data["MRC"] = pd.to_numeric(data["MRC"], errors="coerce")

st.title("📊 March Customer Activity Dashboard")

# --- Total Summary ---
st.header("Overall Totals by Status")
total_summary = data.groupby("Status").agg(
    Count=("Status", "count")
).reset_index()
total_mrc = data["MRC"].sum()
st.dataframe(total_summary)
st.metric("Total MRC", f"${total_mrc:,.2f}")

# --- Churn Breakdown ---
st.header("Churn Summary by Reason")
churn_df = data[data["Status"] == "Disconnect"]
churn_summary = churn_df.groupby("Reason").agg(
    Count=("Reason", "count")
).reset_index()
churn_total_mrc = churn_df["MRC"].sum()
st.dataframe(churn_summary)
st.metric("Churn Total MRC", f"${churn_total_mrc:,.2f}")

# --- Churn by Location ---
st.header("Churn by Location")
loc_summary = churn_df.groupby("Location").agg(
    Count=("Location", "count")
).sort_values(by="Count", ascending=False).reset_index()
st.dataframe(loc_summary)

# --- Visualizations ---
st.header("Visualizations")

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
category_counts = data["Status"].value_counts()
category_counts.plot(kind="pie", autopct='%1.1f%%', ax=ax3)
ax3.set_ylabel("")
ax3.set_title("Customer Status Breakdown")
st.pyplot(fig3)

st.info("Upload future months' files here to refresh the dashboard.")
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsm"])

if uploaded_file:
    st.success("File uploaded. To integrate auto-update, additional scripting would be needed.")
