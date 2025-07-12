import pandas as pd
import streamlit as st
import plotly.express as px
import os

# Import the robust extraction function
from balance_sheet_utils import extract_balance_sheet_summary

st.set_page_config(page_title="📊 Financial Analyzer", layout="wide")
st.title("📁 Financial Balance Sheet Analyzer")

uploaded_file = st.file_uploader("Upload your Balance Sheet Excel/CSV file", type=["csv", "xlsx"])

if uploaded_file:
    try:
        file_ext = os.path.splitext(uploaded_file.name)[-1]
        if file_ext == ".csv":
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.markdown("### 🧾 Raw Uploaded Data")
        st.dataframe(df.head())

        # Extract cleaned trend data
        summary_df = extract_balance_sheet_summary(df)

        if "Fiscal Year" not in summary_df.columns:
            st.error("❌ Fiscal Year column missing in extracted data.")
        else:
            st.markdown("### 📈 Financial Trends Over Time")
            st.dataframe(summary_df)

            numeric_cols = summary_df.columns.drop("Fiscal Year")
            for col in numeric_cols:
                fig = px.line(summary_df, x="Fiscal Year", y=col, markers=True,
                              title=f"{col} Over Time")
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("### 📊 Financial Ratios Over Time")
            ratios = []
            for _, row in summary_df.iterrows():
                total_liab = row["Short-Term Liabilities"] + row["Long-Term Liabilities"]
                equity = row["Total Owner's Equity"]
                year = row["Fiscal Year"]

                debt_equity = round(total_liab / equity, 2) if equity else None
                equity_ratio = round(equity / (total_liab + equity), 2) if (total_liab + equity) else None

                ratios.append({
                    "Fiscal Year": year,
                    "Debt to Equity": debt_equity,
                    "Equity Ratio": equity_ratio
                })

            ratio_df = pd.DataFrame(ratios)
            st.dataframe(ratio_df)

            fig1 = px.line(ratio_df, x="Fiscal Year", y="Debt to Equity", markers=True, title="Debt to Equity Over Time")
            fig2 = px.line(ratio_df, x="Fiscal Year", y="Equity Ratio", markers=True, title="Equity Ratio Over Time")
            st.plotly_chart(fig1, use_container_width=True)
            st.plotly_chart(fig2, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Failed to process file: {e}")
else:
    st.info("📤 Upload a balance sheet file to begin analysis.")
