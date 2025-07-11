import streamlit as st
import pandas as pd
import os
import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# App title
st.set_page_config(page_title="AccountingAgent", layout="wide")
st.title("📊 AccountingAgent: AI Financial Audit Assistant")

# Upload financial statement file
uploaded_file = st.file_uploader("📁 Upload your Excel financial statement", type=["xlsx"])

# Read Excel file into dataframes
def read_excel(file):
    return pd.read_excel(file, sheet_name=None)

# Basic ratio analysis
def financial_ratios(df_dict):
    try:
        balance = df_dict['Balance Sheet']
        income = df_dict['Income Statement']
        
        total_assets = float(balance.loc[balance['Item'] == 'Total Assets', 'Amount'])
        total_liabilities = float(balance.loc[balance['Item'] == 'Total Liabilities', 'Amount'])
        current_assets = float(balance.loc[balance['Item'] == 'Current Assets', 'Amount'])
        current_liabilities = float(balance.loc[balance['Item'] == 'Current Liabilities', 'Amount'])
        net_income = float(income.loc[income['Item'] == 'Net Income', 'Amount'])
        revenue = float(income.loc[income['Item'] == 'Revenue', 'Amount'])

        ratios = {
            "Current Ratio": round(current_assets / current_liabilities, 2),
            "Debt-to-Equity Ratio": round(total_liabilities / (total_assets - total_liabilities), 2),
            "Return on Assets (ROA)": round(net_income / total_assets, 2),
            "Net Profit Margin": round(net_income / revenue, 2)
        }
        return ratios
    except Exception as e:
        return {"error": str(e)}

# Gemini-powered audit advice
def get_gemini_advice(ratios):
    prompt = f"""You are a financial audit advisor. Given these financial ratios:
{ratios}

Provide insights, flag concerns, and offer suggestions from an audit perspective."""
    
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text

# App logic
if uploaded_file:
    df_dict = read_excel(uploaded_file)
    st.success("✅ File uploaded and parsed successfully!")

    st.subheader("📘 Financial Statement Data")
    for name, df in df_dict.items():
        st.markdown(f"**{name}**")
        st.dataframe(df)

    st.subheader("📈 Ratio Analysis")
    ratios = financial_ratios(df_dict)
    
    if "error" in ratios:
        st.error(f"Error: {ratios['error']}")
    else:
        st.json(ratios)

        st.subheader("🧠 AI-Powered Audit Commentary")
        advice = get_gemini_advice(ratios)
        st.markdown(advice)
