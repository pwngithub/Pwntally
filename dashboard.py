
import os
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
import pdfkit
from jinja2 import Environment, FileSystemLoader

st.title("📊 Monthly Customer Activity Dashboard with PDF Export")

# --- Ensure directories exist ---
UPLOAD_DIR = "uploaded_data"
REPORTS_DIR = "reports"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

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

df["Submission Date"] = pd.to_datetime(df["Submission Date"], errors="coerce")
df = df.dropna(subset=["Submission Date"])
df["Month"] = df["Submission Date"].dt.to_period("M").astype(str)

# --- Metrics ---
disconnects = df[df["Status"] == "Disconnect"].copy()
disconnects["MRC"] = pd.to_numeric(disconnects["MRC"], errors="coerce").fillna(0)

churn_summary = disconnects.groupby("Reason").agg(
    Count=("Reason", "count"),
    Total_MRC=("MRC", "sum")
).reset_index()

st.header("📉 Churn by Reason")
st.dataframe(churn_summary)

total_mrc_sum = churn_summary["Total_MRC"].sum()
st.markdown(f"**Total Churn MRC:** ${total_mrc_sum:,.2f}")

# --- Charts ---
fig1, ax1 = plt.subplots()
churn_summary_sorted = churn_summary.sort_values(by="Count", ascending=True)
ax1.barh(churn_summary_sorted["Reason"], churn_summary_sorted["Count"])
ax1.set_title("Churn Count by Reason (Sorted)")
st.pyplot(fig1)

# Save chart as image for PDF
chart_path = os.path.join(REPORTS_DIR, "churn_reason_chart.png")
fig1.savefig(chart_path)

# --- PDF Export ---
st.header("📄 Export Dashboard as PDF")

if "generate_pdf" not in st.session_state:
    st.session_state.generate_pdf = False

if st.button("Generate PDF Report"):
    st.session_state.generate_pdf = True

if st.session_state.generate_pdf:
    env = Environment(loader=FileSystemLoader("."))
    template = env.from_string("""
    <html>
    <head><style>body { font-family: Arial; }</style></head>
    <body>
    <h1>Customer Activity Dashboard</h1>
    <h2>Churn by Reason</h2>
    {{ churn_table | safe }}
    <p><strong>Total Churn MRC:</strong> ${{ total_mrc_sum }}</p>
    <h2>Churn Reason Chart</h2>
    <img src="{{ chart_path }}" width="600"/>
    </body>
    </html>
    """)
    html_out = template.render(
        churn_table=churn_summary.to_html(index=False),
        total_mrc_sum=f"{total_mrc_sum:,.2f}",
        chart_path=chart_path
    )
    pdf_path = os.path.join(REPORTS_DIR, "dashboard_report.pdf")
    pdfkit.from_string(html_out, pdf_path)
    with open(pdf_path, "rb") as f:
        st.download_button("📥 Download PDF Report", data=f, file_name="dashboard_report.pdf", mime="application/pdf")
