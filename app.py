import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io
import uuid
from fpdf import FPDF

# API keys
OPENROUTER_API_KEY = st.secrets["openrouter"]["api_key"]

# App config
st.set_page_config(page_title="🧠 Your AI-Powered Financial Accountant", layout="wide")
st.title("🧠 Your AI-Powered Financial Accountant")

st.markdown("""
<style>
@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(50, 255, 50, 0.7); }
  70% { box-shadow: 0 0 0 20px rgba(50, 255, 50, 0); }
  100% { box-shadow: 0 0 0 0 rgba(50, 255, 50, 0); }
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
#### 📊 Smarter Insights. Sharper Decisions. Instant Results.
Your AI-Powered Financial Accountant doesn’t just crunch numbers – it thinks like a CFO. Upload your data and unlock professional-grade insights.
""", unsafe_allow_html=True)

# Benchmark data
INDUSTRY_BENCHMARKS = {
    "Dairy": {"Debt-to-Equity Ratio": 1.2, "Equity Ratio": 0.45, "Current Ratio": 1.8, "ROE": 0.12, "Net Profit Margin": 0.08},
    "Tech": {"Debt-to-Equity Ratio": 0.5, "Equity Ratio": 0.7, "Current Ratio": 2.5, "ROE": 0.15, "Net Profit Margin": 0.2}
}

# Helper functions
def compute_ratios(df):
    df["Total Liabilities"] = df["Short-Term Liabilities"] + df["Long-Term Liabilities"]
    df["Debt-to-Equity Ratio"] = df["Total Liabilities"] / df["Owner's Equity"]
    df["Equity Ratio"] = df["Owner's Equity"] / (df["Total Liabilities"] + df["Owner's Equity"])
    df["Current Ratio"] = df["Current Assets"] / df["Short-Term Liabilities"]
    df["ROE"] = df["Net Profit"] / df["Owner's Equity"]
    df["Net Profit Margin"] = df["Net Profit"] / df["Revenue"]
    return df

def detect_industry(name):
    name = name.lower()
    if "fonterra" in name or "milk" in name or "dairy" in name:
        return "Dairy"
    elif "tech" in name:
        return "Tech"
    return "Unknown"

def deepseek_response(prompt):
    try:
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
        payload = {"model": "deepseek/deepseek-r1:free", "messages": [{"role": "user", "content": prompt}]}
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ DeepSeek error: {e}"

def convert_df_to_excel(df):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    return buffer.getvalue()

class PDFReport(FPDF):
    def header(self):
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "📊 Financial Report", ln=True, align="C")
        self.ln(10)
    def add_table(self, df, title=""):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, title, ln=True)
        self.set_font("Arial", "", 10)
        col_width = self.w / (len(df.columns) + 1)
        for col in df.columns:
            self.cell(col_width, 10, str(col), border=1)
        self.ln()
        for _, row in df.iterrows():
            for val in row:
                self.cell(col_width, 10, str(val), border=1)
            self.ln()

def create_pdf_report(df, name):
    pdf = PDFReport()
    pdf.add_page()
    pdf.add_table(df[["Fiscal Year", "Debt-to-Equity Ratio", "Equity Ratio", "Current Ratio", "ROE", "Net Profit Margin"]],
                  title=f"{name} - Key Ratios")
    output = io.BytesIO()
    pdf.output(output)
    output.seek(0)
    return output

# Upload
uploaded_file = st.file_uploader("📂 Upload Excel or CSV File", type=["xlsx", "csv"])
if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file)
    df = df.loc[:, ~df.columns.duplicated()]
    df.rename(columns={df.columns[0]: "Fiscal Year"}, inplace=True)

    rename_map = {
        "Short-Term Liabilities": ["short"],
        "Long-Term Liabilities": ["long"],
        "Owner's Equity": ["equity"],
        "Current Assets": ["current assets"],
        "Revenue": ["revenue"],
        "Net Profit": ["net profit", "profit"]
    }
    used_targets = set()
    for target, patterns in rename_map.items():
        if target in df.columns: continue
        for col in df.columns:
            if col in used_targets: continue
            if any(p.lower() in col.lower() for p in patterns):
                df.rename(columns={col: target}, inplace=True)
                used_targets.add(col)
                break

    df = compute_ratios(df)
    company_name = uploaded_file.name.replace(".xlsx", "").replace(".csv", "")
    industry = detect_industry(company_name)

    st.markdown(f"<div class='info-box'>🏢 Detected Company: <b>{company_name}</b><br>🏷️ Industry: <b>{industry}</b></div>", unsafe_allow_html=True)

    # Tables
    st.subheader("📑 Balance Sheet")
    st.dataframe(df[["Fiscal Year", "Short-Term Liabilities", "Long-Term Liabilities", "Owner's Equity"]])

    st.subheader("💰 Income Statement")
    st.dataframe(df[["Fiscal Year", "Revenue", "Net Profit"]])

    # Ratio Trend
    st.subheader("📈 Ratio Trends")
    st.plotly_chart(px.line(df, x="Fiscal Year", y=["Debt-to-Equity Ratio", "Equity Ratio", "Current Ratio", "ROE", "Net Profit Margin"], markers=True))

    # Balance Sheet Bar
    st.subheader("📊 Balance Sheet Components Over Time")
    st.plotly_chart(px.bar(df, x="Fiscal Year", y=["Short-Term Liabilities", "Long-Term Liabilities", "Owner's Equity"], barmode="group"))

    # Income Statement Bar (All vars)
    st.subheader("📊 Income Statement Components Over Time")
    st.plotly_chart(px.bar(df, x="Fiscal Year", y=["Revenue", "Net Profit"], barmode="group"))

    # Benchmark Comparison
    if industry in INDUSTRY_BENCHMARKS:
        st.subheader(f"🧮 Benchmark Comparison – {industry}")
        latest = df.iloc[-1]
        for ratio, benchmark in INDUSTRY_BENCHMARKS[industry].items():
            val = latest.get(ratio)
            if pd.notna(val):
                firm_color = "green" if val > benchmark else "red"
                industry_color = "red" if val > benchmark else "green"
                status = "🟢 Your firm is performing better" if val > benchmark else "🔴 Industry is performing better"
                if abs(val - benchmark) <= 0.05 * benchmark:
                    status, firm_color, industry_color = "🟡 On Par", "gold", "gold"
                st.markdown(f"**{ratio}**: {val:.2f} vs {benchmark:.2f} → {status}")
                fig = px.bar(
                    pd.DataFrame({"Source": ["Your Firm", "Industry"], ratio: [val, benchmark]}),
                    x="Source", y=ratio, color="Source",
                    color_discrete_map={"Your Firm": firm_color, "Industry": industry_color}
                )
                st.plotly_chart(fig, use_container_width=True)

    # DeepSeek Commentary
    st.subheader("💬 DeepSeek Commentary")
    comment_prompt = f"Company in {industry} sector.\nRatios:\n" + df.iloc[-1][["Debt-to-Equity Ratio", "Equity Ratio", "Current Ratio", "ROE", "Net Profit Margin"]].to_string()
    commentary = deepseek_response(comment_prompt)
    st.markdown(commentary)

    # Q&A
    st.subheader("🧠 Ask DeepSeek")
    user_q = st.text_input("Ask a question about this firm or its ratios:")
    if user_q:
        response = deepseek_response(f"Firm data:\n{df.tail(5).to_string(index=False)}\nQuestion: {user_q}")
        st.success(response)

    # Forecast
    st.subheader("🔮 Forecast (5 Years)")
    forecast_prompt = f"""Forecast next 5 years for:
- Owner's Equity
- Short-Term Liabilities
- Long-Term Liabilities
- Current Assets
- Revenue
- Net Profit

Based on:\n{df.tail(5).to_string(index=False)}\nReturn as a clean table."""
    forecast = deepseek_response(forecast_prompt)
    st.text(forecast)

    # Downloads
    st.subheader("📥 Download Reports")
    st.download_button("⬇️ Excel Report", convert_df_to_excel(df), file_name="report.xlsx")
    st.download_button("⬇️ PDF Report", create_pdf_report(df, company_name), file_name="report.pdf")

    # Botpress Chat
    st.subheader("🤖 Ask Your Financial Assistant (Botpress)")
    user_id = str(uuid.uuid4())
    config_url = "https://files.bpcontent.cloud/2025/07/02/02/20250702020605-VDMFG1YB.json"
    iframe_url = f"https://cdn.botpress.cloud/webchat/v3.0/shareable.html?configUrl={config_url}&userId={user_id}"
    st.markdown(f"""
    <iframe src="{iframe_url}" width="100%" height="600" style="border: none;" allow="microphone"></iframe>
    """, unsafe_allow_html=True)
