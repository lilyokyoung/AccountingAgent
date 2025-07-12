import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="📊 Financial Ratio Trend Analyzer", layout="wide")
st.title("🏢 Balance Sheet Analyzer with Ratio Trends")

uploaded_file = st.file_uploader("📂 Upload Balance Sheet Excel", type=["xlsx", "csv"])

if uploaded_file:
    company_name = uploaded_file.name.replace(".xlsx", "").replace(".csv", "")
    st.markdown(f"**Detected Company:** `{company_name}`")

    # Load file
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(".xlsx") else pd.read_csv(uploaded_file)

    # Detect fiscal year column (first column assumed)
    df.rename(columns={df.columns[0]: "Fiscal Year"}, inplace=True)

    # Match relevant fields
    field_map = {
        "Short-Term Liabilities": None,
        "Long-Term Liabilities": None,
        "Owner's Equity": None
    }

    for col in df.columns:
        col_lower = col.lower()
        if not field_map["Short-Term Liabilities"] and "short" in col_lower or "current" in col_lower:
            field_map["Short-Term Liabilities"] = col
        elif not field_map["Long-Term Liabilities"] and "long" in col_lower or "non" in col_lower:
            field_map["Long-Term Liabilities"] = col
        elif not field_map["Owner's Equity"] and ("equity" in col_lower or "net worth" in col_lower):
            field_map["Owner's Equity"] = col

    # Show match results
    for key, col in field_map.items():
        if col:
            st.success(f"✅ Matched `{key}` to column: `{col}`")
        else:
            st.error(f"❌ No match found for `{key}`")

    if all(field_map.values()):
        df_calc = df[["Fiscal Year", *field_map.values()]].copy()
        df_calc.columns = ["Fiscal Year", "STL", "LTL", "Equity"]

        # Calculate ratios
        df_calc["Total Liabilities"] = df_calc["STL"] + df_calc["LTL"]
        df_calc["Debt-to-Equity Ratio"] = df_calc["Total Liabilities"] / df_calc["Equity"]
        df_calc["Equity Ratio"] = df_calc["Equity"] / (df_calc["Total Liabilities"] + df_calc["Equity"])

        st.subheader("📋 Cleaned Data")
        st.dataframe(df_calc)

        st.subheader("📊 Key Ratios (Latest Year)")
        latest = df_calc.iloc[-1]
        col1, col2 = st.columns(2)
        col1.metric("Debt-to-Equity", f"{latest['Debt-to-Equity Ratio']:.2f}")
        col2.metric("Equity Ratio", f"{latest['Equity Ratio']:.2f}")

        # Trend charts
        st.subheader("📈 Ratio Trends")

        fig1 = px.line(df_calc, x="Fiscal Year", y="Debt-to-Equity Ratio", markers=True,
                       title="Debt-to-Equity Ratio Over Time")
        st.plotly_chart(fig1, use_container_width=True)

        fig2 = px.line(df_calc, x="Fiscal Year", y="Equity Ratio", markers=True,
                       title="Equity Ratio Over Time")
        st.plotly_chart(fig2, use_container_width=True)

    else:
        st.warning("⚠️ Some columns are missing. Please upload a file with consistent column names.")
