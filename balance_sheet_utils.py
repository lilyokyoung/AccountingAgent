def extract_clean_balance_sheet(df):
    df.columns = df.iloc[0]
    df = df.drop(0).reset_index(drop=True)
    latest = df.iloc[0]

    def get_float(colname_options):
        for col in colname_options:
            for actual_col in df.columns:
                if str(actual_col).lower().strip().startswith(col.lower()):
                    try:
                        return float(str(latest[actual_col]).replace(",", ""))
                    except:
                        continue
        return None  # important for conditional logic below

    short_term_liab = get_float(["short-term liabilities", "short term liabilities", "current liabilities"])
    long_term_liab = get_float(["long-term liabilities", "long term liabilities", "non-current liabilities"])
    equity = get_float(["total equity", "net worth"])
    retained = get_float(["retained earnings", "accumulated profits"])
    investment = None

    if retained is not None and equity is not None:
        investment = equity - retained
    elif retained is None and equity is not None:
        retained = 0.0
        investment = equity
    elif equity is None:
        equity = 0.0
        retained = 0.0
        investment = 0.0

    total_equity = investment + retained
    total_liabilities_and_equity = sum(filter(None, [short_term_liab, long_term_liab])) + total_equity

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
            short_term_liab or 0.0,
            long_term_liab or 0.0,
            investment or 0.0,
            retained or 0.0,
            total_equity or 0.0,
            total_liabilities_and_equity or 0.0
        ]
    })
