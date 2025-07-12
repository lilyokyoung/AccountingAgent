# ⚙️ Imports
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io

# 🔐 API keys
OPENROUTER_API_KEY = st.secrets["openrouter"]["api_key"]

# 🎯 Industry benchmarks
INDUSTRY_BENCHMARKS = {
    "Dairy": {"Debt-to-Equity Ratio": 1.2, "Equity Ratio": 0.45, "Current Ratio": 1.8, "ROE": 0.12, "Net Profit Margin": 0.08},
    "Tech": {"Debt-to-Equity Ratio": 0.5, "Equity Ratio": 0.7, "Current Ratio": 2.5, "ROE": 0.15, "Net Profit Margin": 0.2}
}

# 🧠 Streamlit setup
st.set_page_config(page_title="Your AI-Powered Financial Accountant", layout="wide")
st.title("🧠 Your AI-Powered Financial Accountant")
st.markdown("📊 Smarter Insights. Sharper Decisions. Instant Results.")

# 📤 Upload
uploaded_file = st.file_uploader("📂 Upload Excel or CSV File", type=["xlsx", "csv"])
if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file)
    df.rename(columns={df.columns[0]: "Fiscal Year"}, inplace=True)

    # 🔧 Rename key variables (try fuzzy matching if needed)
    rename_map = {
        "Short-Term Liabilities": ["short term", "st liabilities", "short liabilities"],
        "Long-Term Liabilities": ["long term", "lt liabilities"],
        "Owner's Equity": ["owner", "equity"],
        "Current Assets": ["current assets"],
        "Revenue": ["revenue", "sales"],
        "Net Profit": ["net", "profit", "earnings"]
    }

    for target, patterns in rename_map.items():
        for col in df.columns:
            if any(p.lower() in col.lower() for p in patterns):
                df.rename(columns={col: target}, inplace=True)
                break

    # 🧮 Compute ratios
    df["Total Liabilities"] = df["Short-Term Liabilities"] + df["Long-Term Liabilities"]
    df["Debt-to-Equity Ratio"] = df["Total Liabilities"] / df["Owner's Equity"]
    df["Equity Ratio"] = df["Owner's Equity"] / (df["Total Liabilities"] + df["Owner's Equity"])
    df["Current Ratio"] = df["Current Assets"] / df["Short-Term Liabilities"]
    df["ROE"] = df["Net Profit"] / df["Owner's Equity"]
    df["Net Profit Margin"] = df["Net Profit"] / df["Revenue"]

    # 🏷️ Detect industry
    filename = uploaded_file.name.lower()
    industry = "Dairy" if "dairy" in filename or "fonterra" in filename else "Tech" if "tech" in filename else "Unknown"
    st.markdown(f"🏢 **Detected Company:** `{uploaded_file.name}` &nbsp;&nbsp;&nbsp; 🏷️ **Industry:** `{industry}`")

    # 📑 Display tables
    st.subheader("📑 Balance Sheet")
    st.dataframe(df[["Fiscal Year", "Short-Term Liabilities", "Long-Term Liabilities", "Owner's Equity"]])

    st.subheader("💰 Income Statement")
    st.dataframe(df[["Fiscal Year", "Revenue", "Net Profit"]])

    st.subheader("📈 Ratio Trends")
    st.plotly_chart(px.line(df, x="Fiscal Year", y=["Debt-to-Equity Ratio", "Equity Ratio", "Current Ratio", "ROE", "Net Profit Margin"], markers=True))

    st.subheader("📊 Balance Sheet Components Over Time")
    st.plotly_chart(px.bar(df, x="Fiscal Year", y=["Short-Term Liabilities", "Long-Term Liabilities", "Owner's Equity"], barmode="group"))

    st.subheader("📊 Income Statement Components Over Time")
    st.plotly_chart(px.bar(df, x="Fiscal Year", y=["Revenue", "Net Profit"], barmode="group"))

    # 📊 Industry Benchmark Comparison
    if industry in INDUSTRY_BENCHMARKS:
        st.subheader(f"🧮 Benchmark Comparison – {industry}")
        latest = df.iloc[-1]
        for ratio, benchmark in INDUSTRY_BENCHMARKS[industry].items():
            val = latest.get(ratio)
            if pd.notna(val):
                if abs(val - benchmark) <= 0.05 * benchmark:
                    tag = "🟡 On Par"; colors = ["gold", "gold"]
                elif val > benchmark:
                    tag = "🟢 Your firm is performing better"; colors = ["green", "red"]
                else:
                    tag = "🔴 Industry is performing better"; colors = ["red", "green"]
                st.markdown(f"**{ratio}**: {val:.2f} vs {benchmark:.2f} → {tag}")
                chart_df = pd.DataFrame({"Source": ["Your Firm", "Industry"], ratio: [val, benchmark]})
                st.plotly_chart(px.bar(chart_df, x="Source", y=ratio, color="Source", color_discrete_sequence=colors), use_container_width=True)

    # 🔮 DeepSeek via OpenRouter
    def openrouter_call(prompt, model="deepseek/deepseek-r1:free", max_tokens=1024):
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens
        }
        try:
            resp = requests.post("https://openrouter.ai/api/v1/chat/completions", json=data, headers=headers)
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"❌ OpenRouter Error: {e}"

    # 💬 Commentary
    st.subheader("💬 DeepSeek Commentary")
    latest_ratios = f"""
    - Debt-to-Equity Ratio: {latest['Debt-to-Equity Ratio']:.2f}
    - Equity Ratio: {latest['Equity Ratio']:.2f}
    - Current Ratio: {latest['Current Ratio']:.2f}
    - ROE: {latest['ROE']:.2f}
    - Net Profit Margin: {latest['Net Profit Margin']:.2f}
    """
    commentary_prompt = f"You are a financial analyst. The company is in the {industry} industry. Here are the latest financial ratios:\n{latest_ratios}\nCompare to industry benchmarks and provide insights."
    st.info(openrouter_call(commentary_prompt))

    # 🧠 Q&A
    st.subheader("🧠 Ask DeepSeek")
    question = st.text_input("Ask anything about this firm or its performance:")
    if question:
        qa_prompt = f"Firm Data:\n{df.tail(3).to_string(index=False)}\n\nQuestion:\n{question}"
        st.success(openrouter_call(qa_prompt))

    # 📉 Forecast
    st.subheader("🔮 Forecast (5 Years)")
    forecast_prompt = f"Using this data:\n{df.tail(5).to_string(index=False)}\n\nForecast Revenue, Net Profit, and Owner's Equity for the next 5 years. Give results in table format."
    forecast = openrouter_call(forecast_prompt)
    st.code(forecast, language="markdown")

    # 📥 Downloads
    st.subheader("📥 Download Excel Report")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    st.download_button("⬇️ Download Excel", data=buffer.getvalue(), file_name="financial_report.xlsx")
