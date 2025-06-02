
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import os
from datetime import datetime

st.title("📊 Monthly Customer Activity Dashboard")

UPLOAD_DIR = "uploaded_data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

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

st.sidebar.header("📂 Stored Files")

all_files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith(".xlsx")]
sort_order = st.sidebar.radio("Sort files by", ["Newest First", "Oldest First"])
available_files = sorted(all_files, reverse=(sort_order == "Newest First"))

if not available_files:
    st.warning("No uploaded files available.")
    st.stop()



# Compute Net Growth MRC
gains_df = filtered_data[filtered_data["Status"].isin(["NEW", "Convert", "Previous"])]
gains_mrc = gains_df["MRC"].sum()
churn_df = filtered_data[filtered_data["Status"] == "Disconnect"]
churn_mrc = churn_df["MRC"].sum()
net_growth_mrc = gains_mrc - churn_mrc

st.metric("Net Growth MRC (Gains - Churn)", f"${net_growth_mrc:,.2f}")

st.header("⚠️ Churn Summary by Reason")
churn_summary = churn_df.groupby("Reason").agg(Count=("Reason", "count")).reset_index()
st.dataframe(churn_summary)
st.metric("Churn Total MRC", f"${churn_mrc:,.2f}")

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
