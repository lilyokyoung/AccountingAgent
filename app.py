import pandas as pd
import streamlit as st
import plotly.express as px
import os

# Load utility function from balance_sheet_utils.py
from balance_sheet_utils import extract_clean_balance_sheet

st.set_page_config(page_title="📊 Balance Sheet Analyzer", layout="wide")

st.title("📂 Raw Preview of Uploaded File")
uploaded_file = st.file_uploader("Upload your balance sheet Excel/CSV file", type=["csv", "xlsx"])

if uploaded_file:
    try:
        file_ext = os.path.splitext(uploaded_file.name)[-1]
        if file_ext == ".csv":
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.dataframe(df)

        # Generate cleaned summary
        st.markdown("### 🧾 Cleaned Balance Sheet Summary")
        summary_df = extract_clean_balance_sheet(df)
        st.dataframe(summary_df)

        # Warning if all zeros
        if summary_df["Amount"].sum() == 0:
            st.warning("⚠️ All values extracted are zero. Please check your file format and row headers.")

        # 📈 Pie chart: Composition of Liabilities and Equity
        st.markdown("### 📊 Balance Sheet Composition")
        fig = px.pie(summary_df.iloc[:-1], names="Category", values="Amount", title="Composition of Liabilities and Equity")
        st.plotly_chart(fig, use_container_width=True)

        # 📉 Bar chart: Liabilities vs Equity
        st.markdown("### 📉 Liabilities vs Equity")
        grouped = summary_df[summary_df["Category"].isin(["Short-Term Liabilities", "Long-Term Liabilities", "Total Owner's Equity"])]
        fig2 = px.bar(grouped, x="Category", y="Amount", color="Category", title="Liabilities and Equity Breakdown")
        st.plotly_chart(fig2, use_container_width=True)

        # 📌 Financial Ratios
        st.markdown("### 📈 Financial Ratios")
        try:
            short_term = summary_df.loc[summary_df["Category"] == "Short-Term Liabilities", "Amount"].values[0]
            long_term = summary_df.loc[summary_df["Category"] == "Long-Term Liabilities", "Amount"].values[0]
            total_equity = summary_df.loc[summary_df["Category"] == "Total Owner's Equity", "Amount"].values[0]
            total_liabilities = short_term + long_term

            debt_to_equity = round(total_liabilities / total_equity, 2) if total_equity else "N/A"
            equity_ratio = round(total_equity / (total_equity + total_liabilities), 2) if (total_equity + total_liabilities) else "N/A"

            col1, col2 = st.columns(2)
            col1.metric("Debt to Equity Ratio", debt_to_equity)
            col2.metric("Equity Ratio", equity_ratio)
        except Exception as e:
            st.error(f"Ratio calculation failed: {e}")

    except Exception as e:
        st.error(f"❌ Failed to parse balance sheet: {e}")
else:
    st.info("📤 Upload a balance sheet file to begin analysis.")
