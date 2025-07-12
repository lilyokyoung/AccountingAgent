import streamlit as st
import pandas as pd
import plotly.express as px
from balance_sheet_utils import extract_clean_balance_sheet

# Optional Gemini integration
try:
    import google.generativeai as genai
    genai.configure(api_key=st.secrets["gemini"]["api_key"])
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False

# Page config
st.set_page_config(page_title="📊 Accounting Agent - Auditor", layout="wide")
st.title("📊 Accounting Agent: Interactive Balance Sheet Auditor")
st.markdown("Upload a firm's balance sheet to generate insights, visualizations, audit checks, and AI feedback.")

# File upload
uploaded_file = st.file_uploader("📤 Upload Balance Sheet (.xlsx or .csv)", type=["xlsx", "csv"])
if not uploaded_file:
    st.info("Please upload a balance sheet file to begin.")
    st.stop()

# Load and parse file
try:
    raw_df = pd.read_csv(uploaded_file, header=None) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file, header=None)
    clean_df = extract_clean_balance_sheet(raw_df)
except Exception as e:
    st.error(f"❌ Failed to read file: {e}")
    st.stop()

# Display balance sheet
st.subheader("🧾 Cleaned Balance Sheet Summary")
st.dataframe(clean_df, use_container_width=True)

# Extract values
short_liab = clean_df.loc[0, "Amount"]
long_liab = clean_df.loc[1, "Amount"]
investment = clean_df.loc[2, "Amount"]
retained = clean_df.loc[3, "Amount"]
total_equity = clean_df.loc[4, "Amount"]
total_calc = clean_df.loc[5, "Amount"]
total_liabilities = short_liab + long_liab
net_worth = total_equity

# 📘 Capital Structure Donut Chart
st.subheader("📘 Capital Structure Breakdown")
structure_data = pd.DataFrame({
    "Component": ["Liabilities", "Equity"],
    "Amount": [total_liabilities, total_equity]
})
fig_structure = px.pie(structure_data, names="Component", values="Amount", hole=0.5, title="Liabilities vs Equity")
st.plotly_chart(fig_structure, use_container_width=True)

# 🔍 Audit checks
st.subheader("🔍 Automated Audit Checks")
audit_notes = []
if abs(total_equity - (investment + retained)) > 0.01:
    audit_notes.append("❌ Owner's Equity mismatch: Investment + Retained Earnings ≠ Equity.")
if abs(total_calc - (total_liabilities + total_equity)) > 0.01:
    audit_notes.append("❌ Total Liabilities & Equity mismatch.")
if net_worth < 0:
    audit_notes.append("⚠️ Negative Net Worth: Possible insolvency.")
if total_liabilities > 2 * total_equity:
    audit_notes.append("⚠️ High leverage: Liabilities exceed 2× Equity.")

if audit_notes:
    for note in audit_notes:
        st.warning(note)
else:
    st.success("✅ All accounting checks passed.")

# 📊 Financial Ratios
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

# 📌 Benchmark Comparison
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
        status = "✅ OK" if actual <= benchmark else "❌ High"
    else:
        status = "✅ Healthy" if actual >= benchmark else "❌ Low"
    benchmark_results.append({
        "Ratio": ratio_name,
        "Firm Value": f"{actual:.2f}" if actual is not None else "N/A",
        "Industry Benchmark": f"{benchmark:.2f}",
        "Status": status
    })
benchmark_df = pd.DataFrame(benchmark_results)
st.dataframe(benchmark_df, use_container_width=True)

# 📈 Interactive Bar Chart: Firm vs Benchmark
st.subheader("📈 Firm vs Industry Financial Ratios")
bar_data = pd.DataFrame({
    "Ratio": list(benchmarks.keys()) * 2,
    "Value": [
        ratios["Return on Equity (ROE)"],
        ratios["Debt-to-Equity Ratio"],
        ratios["Equity Ratio"],
        ratios["Liabilities Ratio"],
        benchmarks["Return on Equity (ROE)"],
        benchmarks["Debt-to-Equity Ratio"],
        benchmarks["Equity Ratio"],
        benchmarks["Liabilities Ratio"],
    ],
    "Type": ["Firm"] * 4 + ["Industry Benchmark"] * 4
})
fig_bar = px.bar(bar_data, x="Ratio", y="Value", color="Type", barmode="group", title="Financial Ratios Comparison")
st.plotly_chart(fig_bar, use_container_width=True)

# 🧠 AI Summary
if GEMINI_AVAILABLE and st.checkbox("🧠 Generate AI-Powered Financial Summary"):
    prompt = f"""
You are a financial analyst. Analyze the following firm's financial profile:

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
{'; '.join(audit_notes) if audit_notes else "No audit issues detected."}

Write a concise, professional financial summary with insights, strengths, risks, and red flags.
"""
    with st.spinner("Generating summary..."):
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        st.success("📄 Financial Summary")
        st.markdown(response.text)

# 💬 Chat-style Q&A
if GEMINI_AVAILABLE and st.checkbox("💬 Ask questions about this firm"):
    question = st.text_input("Enter your question:")
    if question:
        context = f"""
Firm Details:
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
        full_prompt = f"""
You are an expert accountant. Based on the firm profile and audit results below, answer the following question:

{context}

Question: {question}
"""
        with st.spinner("Thinking..."):
            model = genai.GenerativeModel("gemini-1.5-flash")
            answer = model.generate_content(full_prompt)
            st.markdown("**🧾 Answer:**")
            st.markdown(answer.text)
