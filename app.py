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

# Streamlit page config
st.set_page_config(page_title="📊 Accounting Agent - Balance Sheet Auditor", layout="wide")
st.title("📊 Accounting Agent: Balance Sheet Auditor")
st.markdown(
    """
    Upload a firm's balance sheet file to perform automated auditing checks, compute key financial ratios,
    compare against industry benchmarks, and interact via a chat-style Q&A.
    """
)

# 1️⃣ File Upload
uploaded_file = st.file_uploader("📤 Upload Balance Sheet (.xlsx or .csv)", type=["xlsx", "csv"])
if not uploaded_file:
    st.info("Please upload a balance sheet file to begin.")
    st.stop()

# 2️⃣ Load & Parse
try:
    raw_df = (
        pd.read_csv(uploaded_file, header=None)
        if uploaded_file.name.endswith(".csv")
        else pd.read_excel(uploaded_file, header=None)
    )
    clean_df = extract_clean_balance_sheet(raw_df)

except Exception as e:
    st.error(f"❌ Failed to read or parse file: {e}")
    st.stop()

# 3️⃣ Display Cleaned Balance Sheet
st.subheader("🧾 Cleaned Balance Sheet Summary")
st.dataframe(clean_df, use_container_width=True)

# Extract key figures
short_liab = clean_df.loc[0, "Amount"]
long_liab = clean_df.loc[1, "Amount"]
investment = clean_df.loc[2, "Amount"]
retained = clean_df.loc[3, "Amount"]
total_equity = clean_df.loc[4, "Amount"]
total_calc = clean_df.loc[5, "Amount"]
total_liabilities = short_liab + long_liab
net_worth = total_equity

# 4️⃣ Automated Audit Checks
st.subheader("🔍 Automated Audit Checks")
audit_notes = []

if abs(total_equity - (investment + retained)) > 0.01:
    audit_notes.append("❌ Owner's Equity ≠ Investment + Retained Earnings.")

if abs(total_calc - (total_liabilities + total_equity)) > 0.01:
    audit_notes.append("❌ Total Liabilities & Equity mismatch.")

if net_worth < 0:
    audit_notes.append("⚠️ Negative Net Worth: Insolvency risk.")

if total_liabilities > 2 * total_equity:
    audit_notes.append("⚠️ Leverage high: Liabilities > 2× Equity.")

if audit_notes:
    for note in audit_notes:
        st.warning(note)
else:
    st.success("✅ All accounting checks passed.")

# 5️⃣ Ratio Analysis
st.subheader("📊 Financial Ratio Analysis")
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

# 6️⃣ Industry Benchmark Comparison
st.subheader("📌 Industry Benchmark Comparison")
benchmarks = {
    "Return on Equity (ROE)": 0.12,
    "Debt-to-Equity Ratio": 1.5,
    "Equity Ratio": 0.40,
    "Liabilities Ratio": 0.60
}
benchmark_results = []
for ratio_name, benchmark in benchmarks.items():
    actual = ratios.get(ratio_name)
    if actual is None:
        status = "⚠️ N/A"
    elif "Debt" in ratio_name or "Liabilities" in ratio_name:
        status = "✅ Within range" if actual <= benchmark else "❌ Above benchmark"
    else:
        status = "✅ Healthy" if actual >= benchmark else "❌ Below benchmark"
    benchmark_results.append({
        "Ratio": ratio_name,
        "Firm Value": f"{actual:.2f}" if actual is not None else "N/A",
        "Industry Benchmark": f"{benchmark:.2f}",
        "Status": status
    })
benchmark_df = pd.DataFrame(benchmark_results)
st.dataframe(benchmark_df, use_container_width=True)

# 7️⃣ Optional AI-Powered Summary
if GEMINI_AVAILABLE and st.checkbox("🧠 Generate AI-Powered Financial Summary"):
    prompt = f"""
You are a financial analyst. Here is the firm's balance sheet and key ratios:

Short-term liabilities: {short_liab}
Long-term liabilities: {long_liab}
Owner's investment: {investment}
Retained earnings: {retained}
Total equity: {total_equity}
Total liabilities & equity: {total_calc}

Ratios:
- ROE: {ratios['Return on Equity (ROE)']}
- Debt-to-Equity: {ratios['Debt-to-Equity Ratio']}
- Equity Ratio: {ratios['Equity Ratio']}
- Liabilities Ratio: {ratios['Liabilities Ratio']}

Audit Notes:
{'; '.join(audit_notes) if audit_notes else "No issues detected."}

Provide a concise, professional summary of the firm's financial health, highlighting strengths, risks, and red flags.
"""
    with st.spinner("Generating AI summary..."):
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        st.success("🧠 AI Financial Summary")
        st.markdown(response.text)

# 8️⃣ Botpress-Style Q&A Assistant
if GEMINI_AVAILABLE and st.checkbox("💬 Ask questions about this firm"):
    question = st.text_input("Enter your question:")
    if question:
        context = f"""
Firm Profile:
- Short-term liabilities: {short_liab}
- Long-term liabilities: {long_liab}
- Owner's investment: {investment}
- Retained earnings: {retained}
- Total equity: {total_equity}
- Total liabilities: {total_liabilities}

Ratios:
- ROE: {ratios['Return on Equity (ROE)']}
- Debt-to-Equity: {ratios['Debt-to-Equity Ratio']}
- Equity Ratio: {ratios['Equity Ratio']}
- Liabilities Ratio: {ratios['Liabilities Ratio']}
- Net Worth: {net_worth}

Audit Notes:
{'; '.join(audit_notes) if audit_notes else "No issues detected."}
"""
        prompt = f"""You are an accounting expert. Based on the firm's profile below, answer the question clearly and professionally:

{context}

User's question: "{question}"
"""
        with st.spinner("Thinking..."):
            model = genai.GenerativeModel("gemini-1.5-flash")
            reply = model.generate_content(prompt)
            st.markdown("**🧾 Response:**")
            st.markdown(reply.text)
