import pandas as pd
import difflib

def extract_clean_balance_sheet(df, debug=False):
    # Transpose if needed
    if df.shape[0] < df.shape[1]:
        df = df.transpose()
        if debug: print("🔄 Transposed DataFrame due to wide format.")

    df.columns = df.iloc[0]
    df = df.drop(0).reset_index(drop=True)

    latest = df.iloc[0]
    all_columns = [str(c).strip().lower() for c in df.columns]

    def match_column(possible_names):
        for name in possible_names:
            match = difflib.get_close_matches(name.lower(), all_columns, n=1, cutoff=0.6)
            if match:
                if debug: print(f"✅ Matched '{name}' to column '{match[0]}'")
                return df.columns[all_columns.index(match[0])]
            else:
                if debug: print(f"❌ No match found for '{name}'")
        return None

    def safe_float(val):
        try:
            return float(str(val).replace(",", "").strip())
        except:
            return 0.0

    col_short = match_column(["short term liabilities", "current liabilities"])
    col_long = match_column(["long term liabilities", "non current liabilities"])
    col_equity = match_column(["total equity", "net worth", "owner's equity"])
    col_retained = match_column(["retained earnings", "accumulated profits"])

    val_short = safe_float(latest.get(col_short, 0.0))
    val_long = safe_float(latest.get(col_long, 0.0))
    val_equity = safe_float(latest.get(col_equity, 0.0))
    val_retained = safe_float(latest.get(col_retained, 0.0))

    investment = val_equity - val_retained
    total_equity = val_equity
    total_liabilities_equity = val_short + val_long + total_equity

    if debug:
        print("📊 Extracted Values:")
        print(f"Short-term liabilities: {val_short}")
        print(f"Long-term liabilities: {val_long}")
        print(f"Equity: {val_equity}")
        print(f"Retained Earnings: {val_retained}")
        print(f"Owner’s Investment: {investment}")

    return pd.DataFrame({
        "Category": [
            "Short-Term Liabilities",
            "Long-Term Liabilities",
            "Owner's Investment",
            "Retained Earnings",
            "Total Owner's Equity",
            "Total Liabilities & Equity"
        ],
        "Amount": [
            val_short,
            val_long,
            investment,
            val_retained,
            total_equity,
            total_liabilities_equity
        ]
    })
