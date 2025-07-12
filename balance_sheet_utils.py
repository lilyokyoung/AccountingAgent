# ✅ balance_sheet_utils.py
import pandas as pd

def extract_balance_sheet_summary(df: pd.DataFrame) -> pd.DataFrame:
    # Handle bad headers
    if df.columns[0] != "Fiscal Year" and df.iloc[0].str.contains("fiscal", case=False).any():
        df.columns = df.iloc[0]
        df = df.drop(0).reset_index(drop=True)

    df.columns = df.columns.astype(str).str.strip().str.lower()

    # Ensure fiscal year is numeric
    df["fiscal year"] = pd.to_numeric(df["fiscal year"], errors='coerce')
    df = df.dropna(subset=["fiscal year"]).sort_values("fiscal year", ascending=True)

    # Extract trend over time
    trend_data = []
    for _, row in df.iterrows():
        fy = int(row["fiscal year"])

        def find_val(possible_names):
            for name in possible_names:
                for col in df.columns:
                    if name.lower() in col:
                        try:
                            return float(str(row[col]).replace(",", "").strip())
                        except:
                            continue
            return 0.0

        short_term = find_val(["short-term", "current liabilities"])
        long_term = find_val(["long-term", "non-current liabilities"])
        equity = find_val(["total equity", "net worth"])
        retained = find_val(["retained earnings", "accumulated"])
        investment = equity - retained if equity and retained else equity
        total_equity = investment + retained
        total_liab_equity = short_term + long_term + total_equity

        trend_data.append({
            "Fiscal Year": fy,
            "Short-Term Liabilities": short_term,
            "Long-Term Liabilities": long_term,
            "Owner's Investment": investment,
            "Retained Earnings": retained,
            "Total Owner's Equity": total_equity,
            "Total Liabilities & Equity": total_liab_equity
        })

    return pd.DataFrame(trend_data)
