# Place this at app.py or your Streamlit script
# Make sure to configure your Streamlit secrets:
# [openrouter]
# api_key = "your_openrouter_key"

import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io
from fpdf import FPDF

# 💼 API Keys
OPENROUTER_API_KEY = st.secrets["openrouter"]["api_key"]

# 🎨 Streamlit setup
st.set_page_config(page_title="🧠 Your AI-Powered Financial Accountant", layout="wide")
st.title("🧠 Your AI-Powered Financial Accountant")

# 🌟 Marketing Pitch
st.markdown("#### 📊 Smarter Insights. Sharper Decisions. Instant Results.")
st.markdown("Your AI-Powered Financial Accountant doesn’t just crunch numbers – it thinks like a CFO. Upload your data and unlock professional-grade insights.")

# 📊 Industry Benchmarks
INDUSTRY_BENCHMARKS = {
    "Dairy": {"Debt-to-Equity Ratio": 1.2, "Equity Ratio": 0.45, "Current Ratio": 1.8, "ROE": 0.12, "Net Profit Margin": 0.08},
    "Tech": {"Debt-to-Equity Ratio": 0.5, "Equity Ratio": 0.7, "Current Ratio": 2.5, "ROE": 0.15, "Net Profit Margin": 0.2}
}

# 🧠 DeepSeek via OpenRouter
def openrouter_call(prompt):
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek/deepseek-r1:free",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024
        }
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"❌ OpenRouter error: {e}"

# 🧾 Forecast Table Parser
def parse_forecast_table(text_response):
    lines = [line.strip() for line in text_response.splitlines() if line.strip()]
    if len(lines) < 2: return pd.DataFrame()
    header = lines[0].split()
    rows = [line.split() for line in lines[1:] if len(line.split()) == len(header)]
    df = pd.DataFrame(rows, columns=header)
    for col in df.columns[1:]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

# 📥 PDF Exporter
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

# 📂 File Upload
uploaded_file = st.file_uploader("📂 Upload Excel or CSV File", type=["xlsx", "csv"])
if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file)
    df = df.loc[:, ~df.columns.duplicated()]
    df.rename(columns={df.columns[0]: "Fiscal Year"}, inplace=True)

    # Rename columns
    rename_map = {
        "Short-Term Liabilities": ["short", "current liability"],
        "Long-Term Liabilities": ["long", "non-current"],
        "Owner's Equity": ["equity", "owner"],
        "Current Assets": ["cash", "current asset"],
        "Revenue": ["revenue", "sales"],
        "Net Profit": ["net profit", "net income"]
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

    # ➗ Ratio calculations
    df["Total Liabilities"] = df["Short-Term Liabilities"] + df["Long-Term Liabilities"]
    df["Debt-to-Equity Ratio"] = df["Total Liabilities"] / df["Owner's Equity"]
    df["Equity Ratio"] = df["Owner's Equity"] / (df["Owner's Equity"] + df["Total Liabilities"])
    df["Current Ratio"] = df["Current Assets"] / df["Short-Term Liabilities"]
    df["ROE"] = df["Net Profit"] / df["Owner's Equity"]
    df["Net Profit Margin"] = df["Net Profit"] / df["Revenue"]

    # 📢 Display Info
    name = uploaded_file.name.replace(".xlsx", "").replace(".csv", "")
    industry = "Dairy" if "fonterra" in name.lower() or "milk" in name.lower() else "Unknown"
    st.success(f"🏢 Detected Company: {name} | 🏷️ Industry: {industry}")

    # 📑 Show Tables
    st.subheader("📑 Balance Sheet")
    st.dataframe(df[["Fiscal Year", "Short-Term Liabilities", "Long-Term Liabilities", "Owner's Equity"]])

    st.subheader("💰 Income Statement")
    st.dataframe(df[["Fiscal Year", "Revenue", "Net Profit"]])

    # 📈 Graphs
    st.subheader("📈 Ratio Trends")
    st.plotly_chart(px.line(df, x="Fiscal Year", y=["Debt-to-Equity Ratio", "Equity Ratio", "Current Ratio", "ROE", "Net Profit Margin"], markers=True))

    st.subheader("📊 Balance Sheet Components Over Time")
    st.plotly_chart(px.bar(df, x="Fiscal Year", y=["Short-Term Liabilities", "Long-Term Liabilities", "Owner's Equity"], barmode="group"))

    st.subheader("📊 Income Statement Components Over Time")
    st.plotly_chart(px.bar(df, x="Fiscal Year", y=["Revenue", "Net Profit"], barmode="group"))

    # 📏 Benchmark Comparison
    if industry in INDUSTRY_BENCHMARKS:
        st.subheader(f"🧮 Benchmark Comparison – {industry}")
        latest = df.iloc[-1]
        for ratio, bench in INDUSTRY_BENCHMARKS[industry].items():
            firm = latest.get(ratio)
            if pd.notna(firm):
                if abs(firm - bench) < 0.01 * bench:
                    emoji = "🟡 On Par"
                    color = ["gray", "gray"]
                elif firm > bench:
                    emoji = "🟢 Your firm is performing better"
                    color = ["green", "red"]
                else:
                    emoji = "🔴 Industry is performing better"
                    color = ["red", "green"]
                st.markdown(f"**{ratio}**: {firm:.2f} vs {bench:.2f} → {emoji}")
                st.plotly_chart(px.bar(
                    pd.DataFrame({"Source": ["Your Firm", "Industry"], "Value": [firm, bench]}),
                    x="Source", y="Value", color="Source", color_discrete_sequence=color
                ), use_container_width=True)

    # 💬 Commentary
    st.subheader("💬 DeepSeek Commentary")
    ratios = df.iloc[-1]
    prompt = f"Company is in the {industry} industry. Key Ratios:\n" + "\n".join([f"{k}: {ratios[k]:.2f}" for k in INDUSTRY_BENCHMARKS[industry].keys()])
    st.write(openrouter_call(prompt))

    # ❓ Q&A
    st.subheader("🧠 Ask DeepSeek")
    question = st.text_input("Ask a question about this firm's financials:")
    if question:
        data = df.tail(5).to_string(index=False)
        st.write(openrouter_call(f"Data:\n{data}\nQuestion:\n{question}"))

    # 🔮 Forecast
    st.subheader("🔮 Forecast (5 Years)")
    forecast_txt = openrouter_call("Forecast next 5 years for: Equity, Liabilities, Assets, Revenue, Profit.\nData:\n" + df.tail(5).to_string(index=False))
    st.code(forecast_txt)
    df_forecast = parse_forecast_table(forecast_txt)
    if not df_forecast.empty:
        st.dataframe(df_forecast)
        st.plotly_chart(px.line(df_forecast, x=df_forecast.columns[0], y=df_forecast.columns[1:], markers=True), use_container_width=True)

    # 📤 Download
    st.subheader("⬇️ Download Reports")
    excel = io.BytesIO()
    with pd.ExcelWriter(excel, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    st.download_button("⬇️ Excel Report", excel.getvalue(), file_name=f"{name}_report.xlsx")

    st.download_button("⬇️ PDF Report", create_pdf_report(df, name), file_name=f"{name}_report.pdf")
