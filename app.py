import streamlit as st
import pandas as pd
import os

# ----------------------------
# Helper Functions
# ----------------------------

def detect_company_and_industry(filename):
    name = os.path.basename(filename).lower()
    if "fonterra" in name:
        return "Fonterra", "Dairy"
    elif "airnz" in name or "air new zealand" in name:
        return "Air New Zealand", "Airlines"
    elif "fisher" in name and "paykel" in name:
        return "Fisher & Paykel", "Healthcare"
    else:
        return "Unknown", "Unknown"

def parse_balance_sheet(df):
    df.columns = df.iloc[0]
    df = df.drop(0).reset_index(drop=True)

    latest = df.iloc[0]

    def get_val(possible_names):
        for col in df.columns:
            for name in possible_names:
                if str(col).strip().lower().startswith(name.lower()):
                    try:
                        return float(str(latest[col]).replace(",", ""))
                    except:
                        return None
        return None

    short_liab = get_val(["short-term liabilities", "short term liabilities", "current liabilities"])
    long_liab = get_val(["long-term liabilities", "long term liabilities", "non-current liabilities"])
    equity = get_val(["total equity", "net worth"])
    retained = get_val(["retained earnings", "accumulated profits"])

    if equity is None: equity = 0.0
    if retained is None: retained = 0.0

    investment = equity - retained
    total_equity = investment + retained
    total_liab_equity = (short_liab or 0) + (long_liab or 0) + total_equity

    return {
        "Short-Term Liabilities": short_liab or 0,
        "Long-Term Liabilities": long_liab or 0,
        "Owner's Investment": investment or 0,
        "Retained Earnings": retained or 0,
        "Total Owner's Equity": total_equity or 0,
        "Total Liabilities & Equity": total_liab_equity or 0
    }

def get_industry_benchmarks(industry):
    if industry == "Dairy":
        return {"Debt to Equity": 1.2, "Equity Ratio": 0.45}
    elif industry == "Airlines":
        return {"Debt to Equity": 2.0, "Equity Ratio": 0.30}
    elif industry == "Healthcare":
        return {"Debt to Equity": 0.8, "Equity Ratio": 0.55}
    else:
        return {"Debt to Equity": None, "Equity Ratio": None}

def compute_ratios(balance_data):
    debt = balance_data["Short-Term Liabilities"] + balance_data["Long-Term Liabilities"]
    equity = balance_data["Total Owner's Equity"]
    debt_to_equity = debt / equity if equity else None
    equity_ratio = equity / balance_data["Total Liabilities & Equity"] if balance_data["Total Liabilities & Equity"] else None
    return {"Debt to Equity": debt_to_equity, "Equity Ratio": equity_ratio}

# ----------------------------
# Streamlit UI
# ----------------------------

st.set_page_config(page_title="📊 Balance Sheet Analyzer", layout="wide")
st.title("📄 Balance Sheet Analyzer with Industry Benchmarking")

uploaded_file = st.file_uploader("Upload a Balance Sheet Excel or CSV", type=["xlsx", "xls", "csv"])

if uploaded_file:
    filename = uploaded_file.name
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.subheader("📊 Raw Preview of Uploaded File")
        st.dataframe(df)

        # Identify company
        company_name, industry = detect_company_and_industry(filename)
        st.markdown(f"🏢 **Detected Company:** `{company_name}`")
        st.markdown(f"🏷️ **Industry Classification:** `{industry}`")

        # Parse balance sheet
        balance_summary = parse_balance_sheet(df)
        st.subheader("📘 Cleaned Balance Sheet Summary")
        st.table(pd.DataFrame(balance_summary.items(), columns=["Category", "Amount"]))

        # Compute Ratios
        ratios = compute_ratios(balance_summary)
        benchmarks = get_industry_benchmarks(industry)

        st.subheader(f"📊 Industry Benchmark Comparison for `{industry}`")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Debt to Equity", f"{ratios['Debt to Equity']:.2f}" if ratios['Debt to Equity'] else "N/A", 
                      help="Total Liabilities divided by Total Equity")
            st.caption(f"📊 Industry Avg: {benchmarks['Debt to Equity'] if benchmarks['Debt to Equity'] else 'N/A'}")

        with col2:
            st.metric("Equity Ratio", f"{ratios['Equity Ratio']:.2f}" if ratios['Equity Ratio'] else "N/A",
                      help="Total Equity divided by Total Liabilities + Equity")
            st.caption(f"📊 Industry Avg: {benchmarks['Equity Ratio'] if benchmarks['Equity Ratio'] else 'N/A'}")

    except Exception as e:
        st.error(f"❌ Failed to read file: {e}")
else:
    st.info("📥 Please upload a balance sheet file to begin analysis.")
