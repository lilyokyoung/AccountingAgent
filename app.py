import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io

st.set_page_config(page_title="📊 Financial Ratio Trend Analyzer", layout="wide")

st.title("🏢 Balance Sheet Analyzer with Ratio Trends")

uploaded_file = st.file_uploader("📂 Upload Balance Sheet Excel", type=["xlsx"])

if uploaded_file:
    company_name = uploaded_file.name.replace(".xlsx", "")
    st.markdown(f"**Detected Company:** `{company_name}`")

    # Load Excel
    df = pd.read_excel(uploaded_file)

    # Try to identify column matches
    col_map = {}
    possible_fields = {
        "Short-Term Liabilities": ["short", "current"],
        "Long-Term Liabilities": ["long", "non current"],
        "Owner's Equity": ["equity", "net worth"],
    }

    for field, keywords in possible_fields.items():
        for col in df.columns:
            if any(k.lower() in str(col).lower() for k in keywords):
                col_map[field] = col
                st.success(f"✅ Matched **{field}** to column: `{col}`")
                break
        if field not in col_map:
            st.error(f"❌ No match found for **{field}**")

    # Continue only if all required columns are found
    if len(col_map) == len(possible_fields):
        data = df[[col_map["Short-Term Liabilities"], col_map["Long-Term Liabilities"], col_map["Owner's Equity"]]].copy()
        data.columns = ["Short-Term Liabilities", "Long-Term Liabilities", "Owner's Equity"]
        data["Fiscal Year"] = df[df.columns[0]]

        st.subheader("📋 Cleaned Balance Sheet Summary")
        st.dataframe(data)

        # Calculate ratios
        data["Debt-to-Equity Ratio"] = (data["Short-Term Liabilities"] + data["Long-Term Liabilities"]) / data["Owner's Equity"]
        data["Equity Ratio"] = data["Owner's Equity"] / (
            data["Short-Term Liabilities"] + data["Long-Term Liabilities"] + data["Owner's Equity"]
        )

        st.subheader("📊 Key Ratios (Latest Year)")
        latest = data.iloc[-1]
        col1, col2 = st.columns(2)
        col1.metric("Debt-to-Equity Ratio", f"{latest['Debt-to-Equity Ratio']:.2f}")
        col2.metric("Equity Ratio", f"{latest['Equity Ratio']:.2f}")

        # Plot Trends
        st.subheader("📈 Ratio Trends")

        fig1, ax1 = plt.subplots()
        ax1.plot(data["Fiscal Year"], data["Debt-to-Equity Ratio"], marker='o')
        ax1.set_title("Debt-to-Equity Ratio Trend")
        ax1.set_xlabel("Year")
        ax1.set_ylabel("Ratio")
        ax1.grid(True)
        st.pyplot(fig1)

        fig2, ax2 = plt.subplots()
        ax2.plot(data["Fiscal Year"], data["Equity Ratio"], marker='o', color='green')
        ax2.set_title("Equity Ratio Trend")
        ax2.set_xlabel("Year")
        ax2.set_ylabel("Ratio")
        ax2.grid(True)
        st.pyplot(fig2)

    else:
        st.warning("🚨 Some fields could not be matched. Please check your file format and headers.")
