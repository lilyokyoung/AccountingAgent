import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import difflib
import io
from fpdf import FPDF

# 🎯 Configuration
st.set_page_config(page_title="📊 Accounting Analyzer", layout="wide")
genai.configure(api_key=st.secrets["gemini"]["api_key"])

# 🎨 Styling
st.markdown("""
<style>
@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(0, 123, 255, 0.5); }
  70% { box-shadow: 0 0 0 15px rgba(0, 123, 255, 0); }
  100% { box-shadow: 0 0 0 0 rgba(0, 123, 255, 0); }
}
.info-box {
  background-color: black;
  color: white;
  padding: 20px;
  border-radius: 10px;
  border-left: 5px solid limegreen;
  font-size: 24px;
  animation: pulse 2s infinite;
}
</style>
""", unsafe_allow_html=True)

st.title("📈 Financial Statement Analyzer with Forecast & AI Insights")

INDUSTRY_BENCHMARKS = {
    "Dairy": {"Debt-to-Equity Ratio": 1.2, "Equity Ratio": 0.45, "Current Ratio": 1.8, "ROE": 0.12, "Net Profit Margin": 0.08},
    "Tech": {"Debt-to-Equity Ratio": 0.5, "Equity Ratio": 0.7, "Current Ratio": 2.5, "ROE": 0.15, "Net Profit Margin": 0.2}
}

# 📤 Upload
uploaded_file = st.file_uploader("📂 Upload Excel/CSV", type=["xlsx", "csv"])
if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file)
    df.rename(columns={df.columns[0]: "Fiscal Year"}, inplace=True)

    def fuzzy_match(target, columns, cutoff=0.6):
        match = difflib.get_close_matches(target, columns, n=1, cutoff=cutoff)
        return match[0] if match else None

    def detect_industry(name):
        name = name.lower()
        if "fonterra" in name or "milk" in name or "dairy" in name:
            return "Dairy"
        elif "tech" in name:
            return "Tech"
        return "Unknown"

    def compute_ratios(df):
        df["Total Liabilities"] = df["Short-Term Liabilities"] + df["Long-Term Liabilities"]
        df["Debt-to-Equity Ratio"] = df["Total Liabilities"] / df["Owner's Equity"]
        df["Equity Ratio"] = df["Owner's Equity"] / (df["Total Liabilities"] + df["Owner's Equity"])
        df["Current Ratio"] = df["Current Assets"] / df["Short-Term Liabilities"]
        df["ROE"] = df["Net Profit"] / df["Owner's Equity"]
        df["Net Profit Margin"] = df["Net Profit"] / df["Revenue"]
        return df

    def ai_commentary(df, industry):
        latest = df.iloc[-1]
        prompt = f"""You are a financial analyst. The company belongs to `{industry}` industry.
Latest financial ratios:
- Debt-to-Equity: {latest.get('Debt-to-Equity Ratio')}
- Equity Ratio: {latest.get('Equity Ratio')}
- Current Ratio: {latest.get('Current Ratio')}
- ROE: {latest.get('ROE')}
- Net Profit Margin: {latest.get('Net Profit Margin')}
Compare them to industry averages and offer brief recommendations."""
        response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
        return response.text.strip()

    def ai_forecast(df, industry):
        prompt = f"""You are a forecasting AI. Given the past 5 years of financial statement data:\n{df.tail(5).to_string(index=False)}\n
Generate a realistic 5-year forecast for:
- Owner's Equity
- Short-Term Liabilities
- Long-Term Liabilities
- Current Assets
- Revenue
- Net Profit
Return the forecast as a table with columns."""
        response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
        return response.text.strip()

    def parse_forecast_table(text_response):
        lines = text_response.splitlines()
        lines = [line for line in lines if line.strip()]
        header = lines[0].split()
        data = [line.split() for line in lines[1:] if len(line.split()) == len(header)]
        df_forecast = pd.DataFrame(data, columns=header)
        for col in df_forecast.columns[1:]:
            df_forecast[col] = pd.to_numeric(df_forecast[col], errors='coerce')
        return df_forecast

    def convert_df_to_excel(df):
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Financials')
        buffer.seek(0)
        return buffer

    class PDFReport(FPDF):
        def header(self):
            self.set_font("Arial", "B", 14)
            self.cell(0, 10, "Financial Analysis Report", ln=True, align="C")
            self.ln(10)
        def add_table(self, df, title="Table"):
            self.set_font("Arial", "B", 12)
            self.cell(0, 10, title, ln=True)
            self.set_font("Arial", size=10)
            col_width = self.w / (len(df.columns) + 1)
            for col in df.columns:
                self.cell(col_width, 10, str(col), border=1)
            self.ln()
            for _, row in df.iterrows():
                for val in row:
                    self.cell(col_width, 10, str(val), border=1)
                self.ln()

    def create_pdf_report(df, company_name):
        pdf = PDFReport()
        pdf.add_page()
        pdf.add_table(df[["Fiscal Year", "Debt-to-Equity Ratio", "Equity Ratio", "Current Ratio", "ROE", "Net Profit Margin"]],
                      title=f"{company_name} - Financial Ratios")
        pdf_output = io.BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)
        return pdf_output

    for field in ["Short-Term Liabilities", "Long-Term Liabilities", "Owner's Equity", "Current Assets", "Revenue", "Net Profit"]:
        match = fuzzy_match(field, df.columns)
        if match:
            df.rename(columns={match: field}, inplace=True)

    industry = detect_industry(uploaded_file.name)
    st.markdown(f"<div class='info-box'>🏢 Detected Company: <b>{uploaded_file.name.replace('.xlsx','').replace('.csv','')}</b><br>🏷️ Industry: <b>{industry}</b></div>", unsafe_allow_html=True)

    df = compute_ratios(df)

    st.subheader("📑 Balance Sheet")
    st.dataframe(df[["Fiscal Year", "Short-Term Liabilities", "Long-Term Liabilities", "Owner's Equity"]])

    st.subheader("💰 Income Statement")
    st.dataframe(df[["Fiscal Year", "Revenue", "Net Profit"]])

    st.subheader("📊 Balance Sheet Bar Chart")
    fig = px.bar(df, x="Fiscal Year", y=["Short-Term Liabilities", "Long-Term Liabilities", "Owner's Equity"], barmode="group")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Financial Ratios Table")
    st.dataframe(df[["Fiscal Year", "Debt-to-Equity Ratio", "Equity Ratio", "Current Ratio", "ROE", "Net Profit Margin"]])

    st.subheader("📈 Ratio Trends Over Time")
    fig = px.line(df, x="Fiscal Year", y=["Debt-to-Equity Ratio", "Equity Ratio", "Current Ratio", "ROE", "Net Profit Margin"], markers=True)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("💬 Gemini AI Commentary")
    st.markdown(ai_commentary(df, industry))

    st.subheader("🧠 Ask Gemini a Financial Question")
    user_q = st.text_input("Type your question about this firm or its trends:")
    if user_q:
        full_prompt = f"Here is the company's data:\n{df.tail(5).to_string(index=False)}\nQuestion: {user_q}"
        response = genai.GenerativeModel("gemini-1.5-flash").generate_content(full_prompt)
        st.success(response.text.strip())

    st.subheader("🔮 5-Year Forecast")
    forecast_txt = ai_forecast(df, industry)
    st.markdown(forecast_txt)
    df_forecast = parse_forecast_table(forecast_txt)
    if df_forecast is not None:
        fig = px.line(df_forecast, x=df_forecast.columns[0], y=df_forecast.columns[1:], markers=True,
                      title="📈 Forecasted Financials (Next 5 Years)")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("📥 Download Reports")
    st.download_button("⬇️ Download Excel Report", data=convert_df_to_excel(df), file_name="financial_analysis.xlsx")
    st.download_button("⬇️ Download PDF Report", data=create_pdf_report(df, uploaded_file.name.replace('.xlsx','')), file_name="financial_report.pdf")
