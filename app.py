import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import io
import os

st.set_page_config(page_title="Monthly Business Dashboard", layout="wide", page_icon="📊")

st.title("Monthly Business Dashboard")
st.markdown("Welcome! This dashboard helps visualize **Profit & Attendance Trends** over the months.")

st.sidebar.title("Navigation")
option = st.sidebar.radio("Go to", ["Overview", "Profit Calculator", "Attendance Insights"])

def generate_profit_plot(dataframe):
    fig, ax = plt.subplots(figsize=(6, 3))
    dataframe.plot(x='Month', y='Profit', kind='line', marker='o', ax=ax, color='blue', legend=False)
    ax.set_title("Monthly Profit Trend")
    ax.set_xlabel("Month")
    ax.set_ylabel("Profit (₹)")
    ax.grid(True)
    img_buffer = io.BytesIO()
    plt.tight_layout()
    plt.savefig(img_buffer, format='PNG')
    img_buffer.seek(0)
    plt.close()
    return img_buffer

def generate_attendance_charts():
    try:
        df = pd.read_csv("data/attendance_cleaned.csv")
    except FileNotFoundError:
        return None, None
    monthly = df.groupby("Month")[["Present", "Absent", "OT"]].sum().reset_index()
    fig1, ax1 = plt.subplots(figsize=(6, 3))
    monthly.set_index("Month").plot(kind="bar", ax=ax1)
    ax1.set_title("Monthly Attendance Summary")
    fig1.tight_layout()
    img1 = io.BytesIO()
    plt.savefig(img1, format='PNG')
    img1.seek(0)
    plt.close()

    pivot = df.pivot_table(index="Employee Name", columns="Month", values="Total Days", fill_value=0)
    fig2, ax2 = plt.subplots(figsize=(6, 3))
    pivot.T.plot(ax=ax2, legend=False)
    ax2.set_title("Employee Attendance Trend")
    fig2.tight_layout()
    img2 = io.BytesIO()
    plt.savefig(img2, format='PNG')
    img2.seek(0)
    plt.close()
    return img1, img2

def generate_full_pdf(data, profit_plot, att_plot1=None, att_plot2=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Monthly Profit & Attendance Report", ln=True, align='C')
    pdf.ln(10)
    
    for key, value in data.items():
        key_ascii = key.encode('ascii', 'ignore').decode()
        if isinstance(value, (int, float)):
            val_str = f"{value:,.2f}"
        else:
            val_str = str(value).encode('ascii', 'ignore').decode()
        pdf.cell(200, 10, txt=f"{key_ascii}: {val_str}", ln=True)

    def save_img(buffer, filename):
        with open(filename, "wb") as f:
            f.write(buffer.read())
        buffer.seek(0)

    save_img(profit_plot, "profit_plot.png")
    pdf.ln(5)
    pdf.image("profit_plot.png", x=10, w=180)

    if att_plot1:
        save_img(att_plot1, "attendance_summary.png")
        pdf.add_page()
        pdf.image("attendance_summary.png", x=10, w=180)

    if att_plot2:
        save_img(att_plot2, "attendance_trend.png")
        pdf.ln(10)
        pdf.image("attendance_trend.png", x=10, w=180)

    pdf_output = pdf.output(dest='S')
    pdf_bytes = pdf_output.encode('latin1') if isinstance(pdf_output, str) else pdf_output
    return io.BytesIO(pdf_bytes)

if option == "Overview":
    st.header("Business Summary Report")
    st.markdown("View monthly salary, income, and profit trends here.")

    if "profit_log" in st.session_state and st.session_state.profit_log:
        summary_df = pd.DataFrame(st.session_state.profit_log)

        st.subheader("Monthly Summary Table")
        st.dataframe(summary_df, use_container_width=True)

        st.subheader("Income vs Salary vs Profit")
        chart_df = summary_df[["Month", "Income", "Net Salary", "Profit"]].set_index("Month")
        st.bar_chart(chart_df)

    else:
        st.info("No data available yet. Please use the Profit Calculator first.")

elif option == "Profit Calculator":
    st.header("Monthly Profit Calculator")
    st.markdown("Predict monthly profit using manual input based on business logic.")

    month = st.selectbox("Select Month", [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ])

    st.subheader(f"Inputs for {month}")
    income = st.number_input("Income (₹)", min_value=0, step=10000, placeholder="Enter your income")
    gross_salary = st.number_input("Gross Salary (₹)", min_value=0, step=10000, placeholder="Enter gross salary")
    deductions = st.number_input("Deductions (₹)", min_value=0, step=1000, placeholder="PF + ESI deduction")
    emi = st.number_input("EMI (₹)", min_value=0, step=1000, placeholder="Enter EMI")
    office_expenses = st.number_input("Office Expenses (₹)", min_value=0, step=1000, placeholder="Enter office expenses")

    if "profit_log" not in st.session_state:
        st.session_state.profit_log = []

    if st.button(f"Calculate Profit for {month}"):
        salary = gross_salary - deductions
        profit = income - salary - emi - office_expenses

        st.success(f"Net Salary: ₹{salary:,.2f}")
        st.success(f"Predicted Profit for {month}: ₹{profit:,.2f}")
        st.markdown("---")
        st.info("Formula Used: `Profit = Income - (Gross Salary - Deductions) - EMI - Office Expenses`")

        st.session_state.profit_log.append({
            "Month": month,
            "Income": income,
            "Gross Salary": gross_salary,
            "Deductions": deductions,
            "EMI": emi,
            "Office Expenses": office_expenses,
            "Net Salary": salary,
            "Profit": profit
        })

        df = pd.DataFrame(st.session_state.profit_log)
        profit_graph = generate_profit_plot(df)
        att_graph1, att_graph2 = generate_attendance_charts()
        pdf = generate_full_pdf(st.session_state.profit_log[-1], profit_graph, att_graph1, att_graph2)

        st.download_button("Download Full Report PDF", data=pdf, file_name=f"{month}_Report.pdf", mime="application/pdf")

        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download All Logs as CSV", data=csv_data, file_name="monthly_profit_log.csv", mime="text/csv")


elif option == "Attendance Insights":
    st.header("📅 Attendance Insights")
    st.markdown("Upload your Form B CSV with at least these columns: 'Name', 'No of Days Worked', 'Total', 'Net Payment'.")

    month_context = st.selectbox("Which month's data is this?", [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ])

    uploaded_file = st.file_uploader("Upload Form B (CSV only)", type="csv")

    if uploaded_file:
        with st.spinner("Processing uploaded data..."):
            try:
                df_raw = pd.read_csv(uploaded_file)
                df_raw = df_raw.dropna(how="all").reset_index(drop=True)
                df_raw.columns = df_raw.columns.str.strip().str.lower()

                col_map = {
                    "name": "Employee Name",
                    "no of days worked": "Days Worked",
                    "total": "Total Earnings",
                    "net payment": "Net Payment"
                }

                if not set(col_map.keys()).issubset(df_raw.columns):
                    missing = set(col_map.keys()) - set(df_raw.columns)
                    st.error(f"❌ Missing column(s): {', '.join(missing)}")
                    st.stop()

                df = df_raw[list(col_map.keys())].copy()
                df.columns = [col_map[c] for c in df.columns]
                df = df[~df["Employee Name"].str.lower().str.strip().eq("total")]

                df["Days Worked"] = pd.to_numeric(df["Days Worked"], errors="coerce")
                df["Net Payment"] = pd.to_numeric(df["Net Payment"], errors="coerce")
                df.dropna(subset=["Employee Name", "Days Worked", "Net Payment"], inplace=True)

                st.subheader(f"📋 Summary Table – {month_context}")
                st.dataframe(df, use_container_width=True)

                st.subheader("📊 Days Worked per Employee")
                st.bar_chart(df.set_index("Employee Name")["Days Worked"])

                st.subheader("💰 Net Payment per Employee")
                st.line_chart(df.set_index("Employee Name")["Net Payment"])

                st.subheader("🔍 Filter by Employee")
                emp = st.selectbox("Select Employee", df["Employee Name"].dropna().unique())
                st.write(df[df["Employee Name"] == emp])

            except Exception as e:
                st.error(f"❌ Error reading file: {e}")
    else:
        st.info("📎 Please upload your Form B CSV.")

# ✅ Branding Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; font-size: 13px;'>"
    "🛠️ Powered by Streamlit • Built by Akassh"
    "</div>",
    unsafe_allow_html=True
)
