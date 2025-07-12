import streamlit as st
import pandas as pd

# App config
st.set_page_config(page_title="📊 Accounting Agent", layout="wide")
st.title("📊 Accounting Agent")
st.markdown("Upload a firm's balance sheet to extract, audit, and visualize the financial structure.")

# Safe import
try:
    from balance_sheet_utils import extract_clean_balance_sheet
except Exception as e:
    st.error(f"❌ Failed to import balance sheet parser: {e}")
    st.stop()

# File uploader
uploaded_file = st.file_uploader("📤 Upload Balance Sheet File (.xlsx or .csv)", type=["xlsx", "csv"])

if not uploaded_file:
    st.info("👈 Please upload a file to begin.")
    st.stop()

# Load the file
try:
    df = pd.read_excel(uploaded_file, header=None) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file, header=None)
except Exception as e:
    st.error(f"❌ Could not read file: {e}")
    st.stop()

# Parse balance sheet
try:
    clean_df = extract_clean_balance_sheet(df)
    st.subheader("📘 Cleaned Balance Sheet Summary")
    st.dataframe(clean_df, use_container_width=True)

    if clean_df["Amount"].sum() == 0:
        st.warning("⚠️ All values extracted are zero. Please check that the row labels in your file match expected terms like 'retained earnings', 'owner's investment', etc.")

except Exception as e:
    st.error(f"❌ Failed to extract balance sheet values: {e}")
