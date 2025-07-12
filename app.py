import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import difflib

# 🔐 API config
genai.configure(api_key=st.secrets["gemini"]["api_key"])
st.set_page_config(page_title="📊 Accounting Analyzer", layout="wide")
st.title("📈 Financial Statement Analyzer with Industry Comparison & AI Insights")

# 📘 Benchmarks
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

# 🧠 Fuzzy match helper
def fuzzy_match(target, columns, cutoff=0.6):
    match = difflib.get_close_matches(target, columns, n=1, cutoff=cutoff)
    return match[0] if match else None

def detect_industry(file_name):
    name = file_name.lower()
    if "fonterra" in name or "milk" in name or "dairy" in name:
        return "Dairy"
    elif "tech" in name or "software" in name:
        return "Tech"
    return "Unknown"

def compute_ratios(df):
    numeric_cols = [
        "Short-Term Liabilities", "Long-Term Liabilities", "Owner's Equity",
        "Current Assets", "Net Profit", "Revenue"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Total Liabilities"] = df["Short-Term Liabilities"] + df["Long-Term Liabilities"]
    df["Debt-to-Equity Ratio"] = df["Total Liabilities"] / df["Owner's Equity"]
    df["Equity Ratio"] = df["Owner's Equity"] / (df["Total Liabilities"] + df["Owner's Equity"])
    df["Current Ratio"] = df["Current Assets"] / df["Short-Term Liabilities"] if "Current Assets" in df.columns else None
    df["ROE"] = df["Net Profit"] / df["Owner's Equity"] if "Net Profit" in df.columns else None
    df["Net Profit Margin"] = df["Net Profit"] / df["Revenue"] if "Revenue" in df.columns and "Net Profit" in df.columns else None
    return df

def ai_commentary(df, industry):
    latest = df.iloc[-1]
    prompt = f"""You are a financial analyst. The company belongs to the `{industry}` industry.
Latest financial ratios:
- Debt-to-Equity: {latest.get('Debt-to-Equity Ratio', 'N/A')}
- Equity Ratio: {latest.get('Equity Ratio', 'N/A')}
- Current Ratio: {latest.get('Current Ratio', 'N/A')}
- ROE: {latest.get('ROE', 'N/A')}
- Net Profit Margin: {latest.get('Net Profit Margin', 'N/A')}
Compare them to industry averages and offer brief recommendations."""
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

def plot_ratio_comparison(firm_value, benchmark, ratio_name):
    df_plot = pd.DataFrame({
        "Source": ["Your Firm", "Industry Benchmark"],
        ratio_name: [firm_value, benchmark]
    })
    fig = px.bar(df_plot, x="Source", y=ratio_name, color="Source",
                 text_auto=True, title=f"{ratio_name} Comparison")
    st.plotly_chart(fig, use_container_width=True)

# 📂 Upload
uploaded_file = st.file_uploader("📂 Upload Excel/CSV", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file)
    df.rename(columns={df.columns[0]: "Fiscal Year"}, inplace=True)

    st.write("📑 Columns:", df.columns.tolist())
    st.dataframe(df.head())

    industry = detect_industry(uploaded_file.name)
    st.markdown(f"🏢 **Detected Company:** `{uploaded_file.name.replace('.xlsx', '').replace('.csv', '')}`")
    st.markdown(f"🏷️ **Industry:** `{industry}`")

    # 🎯 Fuzzy matching expected fields
    expected_fields = {
        "Short-Term Liabilities": "Short-Term Liabilities",
        "Long-Term Liabilities": "Long-Term Liabilities",
        "Owner's Equity": "Owner's Equity",
        "Current Assets": "Current Assets",
        "Net Profit": "Net Profit",
        "Revenue": "Revenue"
    }

    col_map = {}
    for key, expected in expected_fields.items():
        match = fuzzy_match(expected, df.columns)
        col_map[key] = match

    with st.expander("🛠 Manually confirm or correct column mapping"):
        for key in col_map:
            current_val = col_map[key] if col_map[key] in df.columns else None
            col_map[key] = st.selectbox(
                f"{key}",
                [None] + list(df.columns),
                index=([None] + list(df.columns)).index(current_val) if current_val else 0
            )

    essential_cols = ["Short-Term Liabilities", "Long-Term Liabilities", "Owner's Equity"]
    if not all(col_map[c] for c in essential_cols):
        st.error("❌ Missing essential columns: STL, LTL, or Equity.")
    else:
        df = df.rename(columns={v: k for k, v in col_map.items() if v})
        df = compute_ratios(df)

        st.subheader("📋 Ratio Table (All Years)")
        st.dataframe(df[["Fiscal Year", "Debt-to-Equity Ratio", "Equity Ratio", "Current Ratio", "ROE", "Net Profit Margin"]])

        st.subheader("📈 Ratio Trends")
        for ratio in ["Debt-to-Equity Ratio", "Equity Ratio", "Current Ratio", "ROE", "Net Profit Margin"]:
            if ratio in df.columns and df[ratio].notna().any():
                fig = px.line(df, x="Fiscal Year", y=ratio, markers=True, title=ratio)
                st.plotly_chart(fig, use_container_width=True)

        if industry in INDUSTRY_BENCHMARKS:
            st.subheader(f"🧮 Benchmark Comparison – {industry}")
            latest = df.iloc[-1]
            for ratio, benchmark in INDUSTRY_BENCHMARKS[industry].items():
                firm_val = latest.get(ratio)
                result = compare_to_benchmark(firm_val, benchmark)
                if pd.notna(firm_val):
                    st.markdown(f"**{ratio}**: {firm_val:.2f} vs {benchmark:.2f} → {result}")
                    plot_ratio_comparison(firm_val, benchmark, ratio)
                else:
                    st.markdown(f"**{ratio}**: N/A vs {benchmark:.2f} → {result}")
        else:
            st.warning("⚠️ No industry benchmarks available.")

        st.subheader("💬 Gemini Commentary")
        with st.spinner("Generating insights..."):
            st.markdown(ai_commentary(df, industry))
