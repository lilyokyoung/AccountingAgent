import streamlit as st
import pandas as pd
import os
import re
from difflib import get_close_matches

st.set_page_config(page_title="📊 Financial Statement Analyzer", layout="wide")
st.title("📊 Cleaned Balance Sheet Summary")

# --- Helper Functions ---

def normalize(text):
    return re.sub(r'[^a-z0-9]', '', str(text).lower().strip())

def match_column(possible_names, df_columns):
    norm_cols = {normalize(col): col for col in df_columns}
    for name in possible_names:
        norm_name = normalize(name)
        close = get_close_matches(norm_name, norm_cols.keys(), n=1, cutoff=0.7)
        if close:
            return norm_cols[close[0]]
    return None

def extract_clean_balance_sheet(df):
    if df.columns[0] != 'Year':
        df.columns = df.iloc[0]
        df = df.drop(index=0).reset_index(drop=True)

    latest = df.iloc[-1]
    columns = df.columns

    short_liab_col = match_column(["short term liabilities", "current liabilities", "total current liabilities"], columns)
    long_liab_col = match_column(["long term liabilities", "non current liabilities", "total non-current liabilities"], columns)
    equity_col = match_column(["total equity", "owner's equity", "shareholders funds", "net worth"], columns)
    retained_col = match_column(["retained earnings", "retained profits", "accumulated profits"], columns)

    # Show warnings for unmatched
    for label, col in {
        "Short-Term Liabilities": short_liab_col,
        "Long-Term Liabilities": long_liab_col,
        "Owner's Equity": equity_col,
        "Retained Earnings": retained_col
    }.items():
        if col is None:
            st.warning(f"❌ No match found for **{label}**")

    def get_val(col):
        try:
            return float(str(latest[col]).replace(",", "")) if col else 0.0
        except:
            return 0.0

    short_term_liab = get_val(short_liab_col)
    long_term_liab = get_val(long_liab_col)
    equity = get_val(equity_col)
    retained = get_val(retained_col)

    investment = equity - retained if equity and retained else equity
    total_equity = investment + retained
    total_liab_equity = short_term_liab + long_term_liab + total_equity

    return pd.DataFrame({
        "Category": [
            "Short-Term Liabilities",
            "Long-Term Liabilities",
            "Owner's Investment",
            "Retained Earnings",
            "Total Owner's Equity",
            "Total Liabilities & Equity"
        ],
        "Amount": [
            short_term_liab,
            long_term_liab,
            investment,
            retained,
            total_equity,
            total_liab_equity
        ]
    })

# --- File Upload ---
uploaded_file = st.file_uploader("📤 Upload Balance Sheet Excel File", type=["xlsx", "xls", "csv"])
if uploaded_file:
    company_name = os.path.splitext(uploaded_file.name)[0]
    st.markdown(f"🏢 **Detected Company:** `{company_name}`")

    try:
        df = pd.read_excel(uploaded_file)
    except:
        df = pd.read_csv(uploaded_file)

    summary_df = extract_clean_balance_sheet(df)

    st.subheader("📊 Cleaned Balance Sheet Summary")
    st.dataframe(summary_df)

    if summary_df["Amount"].sum() == 0:
        st.warning("⚠️ All values extracted are zero. Please check your file format and column labels.")
