import streamlit as st
import pandas as pd
from balance_sheet_utils import extract_clean_balance_sheet

st.set_page_config(page_title="📊 Balance Sheet Analyzer", layout="wide")

st.title("📄 Cleaned Balance Sheet Summary")

uploaded_file = st.file_uploader("Upload your balance sheet file (Excel/CSV)", type=["xlsx", "xls", "csv"])

if uploaded_file:
    try:
        # Read file
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.subheader("🧾 Raw Preview of Uploaded File")
        st.dataframe(df)

        # Extract cleaned summary
        summary = extract_clean_balance_sheet(df)
        st.subheader("🧼 Cleaned Balance Sheet Summary")
        st.dataframe(summary)

        if (summary["Amount"] == 0).all():
            st.warning("⚠️ All values extracted are zero. Please check your file format and column labels.")

        # Detect industry based on file name
        industry_map = {
            "dairy": {"de_ratio": 1.2, "equity_ratio": 0.45},
            "retail": {"de_ratio": 1.5, "equity_ratio": 0.4},
            "tech": {"de_ratio": 0.6, "equity_ratio": 0.7},
        }

        filename = uploaded_file.name.lower()
        detected_industry = "Unknown"
        for key in industry_map:
            if key in filename:
                detected_industry = key.capitalize()
                break

        company_name = uploaded_file.name.split('.')[0]
        st.markdown(f"## 🏢 Detected Company: `{company_name}`")
        st.markdown(f"### 🏷️ Industry Classification: **{detected_industry}**")

        if detected_industry != "Unknown":
            st.subheader(f"📊 Industry Benchmark Comparison for `{detected_industry}`")

            # Compute ratios
            total_equity = summary.loc[summary["Category"] == "Total Owner's Equity", "Amount"].values[0]
            total_liabilities = (
                summary.loc[summary["Category"] == "Short-Term Liabilities", "Amount"].values[0] +
                summary.loc[summary["Category"] == "Long-Term Liabilities", "Amount"].values[0]
            )

            try:
                debt_to_equity = total_liabilities / total_equity if total_equity else None
                equity_ratio = total_equity / (total_equity + total_liabilities) if (total_equity + total_liabilities) else None
            except ZeroDivisionError:
                debt_to_equity, equity_ratio = None, None

            # Compare to benchmarks
            industry_data = industry_map[detected_industry.lower()]
            st.metric("Debt to Equity", f"{debt_to_equity:.2f}" if debt_to_equity is not None else "N/A",
                      f"Industry Avg: {industry_data['de_ratio']}")
            st.metric("Equity Ratio", f"{equity_ratio:.2f}" if equity_ratio is not None else "N/A",
                      f"Industry Avg: {industry_data['equity_ratio']}")
        else:
            st.info("ℹ️ Include a known industry keyword (e.g., 'dairy', 'tech') in the filename for benchmark comparison.")

    except Exception as e:
        st.error(f"❌ Failed to read file: {e}")
else:
    st.info("📥 Please upload a file to begin analysis.")
