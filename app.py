import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# 🔐 Secrets
genai.configure(api_key=st.secrets["gemini"]["api_key"])

st.set_page_config(page_title="📊 Accounting Ratio Analyzer", layout="wide")
st.title("📈 Financial Statement Analyzer with Industry Benchmarking + Gemini")

# Hardcoded industry benchmarks
INDUSTRY_BENCHMARKS = {
    "Dairy": {
        "Debt-to-Equity Ratio": 1.20,
        "Equity Ratio": 0.45,
        "Current Ratio": 1.80,
        "ROE": 0.12,
        "Net Profit Margin": 0.08
    },
    "Tech": {
        "Debt-to-Equity Ratio": 0.50,
        "Equity Ratio": 0.70,
        "Current Ratio": 2.50,
        "ROE": 0.15,
        "Net Profit Margin": 0.20
    }
}

def detect_industry(file_name):
    name = file_name.lower()
    if "fonterra" in name or "milk" in name or "dairy" in name:
        return "Dairy"
    elif "tech" in name or "software" in name:
        return "Tech"
    return "Unknown"

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

def ai_commentary(df, industry):
    latest = df.iloc[-1]
    ratios = {
        "Debt-to-Equity": latest["Debt-to-Equity Ratio"],
        "Equity Ratio": latest["Equity Ratio"],
        "Current Ratio": latest.get("Current Ratio", "N/A"),
        "ROE": latest.get("ROE", "N/A"),
        "Net Profit Margin": latest.get("Net Profit Margin", "N/A")
    }
    prompt = f"""You are a financial analyst. The company belongs to the `{industry}` industry.
Here are its latest financial ratios:

{ratios}

Compare with the industry benchmarks and provide a concise professional assessment. Highlight strong or weak areas, and suggest improvements."""
    response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
    return response.text.strip()

def compare_to_benchmark(value, benchmark):
    if pd.isna(value):
        return "N/A"
    elif abs(value - benchmark) <= 0.05 * benchmark:
        return "🟡 On Par"
    elif value > benchmark:
        return "🟢 Above"
    else:
        return "🔴 Below"

# Upload and processing
uploaded_file = st.file_uploader("📂 Upload Balance Sheet Excel", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file)
    df.rename(columns={df.columns[0]: "Fiscal Year"}, inplace=True)

    # Detect industry
    industry = detect_industry(uploaded_file.name)
    st.markdown(f"🏢 **Detected Company:** `{uploaded_file.name.replace('.xlsx', '').replace('.csv', '')}`")
    st.markdown(f"🏷️ **Industry Classification:** `{industry}`")

    # Column matching
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

    essential_cols = ["Short-Term Liabilities", "Long-Term Liabilities", "Owner's Equity"]
    if not all([col_map[c] for c in essential_cols]):
        st.error("❌ Required columns missing (STL, LTL, Equity).")
    else:
        rename_map = {v: k for k, v in col_map.items() if v}
        df = df.rename(columns=rename_map)
        df = compute_ratios(df)

        st.subheader("📋 Financial Ratios (Latest Year)")
        latest = df.iloc[-1]
        st.write(latest[["Fiscal Year", "Debt-to-Equity Ratio", "Equity Ratio", "Current Ratio", "ROE", "Net Profit Margin"]])

        # 📊 Show all ratio trends
        st.subheader("📈 Ratio Trend Charts")
        for col in ["Debt-to-Equity Ratio", "Equity Ratio", "Current Ratio", "ROE", "Net Profit Margin"]:
            if col in df.columns and df[col].notna().any():
                fig = px.line(df, x="Fiscal Year", y=col, markers=True, title=f"{col} Trend")
                st.plotly_chart(fig, use_container_width=True)

        # 🧮 Benchmark comparison
        if industry in INDUSTRY_BENCHMARKS:
            st.subheader(f"🧮 Industry Benchmark Comparison for {industry}")
            benchmarks = INDUSTRY_BENCHMARKS[industry]
            for k, bench_val in benchmarks.items():
                actual_val = latest.get(k)
                result = compare_to_benchmark(actual_val, bench_val)
                st.markdown(f"**{k}**: {actual_val:.2f} vs Benchmark {bench_val:.2f} → {result}")
        else:
            st.warning("⚠️ No benchmark data available for this industry.")

        # 💬 Gemini AI Commentary
        st.subheader("💬 Gemini AI Commentary")
        with st.spinner("Analyzing ratios..."):
            st.markdown(ai_commentary(df, industry))
