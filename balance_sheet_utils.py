import pandas as pd

def extract_balance_sheet_summary(df: pd.DataFrame) -> pd.DataFrame:
    # Handle bad headers
    if df.columns[0] != "Fiscal Year" and df.iloc[0].str.contains("fiscal", case=False).any():
        df.columns = df.iloc[0]
        df = df.drop(0).reset_index(drop=True)

    df.columns = df.columns.astype(str).str.strip().str.lower()

    # Take the latest year
    latest = df.iloc[0]

    def find_value(possible_names):
        for name in possible_names:
            for col in df.columns:
                if name.lower() in col:
                    try:
                        return float(str(latest[col]).replace(",", "").strip())
                    except:
                        continue
        return 0.0

    short_term_liab = find_value(["short-term", "current liabilities"])
    long_term_liab = find_value(["long-term", "non-current liabilities"])
    equity = find_value(["total equity", "net worth"])
    retained = find_value(["retained earnings", "accumulated"])
    investment = equity - retained if equity and retained else equity

    total_equity = investment + retained
    total_liab_equity = short_term_liab + long_term_liab + total_equity

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
            short_term_liab,
            long_term_liab,
            investment,
            retained,
            total_equity,
            total_liab_equity
        ]
    })

    return summary
