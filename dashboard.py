
import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime

st.title("📊 Monthly Customer Activity Dashboard")

# --- Ensure upload directory exists ---
UPLOAD_DIR = "uploaded_data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- File Upload ---
st.sidebar.header("📤 Upload New Monthly File")
uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file and "just_uploaded" not in st.session_state:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_name = f"{timestamp}_{uploaded_file.name}"
    save_path = os.path.join(UPLOAD_DIR, saved_name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.session_state.just_uploaded = True
    st.rerun()

# --- Use the most recent uploaded file ---
uploaded_files = sorted(
    [f for f in os.listdir(UPLOAD_DIR) if f.endswith(".xlsx")],
    reverse=True
)

if not uploaded_files:
    st.warning("No uploaded files found. Please upload an Excel (.xlsx) file to begin.")
    st.stop()

latest_file = uploaded_files[0]
latest_path = os.path.join(UPLOAD_DIR, latest_file)
st.subheader(f"📂 Analyzing: `{latest_file}`")

# --- Load data ---
xls = pd.ExcelFile(latest_path)
df = xls.parse("Sheet1")

# --- Backup full data ---
full_df = df.copy()

# --- Clean and parse ---
df["Submission Date"] = pd.to_datetime(df["Submission Date"], errors="coerce")
df = df.dropna(subset=["Submission Date"])
df["Month"] = df["Submission Date"].dt.to_period("M").astype(str)

full_df["Submission Date"] = pd.to_datetime(full_df["Submission Date"], errors="coerce")
full_df = full_df.dropna(subset=["Submission Date"])
full_df["Month"] = full_df["Submission Date"].dt.to_period("M").astype(str)

# --- Filters ---
st.sidebar.header("🔎 Filters")
month_options = ["All"] + sorted(full_df["Month"].unique())
selected_month = st.sidebar.selectbox("Submission Month", month_options)
if selected_month != "All":
    df = df[df["Month"] == selected_month]

if "Category" in df.columns:
    cat_options = ["All"] + sorted(df["Category"].dropna().unique())
    selected_cat = st.sidebar.selectbox("Category", cat_options)
    if selected_cat != "All":
        df = df[df["Category"] == selected_cat]

if "Status" in df.columns:
    status_options = ["All"] + sorted(df["Status"].dropna().unique())
    selected_status = st.sidebar.selectbox("Status", status_options)
    if selected_status != "All":
        df = df[df["Status"] == selected_status]

if "Reason" in df.columns:
    reason_options = ["All"] + sorted(df["Reason"].dropna().unique())
    selected_reason = st.sidebar.selectbox("Reason", reason_options)
    if selected_reason != "All":
        df = df[df["Reason"] == selected_reason]

# --- Summary ---
st.header("📌 Totals by Category & Status")
summary = df.groupby(["Category", "Status"]).agg(Count=("Status", "count")).reset_index()
st.dataframe(summary)

# --- Churn Overview ---
st.header("📉 Churn by Reason")
disconnects = df[df["Status"] == "Disconnect"].copy()
disconnects["MRC"] = pd.to_numeric(disconnects["MRC"], errors="coerce").fillna(0)

churn_summary = disconnects.groupby("Reason").agg(
    Count=("Reason", "count"),
    Total_MRC=("MRC", "sum")
).reset_index()
st.dataframe(churn_summary)

# --- Total MRC Sum Display ---
if "Total_MRC" in churn_summary.columns and pd.api.types.is_numeric_dtype(churn_summary["Total_MRC"]):
    total_mrc_sum = churn_summary["Total_MRC"].sum()
    st.markdown(f"**Total Churn MRC:** ${total_mrc_sum:,.2f}")

# --- Charts ---
st.header("📊 Visualizations")

if not churn_summary.empty:
    churn_summary_sorted = churn_summary.sort_values(by="Count", ascending=True)
    fig1, ax1 = plt.subplots()
    ax1.barh(churn_summary_sorted["Reason"], churn_summary_sorted["Count"])
    ax1.set_title("Churn Count by Reason (Sorted)")
    st.pyplot(fig1)

if "Location" in disconnects.columns:
    loc_summary = disconnects.groupby("Location").agg(Count=("Location", "count")).reset_index()
    loc_summary_sorted = loc_summary.sort_values(by="Count", ascending=False).head(20)
    if not loc_summary_sorted.empty:
        fig2, ax2 = plt.subplots()
        ax2.bar(loc_summary_sorted["Location"], loc_summary_sorted["Count"])
        ax2.set_title("Churn by Location (Top 20)")
        ax2.tick_params(axis='x', rotation=90)
        st.pyplot(fig2)

pie_data = df["Status"].value_counts()
if not pie_data.empty:
    fig3, ax3 = plt.subplots()
    pie_data.plot.pie(autopct='%1.1f%%', ax=ax3)
    ax3.set_ylabel("")
    ax3.set_title("Status Breakdown")
    st.pyplot(fig3)

# --- New Customers Visualizations ---
st.header("📈 New Customers Visualizations")

new_customers = df[df["Status"] == "NEW"].copy()

if not new_customers.empty:
    cat_summary = new_customers.groupby("Category").size().sort_values(ascending=False)
    if not cat_summary.empty:
        fig4, ax4 = plt.subplots()
        cat_summary.plot(kind="bar", ax=ax4)
        ax4.set_title("New Customers by Category")
        ax4.set_xlabel("Category")
        ax4.set_ylabel("Count")
        st.pyplot(fig4)

    loc_summary = new_customers.groupby("Location").size().sort_values(ascending=False).head(20)
    if not loc_summary.empty:
        fig5, ax5 = plt.subplots()
        loc_summary.plot(kind="bar", ax=ax5)
        ax5.set_title("New Customers by Location (Top 20)")
        ax5.set_xlabel("Location")
        ax5.set_ylabel("Count")
        ax5.tick_params(axis='x', rotation=90)
        st.pyplot(fig5)

# --- Export Options ---
st.header("📤 Export Data")
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Filtered Data as CSV",
    data=csv,
    file_name="filtered_data.csv",
    mime="text/csv"
)

st.info("💡 To save the full dashboard as PDF (including charts), use your browser’s **Print → Save as PDF** option.")
