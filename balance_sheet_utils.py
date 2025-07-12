import pandas as pd

def extract_clean_balance_sheet(df):
    # Safely convert all cells to lowercase strings
    df = df.fillna("").astype(str).apply(lambda x: x.str.strip().str.lower(), axis=1)

    # Define label match patterns
    keywords = {
        "Short-Term Liabilities": ["short term liabilities", "short-term liabilities", "current liabilities"],
        "Long-Term Liabilities": ["long term liabilities", "long-term liabilities", "non current liabilities"],
        "Owner's Investment": ["owner investment", "owner's investment", "capital contributed"],
        "Retained Earnings": ["retained earnings", "accumulated earnings", "reserves"]
    }

    values = {k: 0.0 for k in keywords}

    # Search for matches
    for _, row in df.iterrows():
        row_text = " ".join(row)
        for label, patterns in keywords.items():
            for pattern in patterns:
                if pattern in row_text:
                    try:
                        numeric_values = [x for x in row if x.replace(",", "").replace(".", "", 1).isdigit()]
                        if numeric_values:
                            values[label] = float(numeric_values[0].replace(",", ""))
                    except Exception as e:
                        print(f"Error parsing {label}: {e}")

    # Totals
    total_equity = values["Owner's Investment"] + values["Retained Earnings"]
    total_liab_eq = values["Short-Term Liabilities"] + values["Long-Term Liabilities"] + total_equity

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
            values["Short-Term Liabilities"],
            values["Long-Term Liabilities"],
            values["Owner's Investment"],
            values["Retained Earnings"],
            total_equity,
            total_liab_eq
        ]
    })
