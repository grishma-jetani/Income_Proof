import pandas as pd


def parse_phonepe_csv(filepath: str) -> list[dict]:
    """
    Parses a PhonePe-style UPI export CSV.
    Expected columns:
      Transaction ID | Date | Time | Type | Amount (INR) | Description | Status
    Returns a list of normalized transaction dicts.
    """
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip()

    results = []
    for _, row in df.iterrows():
        status = str(row.get("Status", "")).strip().upper()
        if status != "SUCCESS":
            continue

        try:
            txn_date = pd.to_datetime(str(row["Date"]).strip()).date()
        except Exception:
            continue

        raw_amount = str(row.get("Amount (INR)", "0")).replace(",", "").strip()
        try:
            amount = float(raw_amount)
        except ValueError:
            amount = 0.0

        txn_type = str(row.get("Type", "")).strip().upper()
        description = str(row.get("Description", "")).strip()

        results.append({
            "txn_date": txn_date,
            "description": description,
            "debit": amount if txn_type == "DEBIT" else 0.0,
            "credit": amount if txn_type == "CREDIT" else 0.0,
            "balance": None,
            "source_format": "upi_csv",
        })

    return results