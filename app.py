import pandas as pd
import streamlit as st
import plotly.express as px
import os

# ---------- 🏢 Detect company from filename ----------

def extract_company_name_from_filename(uploaded_file):
    filename = uploaded_file.name.lower()
    company_keywords = ["fonterra", "airnz", "anz", "asb", "fisher", "zenergy", "mainfreight", "kiwibank"]
    for keyword in company_keywords:
        if keyword in filename:
            return keyword.capitalize()
    return "Unknown"

def map_company_to_industry(company_name):
    company_industry_map = {
        "Fonterra": "Dairy",
        "Airnz": "Aviation",
        "Anz": "Banking",
        "Asb": "Banking",
        "Zenergy": "Energy",
        "Fisher": "Healthcare",
        "Mainfreight": "Logistics",
        "Kiwibank": "Banking"
    }
    return company_industry_map.get(company_name, "Unknown")

industry_benchmarks = {
    "Dairy": {"Debt to Equity": 1.5, "Equity Ratio": 0.4},
    "Banking": {"Debt to Equity": 9.0, "Equity Ratio": 0.1},
    "Aviation": {"Debt to Equity": 3.5, "Equity Ratio": 0.25},
    "Healthcare": {"Debt to Equity": 0.8, "Equity Ratio": 0.55},
    "Logistics": {"Debt to Equity": 2.0, "Equity Ratio": 0.3},
    "Energy": {"Debt to Equity": 1.8, "Equity Ratio": 0.35}
}

# ---------- 🧽 Clean balance sheet ----------

def extract_balance_sheet_summary(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.astype(str).str.strip().str.lower()
    if "fiscal year" not in df.columns:
        raise ValueError("Missing 'Fiscal Year' column.")

    def safe_float(x):
        try:
            return float(str(x).replace(",", "").strip())
        except:
            return 0.0

    cleaned = pd.DataFrame()
    cleaned["Fiscal Year"] = df["fiscal year"]

    def match_column(possible_names):
        for name in possible_names:
            for col in df.columns:
                if name in col:
                    return df[col].apply(safe_float)
        return pd.Series([0.0] * len(df))

    cleaned["Short-Term Liabilities"] = match_column(["current liabilities", "short-term liabilities"])
    cleaned["Long-Term Liabilities"] = match_column(["non-current liabilities", "long-term liabilities"])
    cleaned["Retained Earnings"] = match_column(["retained earnings", "accumulated"])
    cleaned["Total Owner's Equity"] = match_column(["total equity", "net worth"])
    cleaned["Owner's Investment"] = cleaned["Total Owner's Equity"] - cleaned["Retained Earnings"]
    cleaned["Total Liabilities & Equity"] = (
        cleaned["Short-Term Liabilities"] + cleaned["Long-Term Liabilities"] + cleaned["Total Owner's Equity"]
    )

    return cleaned

# ---------- 🚀 Streamlit App ----------

st.set_page_config(page_title="📊 Industry Ratio Analyzer", layout="wide")
st.title("📁 Financial Statement Analyzer with Industry Benchmarking")

uploaded_file = st.file_uploader("Upload your Balance Sheet (Excel/CSV)", type=["csv", "xlsx"])

if uploaded_file:
    try:
        file_ext = os.path.splitext(uploaded_file.name)[-1]
        df = pd.read_excel(uploaded_file) if file_ext == ".xlsx" else pd.read_csv(uploaded_file)

        st.markdown("### 🧾 Raw Data Preview")
        st.dataframe(df.head())

        # 🏢 Detect company & industry
        company_name = extract_company_name_from_filename(uploaded_file)
        industry = map_company_to_industry(company_name)

        # 🔁 Fallback
        if company_name == "Unknown":
            company_name = st.text_input("🏢 Enter Company Name:")
        if industry == "Unknown":
            industry = st.selectbox("🏷️ Select Industry:", list(industry_benchmarks.keys()))

        st.markdown(f"**🏢 Company:** `{company_name}`")
        st.markdown(f"**🏷️ Industry:** `{industry}`")

        # 🧼 Clean balance sheet
        summary_df = extract_balance_sheet_summary(df)
        st.markdown("### 📊 Cleaned Balance Sheet Summary")
        st.dataframe(summary_df)

        for col in summary_df.columns.drop("Fiscal Year"):
            fig = px.line(summary_df, x="Fiscal Year", y=col, markers=True, title=f"{col} Over Time")
            st.plotly_chart(fig, use_container_width=True)

        # 📌 Financial Ratios
        st.markdown("### 📈 Financial Ratios Over Time")
        ratios = []
        for _, row in summary_df.iterrows():
            total_liab = row["Short-Term Liabilities"] + row["Long-Term Liabilities"]
            equity = row["Total Owner's Equity"]
            year = row["Fiscal Year"]

            # Handle division by zero or missing data
            debt_equity = round(total_liab / equity, 2) if equity and equity != 0 else float("nan")
            equity_ratio = round(equity / (total_liab + equity), 2) if (total_liab + equity) != 0 else float("nan")

            ratios.append({
                "Fiscal Year": year,
                "Debt to Equity": debt_equity,
                "Equity Ratio": equity_ratio
            })

        ratio_df = pd.DataFrame(ratios)
        st.dataframe(ratio_df)

        fig1 = px.line(ratio_df, x="Fiscal Year", y="Debt to Equity", markers=True, title="Debt to Equity Over Time")
        fig2 = px.line(ratio_df, x="Fiscal Year", y="Equity Ratio", markers=True, title="Equity Ratio Over Time")
        st.plotly_chart(fig1, use_container_width=True)
        st.plotly_chart(fig2, use_container_width=True)

        # 🔍 Debug: Show last year values
        st.markdown("### 🔍 Last Year Input Values")
        st.write(summary_df.iloc[-1])

        # 🧮 Industry Comparison
        if industry in industry_benchmarks:
            st.markdown(f"### 🧮 Industry Benchmark Comparison for `{industry}`")
            bench = industry_benchmarks[industry]
            latest = ratio_df.iloc[-1]
            for metric in ["Debt to Equity", "Equity Ratio"]:
                val = latest[metric]
                delta = round(val - bench[metric], 2) if pd.notna(val) else "N/A"
                st.metric(label=metric, value=val, delta=delta)
        else:
            st.warning("⚠️ No benchmarks for this industry.")

    except Exception as e:
        st.error(f"❌ Error: {e}")
else:
    st.info("📤 Upload a balance sheet file to begin.")
