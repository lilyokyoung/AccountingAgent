import streamlit as st
import pandas as pd
import plotly.express as px
import difflib
import io
import requests
from fpdf import FPDF

# 🔐 OpenRouter API Key from secrets
OPENROUTER_API_KEY = st.secrets["openrouter"]["api_key"]

# 🧠 Unified LLM Caller via OpenRouter (DeepSeek Chat)
def openrouter_call(prompt, model="deepseek-chat", max_tokens=1024):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "AI Financial Forecasting"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7
    }
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        response_json = response.json()
        if "choices" in response_json:
            return response_json["choices"][0]["message"]["content"].strip()
        elif "error" in response_json:
            return f"❌ OpenRouter Error: {response_json['error'].get('message', 'Unknown')}"
        else:
            return f"❌ Unexpected response: {response_json}"
    except Exception as e:
        return f"❌ Request failed: {str(e)}"

# 🎨 App Setup and Branding
st.set_page_config(page_title="Your AI-Powered Financial Accountant", layout="wide")
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

# 📊 Benchmarks
INDUSTRY_BENCHMARKS = {
    "Dairy": {"Debt-to-Equity Ratio": 1.2, "Equity Ratio": 0.45, "Current Ratio": 1.8, "ROE": 0.12, "Net Profit Margin": 0.08},
    "Tech": {"Debt-to-Equity Ratio": 0.5, "Equity Ratio": 0.7, "Current Ratio": 2.5, "ROE": 0.15, "Net Profit Margin": 0.2}
}

# 🔧 Utilities
def fuzzy_match(target, columns):
    match = difflib.get_close_matches(target, columns, n=1, cutoff=0.6)
    return match[0] if match else None

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

def ai_commentary(df, industry):
    latest = df.iloc[-1]
    prompt = f"""You are a financial analyst. The company is in the {industry} industry.
Here are the latest ratios:
Debt-to-Equity: {latest.get('Debt-to-Equity Ratio')},
Equity Ratio: {latest.get('Equity Ratio')},
Current Ratio: {latest.get('Current Ratio')},
ROE: {latest.get('ROE')},
Net Profit Margin: {latest.get('Net Profit Margin')}
Compare with industry benchmarks and give concise advice."""
    return openrouter_call(prompt)

def ai_forecast(df, industry):
    prompt = f"""You are a financial forecasting expert.
Forecast the next 5 years for:
Owner's Equity, Short-Term Liabilities, Long-Term Liabilities, Current Assets, Revenue, Net Profit.
Based on:\n{df.tail(5).to_string(index=False)}\nReturn in table format using pipe separators."""
    return openrouter_call(prompt)

def parse_forecast_table(text_response):
    try:
        lines = [line.strip() for line in text_response.splitlines() if line.strip()]
        header = [h.strip() for h in lines[0].split("|")]
        data = [[v.strip() for v in row.split("|")] for row in lines[1:] if "|" in row]
        df_forecast = pd.DataFrame(data, columns=header)
        for col in df_forecast.columns[1:]:
            df_forecast[col] = pd.to_numeric(df_forecast[col], errors='coerce')
        return df_forecast
    except:
        return None

def convert_df_to_excel(df):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
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

# 📂 Upload file
uploaded_file = st.file_uploader("📂 Upload Excel or CSV File", type=["xlsx", "csv"])
if st.button("🧪 Test OpenRouter Connection"):
    st.write(openrouter_call("Say hello!"))

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file)
    df.rename(columns={df.columns[0]: "Fiscal Year"}, inplace=True)
    for field in ["Short-Term Liabilities", "Long-Term Liabilities", "Owner's Equity", "Current Assets", "Revenue", "Net Profit"]:
        match = fuzzy_match(field, df.columns)
        if match:
            df.rename(columns={match: field}, inplace=True)
    df = compute_ratios(df)

    industry = detect_industry(uploaded_file.name)
    company_name = uploaded_file.name.replace(".xlsx", "").replace(".csv", "")
    st.markdown(f"<div class='info-box'>🏢 Detected Company: <b>{company_name}</b><br>🏷️ Industry: <b>{industry}</b></div>", unsafe_allow_html=True)

    balance_vars = [col for col in df.columns if "Liabilities" in col or "Equity" in col or "Assets" in col]
    income_vars = [col for col in df.columns if col not in balance_vars and col not in ['Fiscal Year'] and df[col].dtype != 'O']

    st.subheader("📑 Balance Sheet")
    st.dataframe(df[["Fiscal Year"] + balance_vars])

    st.subheader("💰 Income Statement")
    st.dataframe(df[["Fiscal Year"] + income_vars])

    st.subheader("📈 Ratio Trends")
    ratio_cols = ["Debt-to-Equity Ratio", "Equity Ratio", "Current Ratio", "ROE", "Net Profit Margin"]
    st.plotly_chart(px.line(df, x="Fiscal Year", y=ratio_cols, markers=True))

    st.subheader("📊 Balance Sheet Components Over Time")
    st.plotly_chart(px.bar(df, x="Fiscal Year", y=balance_vars, barmode="group"), use_container_width=True)

    st.subheader("📊 Income Statement Components Over Time")
    st.plotly_chart(px.bar(df, x="Fiscal Year", y=income_vars, barmode="group"), use_container_width=True)

    if industry in INDUSTRY_BENCHMARKS:
        st.subheader(f"🧮 Benchmark Comparison – {industry}")
        latest = df.iloc[-1]
        for ratio, benchmark in INDUSTRY_BENCHMARKS[industry].items():
            val = latest.get(ratio)
            if pd.notna(val):
                if val > benchmark:
                    colors = ["#32CD32", "red"]
                    tag = "🟢 Your firm is performing better"
                elif val < benchmark:
                    colors = ["red", "#32CD32"]
                    tag = "🔴 Industry is performing better"
                else:
                    colors = ["#FFD700", "#FFD700"]
                    tag = "🟡 On Par"
                st.markdown(f"**{ratio}**: {val:.2f} vs {benchmark:.2f} → {tag}")
                fig = px.bar(pd.DataFrame({"Source": ["Your Firm", "Industry"], ratio: [val, benchmark]}),
                             x="Source", y=ratio, color="Source", color_discrete_sequence=colors)
                st.plotly_chart(fig, use_container_width=True)

    st.subheader("💬 DeepSeek Commentary")
    st.markdown(ai_commentary(df, industry))

    st.subheader("🧠 Ask DeepSeek")
    user_q = st.text_input("Ask a question about this firm or its ratios:")
    if user_q:
        answer = openrouter_call(f"Data:\n{df.tail(5).to_string(index=False)}\nQuestion: {user_q}")
        st.success(answer)

    st.subheader("🔮 Forecast (5 Years)")
    forecast_txt = ai_forecast(df, industry)
    st.code(forecast_txt)
    df_forecast = parse_forecast_table(forecast_txt)
    if df_forecast is not None and not df_forecast.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📈 Forecast Chart")
            st.plotly_chart(px.line(df_forecast, x=df_forecast.columns[0], y=df_forecast.columns[1:], markers=True), use_container_width=True)
        with col2:
            st.subheader("📋 Forecast Table")
            st.dataframe(df_forecast.style.format("{:,.0f}"), use_container_width=True)
    else:
        st.warning("❌ Forecast could not be parsed.")

    st.subheader("📥 Download Reports")
    st.download_button("⬇️ Excel Report", convert_df_to_excel(df), file_name="report.xlsx")
    st.download_button("⬇️ PDF Report", create_pdf_report(df, company_name), file_name="report.pdf")
