import streamlit as st
import pandas as pd
import difflib
import os

# Set page config
st.set_page_config(page_title="📊 Balance Sheet Analyzer", layout="wide")

st.title("🧾 Cleaned Balance Sheet Summary")

def extract_clean_balance_sheet(df, debug=False):
    if df.shape[0] < df.shape[1]:
        df = df.transpose()
        if debug:
            st.warning("🔄 Transposed DataFrame due to wide format.")

    df.columns = df.iloc[0]
    df = df.drop(0).reset_index(drop=True)

    latest = df.iloc[0]
    all_columns = [str(c).strip().lower() for c in df.columns]

    def match_column(possible_names):
        for name in possible_names:
            match = difflib.get_close_matches(name.lower(), all_columns, n=1, cutoff=0.6)
            if match:
                if debug:
                    st.info(f"✅ Matched '{name}' to column '{match[0]}'")
                return df.columns[all_columns.index(match[0])]
            else:
                if debug:
                    st.error(f"❌ No match found for '{name}'")
        return None

    def safe_float(val):
        try:
            return float(str(val).replace(",", "").strip())
        except:
            return 0.0

    col_short = match_column(["short term liabilities", "current liabilities"])
    col_long = match_column(["long term liabilities", "non current liabilities"])
    col_equity = match_column(["total equity", "net worth", "owner's equity"])
    col_retained = match_column(["retained earnings", "accumulated profits"])

    val_short = safe_float(latest.get(col_short, 0.0))
    val_long = safe_float(latest.get(col_long, 0.0))
    val_equity = safe_float(latest.get(col_equity, 0.0))
    val_retained = safe_float(latest.get(col_retained, 0.0))

    investment = val_equity - val_retained
    total_equity = val_equity
    total_liabilities_equity = val_short + val_long + total_equity

    if debug:
        st.write("📊 **Extracted Values:**")
        st.write(f"- Short-term liabilities: {val_short}")
        st.write(f"- Long-term liabilities: {val_long}")
        st.write(f"- Equity: {val_equity}")
        st.write(f"- Retained Earnings: {val_retained}")
        st.write(f"- Owner’s Investment: {investment}")

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
            val_short,
            val_long,
            investment,
            val_retained,
            total_equity,
            total_liabilities_equity
        ]
    })

uploaded_file = st.file_uploader("📤 Upload Balance Sheet File (Excel or CSV)", type=["csv", "xls", "xlsx"])

if uploaded_file:
    file_name = uploaded_file.name
    company_name = os.path.splitext(file_name)[0]
    st.subheader(f"🏢 Detected Company: `{company_name}`")

    try:
        if file_name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        cleaned_df = extract_clean_balance_sheet(df, debug=True)
        st.dataframe(cleaned_df, use_container_width=True)

        if cleaned_df["Amount"].sum() == 0:
            st.warning("⚠️ All values extracted are zero. Please check your file format and column labels.")

    except Exception as e:
        st.error(f"❌ Failed to read file: {e}")
