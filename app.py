import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- Utility Functions ---------------- #

def normalize(text):
    return ''.join(e for e in str(text).lower().strip() if e.isalnum())

def match_columns(df, target_map):
    found = {}
    normalized_columns = {normalize(col): col for col in df.columns}
    for target, options in target_map.items():
        found[target] = None
        for opt in options:
            norm_opt = normalize(opt)
            for norm_col, original_col in normalized_columns.items():
                if norm_opt in norm_col:
                    found[target] = original_col
                    break
            if found[target]:
                break
    return found

# ---------------- Streamlit App ---------------- #

st.set_page_config(page_title="📊 Accounting Agent", layout="wide")
st.title("📁 Upload Balance Sheet File")

uploaded_file = st.file_uploader("Upload Excel or CSV", type=["csv", "xlsx"])

if uploaded_file:
    filename = uploaded_file.name
    st.markdown(f"🏢 **Detected Company:** `{filename.replace('.xlsx','').replace('.csv','')}`")

    df = pd.read_excel(uploaded_file) if filename.endswith(".xlsx") else pd.read_csv(uploaded_file)

    with st.expander("📂 View Raw Data"):
        st.dataframe(df)

    # Expected Concepts
    concept_map = {
        "Short-Term Liabilities": ["short term liabilities", "current liabilities"],
        "Long-Term Liabilities": ["long term liabilities", "non current liabilities"],
        "Owner's Equity": ["owner's equity", "total equity", "net worth"],
        "Retained Earnings": ["retained earnings"],
        "Year": ["fiscal year", "year", "period"]
    }

    matches = match_columns(df, concept_map)
    for k, v in matches.items():
        if v:
            st.success(f"✅ Matched **{k}** to column: `{v}`")
        else:
            st.error(f"❌ No match for **{k}**")

    # Extract matched columns
    if all(matches[k] for k in ["Short-Term Liabilities", "Long-Term Liabilities", "Owner's Equity", "Year"]):
        df_clean = df[[matches["Year"],
                       matches["Short-Term Liabilities"],
                       matches["Long-Term Liabilities"],
                       matches["Owner's Equity"]]].copy()
        df_clean.columns = ["Year", "STL", "LTL", "Equity"]
        df_clean = df_clean.dropna()

        # Compute ratios
        df_clean["Debt_to_Equity"] = (df_clean["STL"] + df_clean["LTL"]) / df_clean["Equity"]
        df_clean["Equity_Ratio"] = df_clean["Equity"] / (df_clean["STL"] + df_clean["LTL"] + df_clean["Equity"])

        # Summary
        st.markdown("## 📊 Cleaned Balance Sheet Summary")
        st.dataframe(df_clean)

        # Key ratios (latest year)
        latest = df_clean.iloc[-1]
        st.markdown("## 🔍 Key Ratios (Latest Year)")
        col1, col2 = st.columns(2)
        col1.metric("Debt-to-Equity", round(latest["Debt_to_Equity"], 2))
        col2.metric("Equity Ratio", round(latest["Equity_Ratio"], 2))

        # Trend Charts
        st.markdown("## 📈 Ratio Trends Over Time")

        fig1 = px.line(df_clean, x="Year", y="Debt_to_Equity", markers=True,
                       title="📉 Debt-to-Equity Ratio Trend")
        fig2 = px.line(df_clean, x="Year", y="Equity_Ratio", markers=True,
                       title="📈 Equity Ratio Trend")

        st.plotly_chart(fig1, use_container_width=True)
        st.plotly_chart(fig2, use_container_width=True)

    else:
        st.warning("⚠️ Not all necessary fields were matched. Trend analysis cannot proceed.")
