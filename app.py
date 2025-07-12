import streamlit as st
import pandas as pd

# App layout
st.set_page_config(page_title="📊 Accounting Agent", layout="wide")
st.title("📊 Accounting Agent")
st.markdown("Upload a balance sheet file (Excel or CSV) to extract and analyze financial data.")

# Import extractor
try:
    from balance_sheet_utils import extract_clean_balance_sheet
except Exception as e:
    st.error(f"❌ Import failed: {e}")
    st.stop()

# Upload file
uploaded_file = st.file_uploader("📤 Upload File", type=["xlsx", "csv"])

if not uploaded_file:
    st.info("👈 Please upload a balance sheet file to continue.")
    st.stop()

# Preview raw data
try:
    df = pd.read_excel(uploaded_file, header=None) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file, header=None)
    st.subheader("📄 Raw Preview of Uploaded File")
    st.dataframe(df.head(20), use_container_width=True)
except Exception as e:
    st.error(f"❌ Error reading file: {e}")
    st.stop()

# Extract balance sheet values
try:
    clean_df = extract_clean_balance_sheet(df)
    st.subheader("📘 Cleaned Balance Sheet Summary")
    st.dataframe(clean_df, use_container_width=True)

    if clean_df["Amount"].sum() == 0:
        st.warning("⚠️ All values extracted are zero. Check if your labels match terms like 'retained earnings', 'share capital', etc.")
except Exception as e:
    st.error(f"❌ Failed to parse balance sheet: {e}")
