import streamlit as st
import pandas as pd
from balance_sheet_utils import extract_clean_balance_sheet

st.subheader("📥 Upload Balance Sheet")
uploaded_file = st.file_uploader("Upload Excel or CSV file", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        raw_df = pd.read_csv(uploaded_file, header=None)
    else:
        raw_df = pd.read_excel(uploaded_file, header=None)

    try:
        clean_df = extract_clean_balance_sheet(raw_df)

        st.success("✅ Balance Sheet Processed Successfully")
        st.dataframe(clean_df)

        if abs(clean_df.loc[4, "Amount"] - clean_df["Amount"].sum() + clean_df.loc[4, "Amount"]) > 0.01:
            st.warning("⚠️ Warning: Totals do not match actual item sums. Please verify data integrity.")

        # Optional: Visual chart
        st.bar_chart(clean_df.set_index("Category"))

    except Exception as e:
        st.error(f"❌ Failed to process balance sheet: {e}")
