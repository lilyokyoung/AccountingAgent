import pandas as pd
import streamlit as st
import plotly.express as px
import os

# ---------- 🔍 Helper Functions ----------

def extract_company_name(df):
    for i in range(min(5, len(df))):
        for j in range(min(3, len(df.columns))):
            val = str(df.iloc[i, j]).strip().lower()
            if any(x in val for x in ["ltd", "limited", "inc", "corporation", "company", "fonterra", "bank", "air", "energy"]):
                return df.iloc[i, j].strip()
    return "Unknown"

def map_company_to_industry(company_name):
    company_industry_map = {
        "fonterra": "Dairy",
        "air new zealand": "Aviation",
        "anz": "Banking",
        "asb": "Banking",
        "z energy": "Energy",
        "fisher & paykel": "Healthcare",
        "kiwibank": "Banking",
        "mainfreight": "Logistics",
        "unknown": "Unknown"
    }
    name = company_name.lower()
    for key in company_industry_map:
        if key in name:
            return company_industry_map[key]
    return "Unknown"

industry_benchmarks = {
    "Dairy": {"Debt to Equity": 1.5, "Equity Ratio": 0.4},
    "Banking": {"Debt to Equity": 9.0, "Equity Ratio": 0.1},
    "Aviation": {"Debt to Equity": 3.5, "Equity Ratio": 0.25},
    "Healthcare": {"Debt to Equity": 0.8, "Equity Ratio": 0.55}
}

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

# ---------- 📊 Streamlit App ----------

st.set_page_config(page_title="📊 Industry Ratio Analyzer", layout="wide")
st.title("📁 Financial Statement Analyzer with Industry Comparison")

uploaded_file = st.file_uploader("Upload your Balance Sheet (Excel/CSV)", type=["csv", "xlsx"])

if uploaded_file:
    try:
        file_ext = os.path.splitext(uploaded_file.name)[-1]
        df = pd.read_excel(uploaded_file) if file_ext == ".xlsx" else pd.read_csv(uploaded_file)

        st.markdown("### 🧾 Raw Data Preview")
        st.dataframe(df.head())

        company_name = extract_company_name(df)
        industry = map_company_to_industry(company_name)

        st.markdown(f"**🏢 Detected Company:** `{company_name}`")
        st.markdown(f"**🏷️ Industry Classification:** `{industry}`")

        summary_df = extract_balance_sheet_summary(df)
        st.markdown("### 📉 Cleaned Balance Sheet Summary")
        st.dataframe(summary_df)

        numeric_cols = summary_df.columns.drop("Fiscal Year")
        for col in numeric_cols:
            fig = px.line(summary_df, x="Fiscal Year", y=col, markers=True, title=f"{col} Over Time")
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 📈 Financial Ratios Over Time")
        ratios = []
        for _, row in summary_df.iterrows():
            total_liab = row["Short-Term Liabilities"] + row["Long-Term Liabilities"]
            equity = row["Total Owner's Equity"]
            year = row["Fiscal Year"]
            debt_equity = round(total_liab / equity, 2) if equity else None
            equity_ratio = round(equity / (total_liab + equity), 2) if (total_liab + equity) else None
            ratios.append({
                "Fiscal Year": year,
                "Debt to Equity": debt_equity,
                "Equity Ratio": equity_ratio
            })

        ratio_df = pd.DataFrame(ratios)
        st.dataframe(ratio_df)

        fig1 = px.line(ratio_df, x="Fiscal Year", y="Debt to Equity", markers=True, title="Debt to Equity Ratio Over Time")
        fig2 = px.line(ratio_df, x="Fiscal Year", y="Equity Ratio", markers=True, title="Equity Ratio Over Time")
        st.plotly_chart(fig1, use_container_width=True)
        st.plotly_chart(fig2, use_container_width=True)

        if industry in industry_benchmarks:
            st.markdown(f"### 🧮 Industry Benchmark Comparison for `{industry}`")
            bench = industry_benchmarks[industry]
            latest = ratio_df.iloc[-1]
            for metric in ["Debt to Equity", "Equity Ratio"]:
                val = latest[metric]
                delta = round(val - bench[metric], 2)
                st.metric(label=metric, value=val, delta=delta)
        else:
            st.warning("⚠️ Industry benchmark not available for this classification.")

    except Exception as e:
        st.error(f"❌ Error: {e}")
else:
    st.info("📤 Upload a balance sheet file to begin.")
