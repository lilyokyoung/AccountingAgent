import pandas as pd
import difflib

def fuzzy_get_column(df, target_keywords, cutoff=0.6):
    columns = [str(c).strip().lower() for c in df.columns]
    for keyword in target_keywords:
        matches = difflib.get_close_matches(keyword.lower(), columns, n=1, cutoff=cutoff)
        if matches:
            match_index = columns.index(matches[0])
            return df.columns[match_index]
    return None

def extract_clean_balance_sheet(df):
    df.columns = df.iloc[0]  # use first row as header
    df = df.drop(0).reset_index(drop=True)
    latest = df.iloc[0]

    def get_value(possible_names):
        col = fuzzy_get_column(df, possible_names)
        if col:
            try:
                return float(str(latest[col]).replace(",", ""))
            except:
                return None
        return None

    short_term_liab = get_value(["short term liabilities", "current liabilities"])
    long_term_liab = get_value(["long term liabilities", "non current liabilities"])
    equity = get_value(["total equity", "net worth"])
    retained = get_value(["retained earnings", "accumulated profits"])

    if retained is not None and equity is not None:
        investment = equity - retained
    elif retained is None and equity is not None:
        retained = 0.0
        investment = equity
    elif equity is None:
        equity = 0.0
        retained = 0.0
        investment = 0.0
    else:
        investment = 0.0

    total_equity = investment + retained
    total_liabilities_and_equity = sum(filter(None, [short_term_liab, long_term_liab])) + total_equity

    summary_df = pd.DataFrame({
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

    return summary_df
