import streamlit as st
import pandas as pd
import plotly.express as px
from balance_sheet_utils import extract_balance_sheet_summary

st.set_page_config(page_title="📘 Balance Sheet Analyzer", layout="wide")
st.title("📘 Cleaned Balance Sheet Summary")

# Upload file
uploaded_file = st.file_uploader("📤 Upload your balance sheet Excel/CSV file", type=["csv", "xlsx"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        st.subheader("📄 Raw Preview of Uploaded File")
        st.dataframe(df)

        # Extract and show summary
        summary_df = extract_balance_sheet_summary(df)
        st.subheader("🧾 Cleaned Balance Sheet Summary")
        st.dataframe(summary_df)

        if summary_df['Amount'].sum() == 0:
            st.warning("⚠️ All values extracted are zero. Please check column names and formatting in your file.")
        else:
            # ✅ Add Ratio Analysis
            st.subheader("📊 Key Financial Ratios")
            try:
                st.markdown("### 📘 Ratio Analysis Based on Latest Year")
                liabilities = summary_df.loc[summary_df['Category'] == "Short-Term Liabilities", 'Amount'].values[0]
                equity = summary_df.loc[summary_df['Category'] == "Total Owner's Equity", 'Amount'].values[0]
                total_assets = summary_df.loc[summary_df['Category'] == "Total Liabilities & Equity", 'Amount'].values[0]

                # Ratios
                current_ratio = round(total_assets / liabilities, 2) if liabilities else None
                debt_to_equity = round((liabilities) / equity, 2) if equity else None
                equity_ratio = round(equity / total_assets, 2) if total_assets else None

                st.metric("🔁 Current Ratio", f"{current_ratio}")
                st.metric("⚖️ Debt-to-Equity Ratio", f"{debt_to_equity}")
                st.metric("📐 Equity Ratio", f"{equity_ratio}")

                # 📈 Graphs
                st.subheader("📉 Balance Sheet Breakdown")
                fig = px.pie(summary_df, names='Category', values='Amount', title='Balance Sheet Composition')
                st.plotly_chart(fig, use_container_width=True)

                bar = px.bar(summary_df, x="Category", y="Amount", title="Balance Sheet Items")
                st.plotly_chart(bar, use_container_width=True)

            except Exception as e:
                st.error(f"❌ Failed to compute ratios: {str(e)}")

    except Exception as e:
        st.error(f"❌ Failed to read file: {str(e)}")
else:
    st.info("📥 Please upload a balance sheet file to begin.")
