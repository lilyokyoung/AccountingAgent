# Add this at the top
import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai
import difflib

# Page config
st.set_page_config(page_title="📊 Accounting Analyzer", layout="wide")

# 🎨 Background and color styling
st.markdown("""
<style>
body {background-color: #f2f6fc;}
.stApp {background-color: #f2f6fc;}
h1, h2, h3, h4 {color: #1a237e;}
.block-container {
    background-color: #ffffff;
    padding: 2rem 1rem;
    border-radius: 8px;
    box-shadow: 0 0 10px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)

# 🔐 Gemini API
genai.configure(api_key=st.secrets["gemini"]["api_key"])

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

# Utility functions
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

def plot_ratio_comparison(firm_val, benchmark, ratio_name):
    COLORS = {"green": "#4CAF50", "red": "#F44336", "yellow": "#FFC107"}
    if abs(firm_val - benchmark) <= 0.05 * benchmark:
        firm_color = benchmark_color = COLORS["yellow"]
    elif firm_val > benchmark:
        firm_color = COLORS["green"]
        benchmark_color = COLORS["red"]
    else:
        firm_color = COLORS["red"]
        benchmark_color = COLORS["green"]
    df_plot = pd.DataFrame({
        "Source": ["Your Firm", "Industry Benchmark"],
        ratio_name: [firm_val, benchmark]
    })
    fig = px.bar(df_plot, x="Source", y=ratio_name,
                 color="Source",
                 color_discrete_map={"Your Firm": firm_color, "Industry Benchmark": benchmark_color},
                 text_auto=True)
    fig.update_layout(title=f"{ratio_name} Comparison", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# 📂 Upload section
uploaded_file = st.file_uploader("📂 Upload Excel/CSV", type=["xlsx", "csv"])
if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file)
    df.rename(columns={df.columns[0]: "Fiscal Year"}, inplace=True)

    # Fuzzy column detection
    fields = {
        "Short-Term Liabilities": None, "Long-Term Liabilities": None,
        "Owner's Equity": None, "Current Assets": None,
        "Revenue": None, "Net Profit": None
    }
    for field in fields:
        match = fuzzy_match(field, df.columns)
        if match:
            df.rename(columns={match: field}, inplace=True)

    # Detect industry
    industry = detect_industry(uploaded_file.name)
    st.markdown(f"<h4 style='font-size:22px;'>🏢 <b>Detected Company:</b> {uploaded_file.name}</h4>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='font-size:22px;'>🏷️ <b>Industry:</b> {industry}</h4>", unsafe_allow_html=True)

    # Ratios
    if all(col in df.columns for col in ["Short-Term Liabilities", "Long-Term Liabilities", "Owner's Equity"]):
        df = compute_ratios(df)

        # 📄 Financial Statements
        st.header("📄 Balance Sheet and Income Statement Over Time")
        bs_cols = ["Fiscal Year", "Short-Term Liabilities", "Long-Term Liabilities", "Owner's Equity", "Current Assets"]
        is_cols = ["Fiscal Year", "Revenue", "Net Profit"]

        if all(col in df.columns for col in bs_cols[1:]):
            st.subheader("📘 Balance Sheet")
            st.dataframe(df[bs_cols])
            bs_melted = df[bs_cols].melt(id_vars="Fiscal Year", var_name="Account", value_name="Amount")
            st.plotly_chart(px.line(bs_melted, x="Fiscal Year", y="Amount", color="Account", markers=True), use_container_width=True)
            st.plotly_chart(px.bar(bs_melted, x="Fiscal Year", y="Amount", color="Account", barmode="group", text_auto=True), use_container_width=True)

        if all(col in df.columns for col in is_cols[1:]):
            st.subheader("📙 Income Statement")
            st.dataframe(df[is_cols])
            is_melted = df[is_cols].melt(id_vars="Fiscal Year", var_name="Metric", value_name="Amount")
            st.plotly_chart(px.bar(is_melted, x="Fiscal Year", y="Amount", color="Metric", barmode="group", text_auto=True), use_container_width=True)

        # 📋 Ratios
        ratio_cols = ["Debt-to-Equity Ratio", "Equity Ratio", "Current Ratio", "ROE", "Net Profit Margin"]
        st.subheader("📋 Ratio Trends")
        df_melted = df[["Fiscal Year"] + ratio_cols].melt(id_vars="Fiscal Year", var_name="Ratio", value_name="Value")
        st.plotly_chart(px.line(df_melted, x="Fiscal Year", y="Value", color="Ratio", markers=True), use_container_width=True)

        # 🧮 Benchmark
        if industry in INDUSTRY_BENCHMARKS:
            st.subheader(f"🧮 Benchmark Comparison – {industry}")
            for ratio in ratio_cols:
                if ratio in df.columns and ratio in INDUSTRY_BENCHMARKS[industry]:
                    plot_ratio_comparison(df.iloc[-1][ratio], INDUSTRY_BENCHMARKS[industry][ratio], ratio)

        # 💬 Gemini commentary
        st.subheader("💬 Gemini Commentary")
        with st.spinner("Generating insights..."):
            st.markdown(ai_commentary(df, industry))

        # 🤖 Gemini Q&A
        st.subheader("🤖 Ask a question about the data")
        user_input = st.text_input("Ask your question:")
        if user_input:
            context = df.to_string()
            q_prompt = f"{context}\n\nUser question: {user_input}"
            with st.spinner("Thinking..."):
                answer = genai.GenerativeModel("gemini-1.5-flash").generate_content(q_prompt)
                st.markdown(answer.text.strip())
