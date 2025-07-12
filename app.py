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
    df["Net Profit Margin"] = df["Net Profit"] / df["Revenue"] if "Net Profit" in df.columns and "Revenue" in df.columns else None
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
    if pd.isna(firm_value) or pd.isna(benchmark):
        return

    # Vibrant colors
    COLORS = {
        "green": "#2ECC40",   # bright green
        "red": "#FF4136",     # vivid red
        "yellow": "#FFDC00"   # bold yellow
    }

    if abs(firm_value - benchmark) <= 0.05 * benchmark:
        firm_color = COLORS["yellow"]
        benchmark_color = COLORS["yellow"]
    elif firm_value > benchmark:
        firm_color = COLORS["green"]
        benchmark_color = COLORS["red"]
    else:
        firm_color = COLORS["red"]
        benchmark_color = COLORS["green"]

    df_plot = pd.DataFrame({
        "Label": [f"{ratio_name}"],
        "Your Firm": [firm_value],
        "Industry Benchmark": [benchmark]
    })
    df_melted = df_plot.melt(id_vars="Label", var_name="Source", value_name="Value")

    fig = px.bar(
        df_melted,
        x="Source",
        y="Value",
        color="Source",
        color_discrete_map={
            "Your Firm": firm_color,
            "Industry Benchmark": benchmark_color
        },
        text_auto=True,
        title=f"{ratio_name} vs Industry Benchmark"
    )
    fig.update_layout(showlegend=False)
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

    expected_fields = {
        "Short-Term Liabilities": "Short-Term Liabilities",
        "Long-Term Liabilities": "Long-Term Liabilities",
        "Owner's Equity": "Owner's Equity",
        "Current Assets": "Current Assets",
        "Net Profit": "Net Profit",
        "Revenue": "Revenue"
    }

    for key, expected in expected_fields.items():
        match = fuzzy_match(expected, df.columns)
        if match:
            df = df.rename(columns={match: key})

    missing_cols = [k for k in ["Current Assets", "Net Profit", "Revenue"] if k not in df.columns]
    if missing_cols:
        st.warning(f"⚠️ Missing columns for full analysis: {', '.join(missing_cols)}")

    essential_cols = ["Short-Term Liabilities", "Long-Term Liabilities", "Owner's Equity"]
    if not all(col in df.columns for col in essential_cols):
        st.error("❌ Essential columns missing: STL, LTL, or Equity.")
    else:
        df = compute_ratios(df)

        st.subheader("📋 Ratio Table (All Years)")
        st.dataframe(df[["Fiscal Year", "Debt-to-Equity Ratio", "Equity Ratio", "Current Ratio", "ROE", "Net Profit Margin"]])

        st.subheader("📈 All Ratio Trends Over Time")
        ratio_cols = ["Debt-to-Equity Ratio", "Equity Ratio", "Current Ratio", "ROE", "Net Profit Margin"]
        available = [r for r in ratio_cols if r in df.columns and df[r].notna().any()]
        if available:
            df_melted = df[["Fiscal Year"] + available].melt(id_vars="Fiscal Year", var_name="Ratio", value_name="Value")
            fig = px.line(df_melted, x="Fiscal Year", y="Value", color="Ratio", markers=True, title="Financial Ratios Over Time")
            fig.update_layout(legend_title_text="Ratio")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No ratios available to plot.")

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

        # 📊 BALANCE SHEET & INCOME STATEMENT TABLES + GRAPHS
        st.header("📄 Balance Sheet and Income Statement Over Time")

        bs_fields = ["Fiscal Year", "Short-Term Liabilities", "Long-Term Liabilities", "Owner's Equity", "Current Assets"]
        is_fields = ["Fiscal Year", "Revenue", "Net Profit"]

        if all(col in df.columns for col in bs_fields[1:]):
            st.subheader("📘 Balance Sheet")
            st.dataframe(df[bs_fields])

            bs_melted = df[bs_fields].melt(id_vars="Fiscal Year", var_name="Account", value_name="Amount")
            fig_bs = px.line(bs_melted, x="Fiscal Year", y="Amount", color="Account", markers=True, title="Balance Sheet Components Over Time")
            fig_bs.update_layout(legend_title_text="Account")
            st.plotly_chart(fig_bs, use_container_width=True)
        else:
            st.warning("⚠️ Missing data to display full Balance Sheet.")

        if all(col in df.columns for col in is_fields[1:]):
            st.subheader("📙 Income Statement")
            st.dataframe(df[is_fields])

            is_melted = df[is_fields].melt(id_vars="Fiscal Year", var_name="Metric", value_name="Amount")
            fig_is = px.bar(is_melted, x="Fiscal Year", y="Amount", color="Metric", barmode="group", text_auto=True,
                            title="Income Statement Components Over Time")
            fig_is.update_layout(legend_title_text="Metric")
            st.plotly_chart(fig_is, use_container_width=True)
        else:
            st.warning("⚠️ Missing data to display full Income Statement.")
