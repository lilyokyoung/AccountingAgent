import streamlit as st
import pandas as pd
import os

# 🔧 Flexible column matching
def get_value_fuzzy(row, keywords):
    for keyword in keywords:
        keyword = keyword.lower().replace("-", " ").strip()
        for col in row.index:
            col_norm = str(col).lower().replace("-", " ").replace("_", " ").strip()
            if keyword in col_norm:
                try:
                    return float(str(row[col]).replace(",", ""))
                except:
                    continue
    return None

# 🚀 Streamlit App
st.set_page_config(page_title="Balance Sheet Analyzer", layout="wide")
st.title("💡 Cleaned Balance Sheet Summary")

uploaded_file = st.file_uploader("📤 Upload your Balance Sheet Excel or CSV", type=["xlsx", "xls", "csv"])

if uploaded_file:
    company_name = os.path.splitext(uploaded_file.name)[0]
    st.markdown(f"🏢 **Detected Company:** `{company_name}`")

    try:
        if uploaded_file.name.endswith(".csv"):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file)

        # Detect if transposition needed
        if "Fiscal Year" in df_raw.iloc[:, 0].values:
            df_raw.columns = df_raw.iloc[:, 0]
            df = df_raw.iloc[:, 1:].T
            df.columns.name = None
            df = df.reset_index(drop=True)
        else:
            df = df_raw.copy()

        row = df.iloc[0]

        short_term_liab = get_value_fuzzy(row, ["short term liabilities", "current liabilities"])
        long_term_liab = get_value_fuzzy(row, ["long term liabilities", "non current liabilities"])
        retained_earnings = get_value_fuzzy(row, ["retained earnings"])
        total_equity = get_value_fuzzy(row, ["total equity", "owner's equity", "net worth"])
        investment = get_value_fuzzy(row, ["owner's investment"])

        if total_equity is not None and retained_earnings is not None:
            investment = total_equity - retained_earnings
        if retained_earnings is None:
            retained_earnings = 0.0
        if investment is None:
            investment = 0.0
        if total_equity is None:
            total_equity = investment + retained_earnings

        total_liab_equity = sum(filter(None, [short_term_liab, long_term_liab])) + total_equity

        summary = pd.DataFrame({
            "Category": [
                "Short-Term Liabilities",
                "Long-Term Liabilities",
                "Owner's Investment",
                "Retained Earnings",
                "Total Owner's Equity",
                "Total Liabilities & Equity"
            ],
            "Amount": [
                short_term_liab or 0.0,
                long_term_liab or 0.0,
                investment or 0.0,
                retained_earnings or 0.0,
                total_equity or 0.0,
                total_liab_equity or 0.0
            ]
        })

        st.dataframe(summary)

        if summary["Amount"].sum() == 0:
            st.warning("⚠️ All values extracted are zero. Please check your file format and column labels.")

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")

else:
    st.info("📂 Please upload a balance sheet file.")
