import streamlit as st
import pandas as pd
from difflib import get_close_matches
import re
import os

# --- Config ---
st.set_page_config(page_title="🧾 Smart Balance Sheet Analyzer", layout="wide")
st.title("💡 Smart Balance Sheet Analyzer")

# --- Utility Functions ---
def normalize_text(text):
    return re.sub(r'[^a-z0-9]', '', str(text).lower().strip())

def detect_header_row(df, key_terms=["assets", "liabilities", "equity", "net worth"]):
    for i in range(min(10, len(df))):
        row = df.iloc[i].astype(str).str.lower().str.replace(r'[^a-z]', '', regex=True)
        if any(term in ' '.join(row) for term in key_terms):
            return i
    return 0  # fallback

def match_column(df, options):
    norm_cols = {normalize_text(col): col for col in df.columns}
    for label in options:
        norm_label = normalize_text(label)
        match = get_close_matches(norm_label, norm_cols.keys(), n=1, cutoff=0.6)
        if match:
            return norm_cols[match[0]]
    return None

def extract_clean_balance_sheet(df):
    notes = []
    if df.empty:
        return pd.DataFrame(), ["❌ Empty DataFrame"]

    header_row = detect_header_row(df)
    df.columns = df.iloc[header_row]
    df = df.drop(range(0, header_row + 1)).reset_index(drop=True)
    latest = df.iloc[-1]

    fields = {
        "Short-Term Liabilities": ["short term liabilities", "current liabilities"],
        "Long-Term Liabilities": ["long term liabilities", "non current liabilities"],
        "Retained Earnings": ["retained earnings", "accumulated profits"],
        "Owner's Equity": ["total equity", "owner's equity", "net worth"]
    }

    values = {}

    def try_get(field):
        col = match_column(df, fields[field])
        if col:
            try:
                return float(str(latest[col]).replace(",", "").strip()), None
            except:
                return 0.0, f"⚠️ Couldn't convert value for `{field}`"
        return 0.0, f"❌ No match found for `{field}`"

    for k in fields:
        val, note = try_get(k)
        values[k] = val
        if note:
            notes.append(note)

    investment = max(values["Owner's Equity"] - values["Retained Earnings"], 0.0)
    total_equity = investment + values["Retained Earnings"]
    total_liabilities_equity = values["Short-Term Liabilities"] + values["Long-Term Liabilities"] + total_equity

    summary = pd.DataFrame({
        "Category": [
            "Short-Term Liabilities",
            "Long-Term Liabilities",
            "Owner's Investment",
            "Retained Earnings",
            "Total Owner's Equity",
            "Total Liabilities & Equity"
        ],
        "Amount": [
            values["Short-Term Liabilities"],
            values["Long-Term Liabilities"],
            investment,
            values["Retained Earnings"],
            total_equity,
            total_liabilities_equity
        ]
    })

    return summary, notes

# --- File Upload ---
uploaded_file = st.file_uploader("📤 Upload Balance Sheet Excel or CSV File", type=["xlsx", "xls", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df_uploaded = pd.read_csv(uploaded_file)
    else:
        df_uploaded = pd.read_excel(uploaded_file)

    company_name = os.path.splitext(uploaded_file.name)[0]
    st.markdown(f"🏢 **Detected Company:** `{company_name}`")

    summary_df, warnings = extract_clean_balance_sheet(df_uploaded)

    st.subheader("📊 Cleaned Balance Sheet Summary")
    st.dataframe(summary_df, use_container_width=True)

    for note in warnings:
        st.warning(note)
else:
    st.info("👈 Upload a file to get started.")
