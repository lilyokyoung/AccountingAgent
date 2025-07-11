import pandas as pd

def extract_clean_balance_sheet(df):
    df.columns = [str(col) for col in df.columns]
    df = df.astype(str)

    balance_data = {
        "Total Long-Term Liabilities": 0.0,
        "Owner's Investment": 0.0,
        "Retained Earnings": 0.0
    }

    for _, row in df.iterrows():
        row_str = " ".join(row).lower()
        if "total long-term liabilities" in row_str:
            try:
                balance_data["Total Long-Term Liabilities"] = float([x for x in row if x.replace('.', '', 1).isdigit()][0])
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

    total_equity = balance_data["Owner's Investment"] + balance_data["Retained Earnings"]
    total_liabilities_equity = balance_data["Total Long-Term Liabilities"] + total_equity

    clean_df = pd.DataFrame({
        "Category": [
            "Liabilities",
            "Owner's Investment",
            "Retained Earnings",
            "Total Owner's Equity",
            "Total Liabilities & Equity"
        ],
        "Amount": [
            balance_data["Total Long-Term Liabilities"],
            balance_data["Owner's Investment"],
            balance_data["Retained Earnings"],
            total_equity,
            total_liabilities_equity
        ]
    })

    return clean_df
