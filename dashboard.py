
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import os
from datetime import datetime

st.title("📊 Monthly Customer Activity Dashboard")

# --- Shared Upload Directory ---
UPLOAD_DIR = "uploaded_data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Upload File ---
st.sidebar.header("📤 Upload a New Monthly File")
uploaded_file = st.sidebar.file_uploader("Choose an Excel File", type=["xlsx", "xlsm", "xls"])
if uploaded_file and "just_uploaded" not in st.session_state:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = uploaded_file.name.split(".")[-1].lower()
    filename = f"{timestamp}_{uploaded_file.name}"
    if ext in ["xls", "xlsm"]:
        filename = filename.replace(f".{ext}", ".xlsx")
    save_path = os.path.join(UPLOAD_DIR, filename)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.session_state.just_uploaded = True
    st.rerun()

# --- List Saved Files ---
st.sidebar.header("📂 Stored Files")
all_files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith(".xlsx")]
sort_order = st.sidebar.radio("Sort files by", ["Newest First", "Oldest First"])
available_files = sorted(all_files, reverse=(sort_order == "Newest First"))

if not available_files:
    st.warning("No uploaded files available.")
    st.stop()

selected_file = st.sidebar.selectbox("Choose a file to analyze", available_files)
selected_file_path = os.path.join(UPLOAD_DIR, selected_file)

# --- File Preview ---
with st.expander("📄 Preview First 5 Rows"):
    try:
        preview_df = pd.read_excel(selected_file_path, sheet_name="Sheet1", nrows=5)
        st.dataframe(preview_df)
    except Exception as e:
        st.error(f"Error previewing file: {e}")

# --- Analyze File ---
st.subheader(f"📂 Analyzing File: `{selected_file}`")
xls = pd.ExcelFile(selected_file_path)
data = xls.parse("Sheet1")

# --- Clean Data ---
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

status_options = ["All"] + sorted(filtered_data["Status"].dropna().unique())
selected_status = st.sidebar.selectbox("Status", status_options)
if selected_status != "All":
    filtered_data = filtered_data[filtered_data["Status"] == selected_status]

reason_options = ["All"] + sorted(filtered_data["Reason"].dropna().unique())
selected_reason = st.sidebar.selectbox("Reason", reason_options)
if selected_reason != "All":
    filtered_data = filtered_data[filtered_data["Reason"] == selected_reason]

customer_search = st.sidebar.text_input("Search Customer Name")
if customer_search:
    filtered_data = filtered_data[filtered_data["Customer Name"].str.contains(customer_search, case=False, na=False)]

# --- Totals ---
st.header("📌 Overall Totals")
total_summary = filtered_data.groupby("Status").agg(Count=("Status", "count")).reset_index()
adjusted_mrc = filtered_data.copy()
adjusted_mrc["MRC"] = adjusted_mrc.apply(
    lambda row: -row["MRC"] if row["Status"] == "Disconnect" else row["MRC"],
    axis=1
)
total_mrc = adjusted_mrc["MRC"].sum()
st.dataframe(total_summary)
st.metric("Net MRC", f"${total_mrc:,.2f}")

# --- Growth Status Summary ---
st.header("📈 Growth Summary (NEW, Convert, Previous)")
growth_df = filtered_data[filtered_data["Status"].isin(["NEW", "Convert", "Previous"])].copy()
growth_totals = growth_df.groupby("Status").agg(TotalMRC=("MRC", "sum")).reset_index()

new_mrc = growth_df[growth_df["Status"] == "NEW"]["MRC"].sum()
convert_mrc = growth_df[growth_df["Status"] == "Convert"]["MRC"].sum()
previous_mrc = growth_df[growth_df["Status"] == "Previous"]["MRC"].sum()

churn_df = filtered_data[filtered_data["Status"] == "Disconnect"]
churn_mrc = churn_df["MRC"].sum()
net_growth_mrc = new_mrc + convert_mrc + previous_mrc - churn_mrc

st.dataframe(growth_totals)
st.metric("Net Growth MRC (Gains - Churn)", f"${net_growth_mrc:,.2f}")

# --- Churn Reason Summary ---
st.header("⚠️ Churn Summary by Reason")
churn_summary = churn_df.groupby("Reason").agg(Count=("Reason", "count")).reset_index()
st.dataframe(churn_summary)
st.metric("Churn Total MRC", f"${churn_mrc:,.2f}")

# --- Disconnect Location Map (Always)
st.header("📍 Disconnects by Location")
disconnect_df = filtered_data[filtered_data["Status"] == "Disconnect"]
if not disconnect_df.empty:
    loc_summary = disconnect_df.groupby("Location").agg(Count=("Location", "count")).sort_values(by="Count", ascending=False).reset_index()
    st.dataframe(loc_summary)
    fig, ax = plt.subplots()
    ax.bar(loc_summary["Location"], loc_summary["Count"])
    ax.set_title("Disconnect Count by Location")
    ax.tick_params(axis='x', rotation=90)
    st.pyplot(fig)

# --- NEW/Convert/Previous Location View (if filtered)
if selected_status in ["NEW", "Convert", "Previous"]:
    st.subheader(f"📍 {selected_status} Customers by Location")
    status_df = filtered_data[filtered_data["Status"] == selected_status]
    if not status_df.empty:
        loc_summary = status_df.groupby("Location").agg(Count=("Location", "count")).sort_values(by="Count", ascending=False).reset_index()
        st.dataframe(loc_summary)
        fig, ax = plt.subplots()
        ax.bar(loc_summary["Location"], loc_summary["Count"])
        ax.set_title(f"{selected_status} Count by Location")
        ax.tick_params(axis='x', rotation=90)
        st.pyplot(fig)
