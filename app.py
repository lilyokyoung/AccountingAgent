import streamlit as st
import pandas as pd
import re

# ---------------- Utility Functions ---------------- #

def normalize(text):
    return ''.join(e for e in str(text).lower().strip() if e.isalnum())

def match_columns(df, target_map):
    found = {}
    normalized_columns = {normalize(col): col for col in df.columns}

    for target, options in target_map.items():
        found[target] = None
        for opt in options:
            norm_opt = normalize(opt)
            for norm_col, original_col in normalized_columns.items():
                if norm_opt in norm_col:
                    found[target] = original_col
                    break
            if found[target]:
                break
    return found

def extract_clean_balance_sheet(df, col_map):
    cleaned = []
    for label in col_map:
        col = col_map[label]
        if col and col in df.columns:
            try:
                amount = pd.to_numeric(df[col], errors='coerce').fillna(0).sum()
                cleaned.append((label, amount))
            except:
                cleaned.append((label, 0))
        else:
            cleaned.append((label, 0))
    return pd.DataFrame(cleaned, columns=["Category", "Amount"])

# ---------------- Streamlit App ---------------- #

st.set_page_config(page_title="📊 Accounting Agent", layout="wide")

st.title("📁 Upload Balance Sheet")
uploaded_file = st.file_uploader("Upload Excel or CSV file", type=["csv", "xlsx"])

if uploaded_file:
    filename = uploaded_file.name
    st.markdown(f"🏢 **Detected Company:** `{filename.replace('.xlsx','').replace('.csv','')}`")

    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Display raw data
    with st.expander("🧾 View Raw Data"):
        st.dataframe(df)

    # Fuzzy match map
    concept_map = {
        "Short-Term Liabilities": ["short term liabilities", "current liabilities", "short term borrowings"],
        "Long-Term Liabilities": ["long term liabilities", "non current liabilities", "non-current liabilities"],
        "Owner's Equity": ["owner's equity", "total equity", "share capital", "net worth"],
        "Retained Earnings": ["retained earnings", "accumulated profits", "retained profits", "accumulated earnings"],
    }

    # Perform column matching
    matches = match_columns(df, concept_map)

    for k, v in matches.items():
        if v:
            st.success(f"✅ Matched **{k}** to column: `{v}`")
        else:
            st.error(f"❌ No match found for **{k}**")

    # Build cleaned summary
    summary_df = extract_clean_balance_sheet(df, matches)
    st.markdown("### 📊 Cleaned Balance Sheet Summary")
    st.dataframe(summary_df)

    # Ratio calculation
    st.markdown("### 📉 Key Ratios")
    try:
        st.write("**Debt-to-Equity Ratio**")
        st.metric("Ratio", round(
            (summary_df.loc[summary_df['Category'] == 'Short-Term Liabilities', 'Amount'].values[0] +
             summary_df.loc[summary_df['Category'] == 'Long-Term Liabilities', 'Amount'].values[0]) /
            summary_df.loc[summary_df['Category'] == "Owner's Equity", 'Amount'].values[0], 2)
        )
    except:
        st.warning("⚠️ Unable to compute Debt-to-Equity Ratio due to missing or zero values.")

    try:
        st.write("**Equity Ratio**")
        st.metric("Ratio", round(
            summary_df.loc[summary_df['Category'] == "Owner's Equity", 'Amount'].values[0] /
            summary_df['Amount'].sum(), 2)
        )
    except:
        st.warning("⚠️ Unable to compute Equity Ratio due to missing or zero values.")
