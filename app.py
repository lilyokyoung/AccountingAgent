import streamlit as st
import pandas as pd
from balance_sheet_utils import extract_clean_balance_sheet

# Optional Gemini integration
try:
    import google.generativeai as genai
    genai.configure(api_key=st.secrets["gemini"]["api_key"])
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False

# Streamlit setup
st.set_page_config(page_title="📊 Accounting Agent - Balance Sheet Auditor", layout="wide")
st.title("📊 Accounting Agent: Balance Sheet Auditor")
st.markdown(
    """
    Upload a firm's balance sheet file to perform automated auditing checks, compute key financial ratios, and receive an AI-generated summary of financial health.
    """
)

# File upload
uploaded_file = st.file_uploader("📤 Upload Balance Sheet (.xlsx or .csv)", type=["xlsx", "csv"])

if uploaded_file:
    try:
        # Load the file
        if uploaded_file.name.endswith(".csv"):
            raw_df = pd.read_csv(uploaded_file, header=None)
        else:
            raw_df = pd.read_excel(uploaded_file, header=None)

        # Parse balance sheet
        clean_df = extract_clean_balance_sheet(raw_df)
        st.subheader("🧾 Cleaned Balance Sheet Summary")
        st.dataframe(clean_df, use_container_width=True)

        # Extract key values
        short_liab = clean_df.loc[0, "Amount"]
        long_liab = clean_df.loc[1, "Amount"]
        investment = clean_df.loc[2, "Amount"]
        retained = clean_df.loc[3, "Amount"]
        total_equity = clean_df.loc[4, "Amount"]
        total_calc = clean_df.loc[5, "Amount"]
        total_liabilities = short_liab + long_liab
        net_worth = total_equity

        # Audit section
        st.subheader("🔍 Automated Audit Checks")
        audit_notes = []

        if abs(total_equity - (investment + retained)) > 0.01:
            audit_notes.append("❌ Owner's Equity mismatch: should equal Investment + Retained Earnings.")

        if abs(total_calc - (total_equity + total_liabilities)) > 0.01:
            audit_notes.append("❌ Total Liabilities & Equity does not match actual sum of parts.")

        if net_worth < 0:
            audit_notes.append("⚠️ Negative Net Worth: Firm may be insolvent.")

        if total_liabilities > 2 * total_equity:
            audit_notes.append("⚠️ High leverage risk: Liabilities exceed double the equity.")

        if audit_notes:
            for issue in audit_notes:
                st.warning(issue)
        else:
            st.success("✅ All accounting checks passed successfully.")

        # Financial Ratio Analysis
        st.subheader("📊 Financial Ratios")

        ratios = {
            "Return on Equity (ROE)": retained / total_equity if total_equity else None,
            "Debt-to-Equity Ratio": total_liabilities / total_equity if total_equity else None,
            "Equity Ratio": total_equity / total_calc if total_calc else None,
            "Liabilities Ratio": total_liabilities / total_calc if total_calc else None,
            "Net Worth": net_worth
        }

        ratio_df = pd.DataFrame([
            {"Ratio": name, "Value": f"{value:.2f}" if value is not None else "N/A"}
            for name, value in ratios.items()
        ])

        st.dataframe(ratio_df, use_container_width=True)

        # AI Summary using Gemini
        if GEMINI_AVAILABLE and st.checkbox("🧠 Generate AI-Powered Financial Summary (Gemini)"):
            with st.spinner("Generating AI summary..."):
                prompt = f"""
You are a financial analyst reviewing a firm's balance sheet. Below are the figures:

- Short-term liabilities: {short_liab}
- Long-term liabilities: {long_liab}
- Owner's investment: {investment}
- Retained earnings: {retained}
- Total equity: {total_equity}
- Total liabilities and equity: {total_calc}

Key Ratios:
- ROE: {ratios['Return on Equity (ROE)']}
- Debt-to-Equity: {ratios['Debt-to-Equity Ratio']}
- Equity Ratio: {ratios['Equity Ratio']}
- Liabilities Ratio: {ratios['Liabilities Ratio']}

Audit Notes:
{'; '.join(audit_notes) if audit_notes else "No issues found."}

Please write a short, professional summary of the firm's financial health, including strengths, risks, and any red flags.
"""
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                st.success("🧠 Financial Summary")
                st.markdown(response.text)

    except Exception as e:
        st.error(f"❌ Error processing file: {e}")
else:
    st.info("Please upload a balance sheet file to begin.")
