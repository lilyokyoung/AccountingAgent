import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="📊 Accounting Analyzer", layout="wide")
st.title("🧾 Cleaned Balance Sheet Summary")

uploaded_file = st.file_uploader("Upload Balance Sheet Excel File", type=["xlsx", "xls"])

def detect_company_and_industry(filename):
    if filename:
        name = os.path.basename(filename).split('.')[0]
        company = name.replace("_", " ")
        if "fonterra" in name.lower():
            return company, "Dairy"
        elif "airnz" in name.lower():
            return company, "Airlines"
        elif "zenergy" in name.lower():
            return company, "Energy"
        else:
            return company, "Unknown"
    return "Unknown", "Unknown"

def match_column(df, options):
    for opt in options:
        for col in df.columns:
            if str(opt).lower().strip() in str(col).lower().strip():
                return col
    return None

def extract_clean_balance_sheet(df):
    if df.empty:
        return pd.DataFrame(), []

    df.columns = df.iloc[0]
    df = df.drop(0).reset_index(drop=True)

    latest = df.iloc[-1]
    notes = []

    short_term_col = match_column(df, ["short term liabilities", "current liabilities"])
    long_term_col = match_column(df, ["long term liabilities", "non current liabilities"])
    equity_col = match_column(df, ["total equity", "net worth", "owner's equity"])
    retained_col = match_column(df, ["retained earnings", "accumulated profits"])

    def safe_float(val):
        try:
            return float(str(val).replace(",", "").strip())
        except:
            return 0.0

    short_term = safe_float(latest[short_term_col]) if short_term_col else 0.0
    if not short_term_col: notes.append("❌ No match found for 'short term liabilities'")
    long_term = safe_float(latest[long_term_col]) if long_term_col else 0.0
    if not long_term_col: notes.append("❌ No match found for 'long term liabilities'")
    retained = safe_float(latest[retained_col]) if retained_col else 0.0
    if not retained_col: notes.append("❌ No match found for 'retained earnings'")
    equity = safe_float(latest[equity_col]) if equity_col else 0.0
    if not equity_col: notes.append("❌ No match found for 'total equity'")

    investment = max(equity - retained, 0.0)
    total_equity = investment + retained
    total_liabilities_equity = short_term + long_term + total_equity

    result_df = pd.DataFrame({
        "Category": [
            "Short-Term Liabilities",
            "Long-Term Liabilities",
            "Owner's Investment",
            "Retained Earnings",
            "Total Owner's Equity",
            "Total Liabilities & Equity"
        ],
        "Amount": [short_term, long_term, investment, retained, total_equity, total_liabilities_equity]
    })

    return result_df, notes

industry_benchmarks = {
    "Dairy": {"DebtToEquity": 1.2, "EquityRatio": 0.45},
    "Airlines": {"DebtToEquity": 2.5, "EquityRatio": 0.2},
    "Energy": {"DebtToEquity": 1.0, "EquityRatio": 0.5},
}

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    company_name, industry = detect_company_and_industry(uploaded_file.name)
    result_df, extract_notes = extract_clean_balance_sheet(df)

    st.dataframe(result_df, use_container_width=True)

    if extract_notes:
        for note in extract_notes:
            st.warning(note)

    st.subheader("🏢 Detected Company: " + company_name)
    st.markdown(f"🏷️ **Industry Classification:** {industry}")

    st.subheader(f"📊 Industry Benchmark Comparison for `{industry}`")
    if industry in industry_benchmarks:
        debt = result_df[result_df["Category"] == "Short-Term Liabilities"]["Amount"].values[0] + \
               result_df[result_df["Category"] == "Long-Term Liabilities"]["Amount"].values[0]
        equity = result_df[result_df["Category"] == "Total Owner's Equity"]["Amount"].values[0]

        if equity > 0:
            debt_to_equity = round(debt / equity, 2)
            equity_ratio = round(equity / (debt + equity), 2)
        else:
            debt_to_equity = None
            equity_ratio = None

        industry_data = industry_benchmarks[industry]
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Debt to Equity", f"{debt_to_equity if debt_to_equity is not None else 'N/A'}")
            st.caption(f"📊 Industry Avg: {industry_data['DebtToEquity']}")
        with col2:
            st.metric("Equity Ratio", f"{equity_ratio if equity_ratio is not None else 'N/A'}")
            st.caption(f"📊 Industry Avg: {industry_data['EquityRatio']}")

    st.subheader("📈 Year-over-Year Trend (if available)")
    if "Fiscal Year" in df.columns:
        trend_df = df[["Fiscal Year"] + [c for c in df.columns if "liabilities" in str(c).lower() or "equity" in str(c).lower()]]
        trend_df = trend_df.dropna()
        fig = px.line(trend_df, x="Fiscal Year", y=trend_df.columns[1:], markers=True, title="Financial Components Over Time")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No 'Fiscal Year' column found for trend analysis.")
else:
    st.info("Please upload an Excel file to begin analysis.")
