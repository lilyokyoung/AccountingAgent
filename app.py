import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io
import difflib
import uuid

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

# Config
OPENROUTER_API_KEY = st.secrets["openrouter"]["api_key"]

# Benchmarks
INDUSTRY_BENCHMARKS = {
    "Dairy": {"Debt-to-Equity Ratio": 1.2, "Equity Ratio": 0.45, "Current Ratio": 1.8, "ROE": 0.12, "Net Profit Margin": 0.08},
    "Tech": {"Debt-to-Equity Ratio": 0.5, "Equity Ratio": 0.7, "Current Ratio": 2.5, "ROE": 0.15, "Net Profit Margin": 0.2}
}

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

def ai_commentary_deepseek(df, industry):
    latest = df.iloc[-1]
    prompt = f"""You are a financial analyst. The company is in the {industry} industry.
Here are the latest ratios:
- Debt-to-Equity: {latest.get('Debt-to-Equity Ratio')}
- Equity Ratio: {latest.get('Equity Ratio')}
- Current Ratio: {latest.get('Current Ratio')}
- ROE: {latest.get('ROE')}
- Net Profit Margin: {latest.get('Net Profit Margin')}
Compare with industry benchmarks and give insights and recommendations."""
    
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek/deepseek-r1:free", "messages": [{"role": "user", "content": prompt}]}
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ DeepSeek error: {e}"

def ai_forecast_deepseek(df):
    prompt = f"""You are a finance expert. Based on this company's past data:\n{df.tail(5).to_string(index=False)}\n
Forecast next 5 years for:
Owner's Equity, Short-Term Liabilities, Long-Term Liabilities, Current Assets, Revenue, Net Profit.
Return forecast as a clean table with years as rows."""
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek/deepseek-r1:free", "messages": [{"role": "user", "content": prompt}]}
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ Forecast error: {e}"

def parse_forecast_table(text):
    try:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        header = lines[0].split()
        data = [line.split() for line in lines[1:] if len(line.split()) == len(header)]
        if not data: return None
        df = pd.DataFrame(data, columns=header)
        for col in df.columns[1:]:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except:
        return None

# Upload
uploaded_file = st.file_uploader("📂 Upload Excel or CSV File", type=["xlsx", "csv"])
if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file)
    df.rename(columns={df.columns[0]: "Fiscal Year"}, inplace=True)

    # Clean columns
    for field in ["Short-Term Liabilities", "Long-Term Liabilities", "Owner's Equity", "Current Assets", "Revenue", "Net Profit"]:
        match = fuzzy_match(field, df.columns)
        if match:
            df.rename(columns={match: field}, inplace=True)

    df = compute_ratios(df)

    industry = detect_industry(uploaded_file.name)
    company_name = uploaded_file.name.replace(".xlsx", "").replace(".csv", "")
    st.markdown(f"<div class='info-box'>🏢 Detected Company: <b>{company_name}</b><br>🏷️ Industry: <b>{industry}</b></div>", unsafe_allow_html=True)

    st.subheader("📑 Balance Sheet")
    st.dataframe(df[["Fiscal Year", "Short-Term Liabilities", "Long-Term Liabilities", "Owner's Equity"]])

    st.subheader("💰 Income Statement")
    st.dataframe(df[["Fiscal Year", "Revenue", "Net Profit"]])

    st.subheader("📈 Ratio Trends")
    st.plotly_chart(px.line(df, x="Fiscal Year", y=["Debt-to-Equity Ratio", "Equity Ratio", "Current Ratio", "ROE", "Net Profit Margin"], markers=True))

    st.subheader("📊 Balance Sheet Components Over Time")
    fig1 = px.bar(df, x="Fiscal Year", y=["Short-Term Liabilities", "Long-Term Liabilities", "Owner's Equity"], barmode="group")
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("📊 Income Statement Components Over Time")
    fig2 = px.bar(df, x="Fiscal Year", y=["Revenue", "Net Profit"], barmode="group")
    st.plotly_chart(fig2, use_container_width=True)

    if industry in INDUSTRY_BENCHMARKS:
        st.subheader(f"🧮 Benchmark Comparison – {industry}")
        latest = df.iloc[-1]
        for ratio, benchmark in INDUSTRY_BENCHMARKS[industry].items():
            val = latest.get(ratio)
            if pd.notna(val):
                if val > benchmark:
                    firm_color, ind_color = "green", "red"
                    tag = "🟢 Your firm is performing better"
                elif val < benchmark:
                    firm_color, ind_color = "red", "green"
                    tag = "🔴 Industry is performing better"
                else:
                    firm_color = ind_color = "gold"
                    tag = "🟡 On Par"
                st.markdown(f"**{ratio}**: {val:.2f} vs {benchmark:.2f} → {tag}")
                fig = px.bar(pd.DataFrame({"Source": ["Your Firm", "Industry"], ratio: [val, benchmark]}),
                             x="Source", y=ratio, color="Source",
                             color_discrete_map={"Your Firm": firm_color, "Industry": ind_color})
                st.plotly_chart(fig, use_container_width=True)

    st.subheader("💬 DeepSeek Commentary")
    with st.spinner("Generating commentary..."):
        st.markdown(ai_commentary_deepseek(df, industry))

    st.subheader("🧠 Ask DeepSeek")
    user_q = st.text_input("Ask a question about this firm or its ratios:")
    if user_q:
        response = ai_commentary_deepseek(df, f"User Question: {user_q}\nData:\n{df.tail(5).to_string(index=False)}")
        st.success(response)

    st.subheader("🔮 Forecast (5 Years)")
    with st.spinner("Generating forecast..."):
        forecast_txt = ai_forecast_deepseek(df)
        st.code(forecast_txt)
        df_forecast = parse_forecast_table(forecast_txt)
        if df_forecast is not None:
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(px.line(df_forecast, x=df_forecast.columns[0], y=df_forecast.columns[1:], markers=True), use_container_width=True)
            with col2:
                st.dataframe(df_forecast)

    # Botpress Q&A assistant
    st.subheader("🤖 Ask Your Financial Assistant (Botpress)")
    user_id = str(uuid.uuid4())
    config_url = "https://files.bpcontent.cloud/2025/07/02/02/20250702020605-VDMFG1YB.json"
    iframe_url = f"https://cdn.botpress.cloud/webchat/v3.0/shareable.html?configUrl={config_url}&userId={user_id}"
    st.markdown(f"""<iframe src="{iframe_url}" width="100%" height="600" style="border:none;" allow="microphone"></iframe>""", unsafe_allow_html=True)
