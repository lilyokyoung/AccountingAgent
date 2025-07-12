import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import difflib

# Page setup
st.set_page_config(page_title="📊 Accounting Analyzer", layout="wide")

# ⬛ Black background styling for company info box
HIGHLIGHT_STYLE = """
<style>
.info-box {
    background-color: #000000;
    color: #ffffff;
    padding: 15px 20px;
    border-left: 6px solid #FF5722;
    margin-top: 15px;
    border-radius: 5px;
    font-size: 20px;
}
</style>
"""

# Gemini config
genai.configure(api_key=st.secrets["gemini"]["api_key"])
st.title("📈 Financial Statement Analyzer")

# Benchmarks
INDUSTRY_BENCHMARKS = {
    "Dairy": {
        "Debt-to-Equity Ratio": 1.20, "Equity Ratio": 0.45,
        "Current Ratio": 1.80, "ROE": 0.12, "Net Profit Margin": 0.08
    },
    "Tech": {
        "Debt-to-Equity Ratio": 0.50, "Equity Ratio": 0.70,
        "Current Ratio": 2.50, "ROE": 0.15, "Net Profit Margin": 0.20
    }
}

# Utilities
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

# 📂 Upload
uploaded_file = st.file_uploader("📂 Upload Excel/CSV", type=["xlsx", "csv"])
if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file)
    df.rename(columns={df.columns[0]: "Fiscal Year"}, inplace=True)

    fields = {
        "Short-Term Liabilities": None, "Long-Term Liabilities": None,
        "Owner's Equity": None, "Current Assets": None,
        "Revenue": None, "Net Profit": None
    }

    for field in fields:
        match = fuzzy_match(field, df.columns)
        if match:
            df.rename(columns={match: field}, inplace=True)

    industry = detect_industry(uploaded_file.name)

    # Inject custom style and display company info box
    st.markdown(HIGHLIGHT_STYLE, unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="info-box">
        🏢 <strong>Detected Company:</strong> {uploaded_file.name.replace('.xlsx', '').replace('.csv', '')}<br>
        🏷️ <strong>Industry:</strong> {industry}
        </div>
        """, unsafe_allow_html=True
    )

    if all(col in df.columns for col in ["Short-Term Liabilities", "Long-Term Liabilities", "Owner's Equity"]):
        df = compute_ratios(df)

        st.subheader("📋 Financial Ratios")
        st.dataframe(df[["Fiscal Year", "Debt-to-Equity Ratio", "Equity Ratio", "Current Ratio", "ROE", "Net Profit Margin"]])

        st.subheader("💬 Gemini Commentary")
        with st.spinner("Generating insights..."):
            st.markdown(ai_commentary(df, industry))
