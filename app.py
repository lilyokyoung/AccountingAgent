import streamlit as st
import pandas as pd
from balance_sheet_utils import extract_clean_balance_sheet
import google.generativeai as genai  # Optional: Gemini integration

# Configure Gemini (if you want AI-powered summary)
genai.configure(api_key=st.secrets["gemini"]["api_key"])

# Page setup
st.set_page_config(page_title="🧠 Accounting Agent - AI Auditor", layout="wide")
st.title("🧠 Accounting Agent")
st.markdown("Upload a firm's balance sheet to get auditing checks, red flags, ratio analysis, and AI summary.")

# Upload balance sheet
uploaded_file = st.file_uploader("📤 Upload Balance Sheet (.xlsx or .csv)", type=["xlsx", "csv"])

if uploaded_file:
    try:
        # Load file
        if uploaded_file.name.endswith(".csv"):
            raw_df = pd.read_csv(uploaded_file, header=None)
        else:
            raw_df = pd.read_excel(uploaded_file, header=None)

        # Clean and extract key figures
        clean_df = extract_clean_balance_sheet(raw_df)

        # Display extracted summary
        st.subheader("🧾 Extracted Balance Sheet")
        st.dataframe(clean_df, use_container_width=True)

        # --- AUDIT CHECKS ---
        st.subheader("🔍 Audit Checks")

        liabilities = clean_df.loc[0, "Amount"] + clean_df.loc[1, "Amount"]
        investment = clean_df.loc[2, "Amount"]
        retained = clean_df.loc[3, "Amount"]
        equity = clean_df.loc[4, "Amount"]
        total = clean_df.loc[5, "Amount"]

        audit_issues = []

        # Check equity consistency
        if abs(equity - (investment + retained)) > 0.01:
            audit_issues.append("❌ Owner's Equity does not match Investment + Retained Earnings.")

        # Check total consistency
        if abs(total - (liabilities + equity)) > 0.01:
            audit_issues.append("❌ Total Liabilities & Equity does not match calculated total.")

        # Check for negative values
        if equity < 0:
            audit_issues.append("⚠️ Negative equity detected.")
        if liabilities > 2 * equity:
            audit_issues.append("⚠️ Liabilities exceed double the equity — potential solvency risk.")

        if audit_issues:
            for issue in audit_issues:
                st.warning(issue)
        else:
            st.success("✅ All accounting checks passed.")

        # --- RATIO ANALYSIS ---
        st.subheader("📊 Ratio Analysis")

        roe = retained / equity if equity != 0 else None
        debt_equity = liabilities / equity if equity != 0 else None

        ratio_df = pd.DataFrame({
            "Ratio": ["Return on Equity (ROE)", "Debt-to-Equity Ratio"],
            "Value": [f"{roe:.2f}" if roe is not None else "N/A",
                      f"{debt_equity:.2f}" if debt_equity is not None else "N/A"]
        })

        st.dataframe(ratio_df, use_container_width=True)

        # --- GEMINI AI SUMMARY (Optional) ---
        if st.checkbox("🧠 Generate AI Summary (Gemini)"):
            prompt = f"""
            Analyze the following balance sheet:
            Liabilities: {liabilities}
            Owner's Investment: {investment}
            Retained Earnings: {retained}
            Equity: {equity}
            Total: {total}

            ROE: {roe}
            Debt-to-Equity: {debt_equity}

            Provide a brief financial health summary and red flag interpretation.
            """
            with st.spinner("Thinking like an auditor..."):
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                st.success("🧠 AI Summary")
                st.markdown(response.text)

    except Exception as e:
        st.error(f"❌ Failed to process file: {e}")
else:
    st.info("Please upload a balance sheet to begin.")
