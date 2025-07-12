import pandas as pd
import difflib

def extract_clean_balance_sheet(df):
    # Try to fix orientation
    if df.shape[0] < df.shape[1]:
        df = df.transpose()

    df.columns = df.iloc[0]
    df = df.drop(0).reset_index(drop=True)

    # Only take first row for latest values
    latest = df.iloc[0]
    all_columns = [str(c).strip().lower() for c in df.columns]

    def match_column(possible_names):
        for name in possible_names:
            match = difflib.get_close_matches(name.lower(), all_columns, n=1, cutoff=0.6)
            if match:
                return df.columns[all_columns.index(match[0])]
        return None

    short_term_liab_col = match_column(["short term liabilities", "current liabilities"])
    long_term_liab_col = match_column(["long term liabilities", "non current liabilities"])
    equity_col = match_column(["total equity", "net worth", "owner's equity"])
    retained_col = match_column(["retained earnings", "accumulated profits"])

    def safe_float(value):
        try:
            return float(str(value).replace(",", "").strip())
        except:
            return 0.0

    short_term_liab = safe_float(latest.get(short_term_liab_col, 0.0))
    long_term_liab = safe_float(latest.get(long_term_liab_col, 0.0))
    equity = safe_float(latest.get(equity_col, 0.0))
    retained = safe_float(latest.get(retained_col, 0.0))

    investment = equity - retained if retained is not None else equity
    total_equity = investment + retained
    total_liabilities_and_equity = short_term_liab + long_term_liab + total_equity

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
            short_term_liab,
            long_term_liab,
            investment,
            retained,
            total_equity,
            total_liabilities_and_equity
        ]
    })
