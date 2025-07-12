import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# 🔐 Secrets
genai.configure(api_key=st.secrets["gemini"]["api_key"])

st.set_page_config(page_title="📊 Accounting Ratio Analyzer", layout="wide")
st.title("📈 Financial Statement Analyzer with AI Advice")

uploaded_file = st.file_uploader("📂 Upload Balance Sheet Excel", type=["xlsx", "csv"])

# Optional ratio logic
def compute_ratios(df):
    df["Total Liabilities"] = df["Short-Term Liabilities"] + df["Long-Term Liabilities"]
    df["Debt-to-Equity Ratio"] = df["Total Liabilities"] / df["Owner's Equity"]
    df["Equity Ratio"] = df["Owner's Equity"] / (df["Total Liabilities"] + df["Owner's Equity"])

    if "Current Assets" in df.columns:
        df["Current Ratio"] = df["Current Assets"] / df["Short-Term Liabilities"]
    else:
        df["Current Ratio"] = None

    if "Net Profit" in df.columns:
        df["ROE"] = df["Net Profit"] / df["Owner's Equity"]
    else:
        df["ROE"] = None

    if "Revenue" in df.columns and "Net Profit" in df.columns:
        df["Net Profit Margin"] = df["Net Profit"] / df["Revenue"]
    else:
        df["Net Profit Margin"] = None

    return df

def ai_commentary(df):
    latest = df.iloc[-1]
    prompt = f"""You are a financial analyst. The following ratios were computed for the latest year:

- Debt-to-Equity: {latest['Debt-to-Equity Ratio']:.2f}
- Equity Ratio: {latest['Equity Ratio']:.2f}
- Current Ratio: {latest.get('Current Ratio', 'N/A')}
- ROE: {latest.get('ROE', 'N/A')}
- Net Profit Margin: {latest.get('Net Profit Margin', 'N/A')}

Please provide a short, professional summary with suggestions and warnings if applicable."""
    response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
    return response.text.strip()

# App logic
if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file)
    df.rename(columns={df.columns[0]: "Fiscal Year"}, inplace=True)

    # Auto map
    col_map = {
        "Short-Term Liabilities": None,
        "Long-Term Liabilities": None,
        "Owner's Equity": None,
        "Current Assets": None,
        "Net Profit": None,
        "Revenue": None
    }

    for col in df.columns:
        col_lower = col.lower()
        if not col_map["Short-Term Liabilities"] and ("short" in col_lower or "current liab" in col_lower):
            col_map["Short-Term Liabilities"] = col
        elif not col_map["Long-Term Liabilities"] and ("long" in col_lower or "non" in col_lower):
            col_map["Long-Term Liabilities"] = col
        elif not col_map["Owner's Equity"] and ("equity" in col_lower or "net worth" in col_lower):
            col_map["Owner's Equity"] = col
        elif not col_map["Current Assets"] and ("current asset" in col_lower):
            col_map["Current Assets"] = col
        elif not col_map["Net Profit"] and ("net profit" in col_lower or "net income" in col_lower):
            col_map["Net Profit"] = col
        elif not col_map["Revenue"] and ("revenue" in col_lower or "sales" in col_lower):
            col_map["Revenue"] = col

    # Validate
    if not all([col_map["Short-Term Liabilities"], col_map["Long-Term Liabilities"], col_map["Owner's Equity"]]):
        st.error("❌ Essential columns not found. Ensure short/long liabilities and equity are present.")
    else:
        # Rename for analysis
        rename_map = {v: k for k, v in col_map.items() if v}
        df = df.rename(columns=rename_map)

        df = compute_ratios(df)
        st.subheader("📊 Financial Ratios Table")
        st.dataframe(df[["Fiscal Year", "Debt-to-Equity Ratio", "Equity Ratio", "Current Ratio", "ROE", "Net Profit Margin"]])

        # Trend Plots
        for col in ["Debt-to-Equity Ratio", "Equity Ratio", "Current Ratio", "ROE", "Net Profit Margin"]:
            if col in df.columns and df[col].notna().any():
                fig = px.line(df, x="Fiscal Year", y=col, markers=True, title=f"{col} Trend")
                st.plotly_chart(fig, use_container_width=True)

        # AI Commentary
        st.subheader("💬 Gemini Financial Analysis")
        with st.spinner("Generating insights..."):
            ai_text = ai_commentary(df)
            st.markdown(ai_text)
