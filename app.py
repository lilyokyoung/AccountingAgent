import streamlit as st
import pandas as pd
from balance_sheet_utils import extract_clean_balance_sheet

# Page config
st.set_page_config(page_title="📊 Accounting Agent - Balance Sheet Analyzer", layout="wide")
st.title("📊 Accounting Agent")
st.markdown("Upload a balance sheet to extract and verify key components like liabilities and owner's equity.")

# File uploader
uploaded_file = st.file_uploader("Upload Balance Sheet File (.xlsx or .csv)", type=["xlsx", "csv"])

if uploaded_file:
    try:
        # Load file into DataFrame
        if uploaded_file.name.endswith(".csv"):
            raw_df = pd.read_csv(uploaded_file, header=None)
        else:
            raw_df = pd.read_excel(uploaded_file, header=None)

        # Process balance sheet
        clean_df = extract_clean_balance_sheet(raw_df)

        # Show cleaned output
        st.subheader("✅ Extracted Balance Sheet Summary")
        st.dataframe(clean_df, use_container_width=True)

        # Validate total
        computed_total = clean_df.loc[5, "Amount"]
        expected_total = clean_df["Amount"].iloc[0:4].sum()

        if abs(computed_total - expected_total) > 0.01:
            st.warning("⚠️ Warning: Totals do not match actual item sums. Please verify data integrity.")
        else:
            st.success("✅ Totals match. Balance sheet appears consistent.")

        # Optional: Chart
        st.subheader("📈 Visual Breakdown")
        st.bar_chart(clean_df.set_index("Category").iloc[:-1])

    except Exception as e:
        st.error(f"❌ Error processing the file: {e}")
else:
    st.info("Please upload a balance sheet file to begin.")
