import pandas as pd

def extract_clean_balance_sheet(df):
    # Assume first row contains headers
    df.columns = df.iloc[0]
    df = df.drop(0).reset_index(drop=True)

    # Use the most recent year (row 0)
    latest = df.iloc[0]

    def get_float(colname_options):
        for col in colname_options:
            for actual_col in df.columns:
                if str(actual_col).lower().strip().startswith(col.lower()):
                    try:
                        return float(str(latest[actual_col]).replace(",", ""))
                    except:
                        continue
        return 0.0

    # Match relevant fields
    short_term_liab = get_float(["short-term liabilities", "short term liabilities", "current liabilities"])
    long_term_liab = get_float(["long-term liabilities", "long term liabilities", "non-current liabilities"])
    equity = get_float(["total equity", "net worth"])
    retained = get_float(["retained earnings", "accumulated profits"])
    investment = equity - retained if retained else 0.0

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
