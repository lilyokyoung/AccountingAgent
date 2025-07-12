import pandas as pd

def extract_clean_balance_sheet(df):
    # Standardize column names and string types
    df.columns = [str(col) for col in df.columns]
    df = df.astype(str)

    # Store extracted values
    balance_data = {
        "Short-Term Liabilities": 0.0,
        "Long-Term Liabilities": 0.0,
        "Owner's Investment": 0.0,
        "Retained Earnings": 0.0
    }

    # Extract values based on row text
    for _, row in df.iterrows():
        row_str = " ".join(row).lower()
        # Match and extract numbers
        if "short-term liabilities" in row_str:
            try:
                balance_data["Short-Term Liabilities"] = float([x for x in row if x.replace('.', '', 1).isdigit()][0])
            except:
                pass
        elif "total long-term liabilities" in row_str:
            try:
                balance_data["Long-Term Liabilities"] = float([x for x in row if x.replace('.', '', 1).isdigit()][0])
            except:
                pass
        elif "owner's investment" in row_str:
            try:
                balance_data["Owner's Investment"] = float([x for x in row if x.replace('.', '', 1).isdigit()][0])
            except:
                pass
        elif "retained earnings" in row_str:
            try:
                balance_data["Retained Earnings"] = float([x for x in row if x.replace('.', '', 1).isdigit()][0])
            except:
                pass

    # Compute totals
    total_liabilities = balance_data["Short-Term Liabilities"] + balance_data["Long-Term Liabilities"]
    total_equity = balance_data["Owner's Investment"] + balance_data["Retained Earnings"]
    total_liabilities_equity = total_liabilities + total_equity

    # Return a cleaned summary table
    clean_df = pd.DataFrame({
        "Category": [
            "Short-Term Liabilities",
            "Long-Term Liabilities",
            "Owner's Investment",
            "Retained Earnings",
            "Total Owner's Equity",
            "Total Liabilities & Equity"
        ],
        "Amount": [
            balance_data["Short-Term Liabilities"],
            balance_data["Long-Term Liabilities"],
            balance_data["Owner's Investment"],
            balance_data["Retained Earnings"],
            total_equity,
            total_liabilities_equity
        ]
    })

    return clean_df
