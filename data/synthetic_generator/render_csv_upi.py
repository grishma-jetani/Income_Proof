# data/synthetic_generator/render_csv_upi.py
import pandas as pd


def render_upi_csv(df, output_path):
    rows = []
    for i, row in df.iterrows():
        if row["credit"] > 0:
            txn_type, amount = "CREDIT", row["credit"]
        else:
            txn_type, amount = "DEBIT", row["debit"]

        rows.append({
            "Transaction ID": f"T{1000000 + i}",
            "Date": row["date"].strftime("%Y-%m-%d"),
            "Time": "00:00:00",
            "Type": txn_type,
            "Amount (INR)": amount,
            "Description": row["description"],
            "Status": "SUCCESS",
        })

    pd.DataFrame(rows).to_csv(output_path, index=False)