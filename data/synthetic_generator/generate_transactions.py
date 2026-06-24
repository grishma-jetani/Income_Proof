# data/synthetic_generator/generate_transactions.py
import random
from datetime import date, timedelta
import pandas as pd

random.seed(42)  # reproducible output — same data every run, useful for demos

# # (name, min_amount, max_amount, weekdays they typically pay out — 0=Mon..6=Sun)
# PLATFORMS = [
#     ("SWIGGY PAYOUT",          350, 900,  [0, 1, 2, 3, 4, 5, 6]),
#     ("ZOMATO SETTLEMENT",      300, 850,  [0, 2, 4, 6]),
#     ("UBER EARNINGS",          500, 1500, [1, 3, 5, 6]),
#     ("OLA DRIVER PAYOUT",      400, 1300, [0, 2, 4]),
#     ("URBAN COMPANY SETTLEMENT", 600, 2000, [2, 5]),
# ]

# (name, min_amount, max_amount, weekdays they typically pay out — 0=Mon..6=Sun)
PLATFORMS = [
    ("SWIGGY PAYOUT",          250, 600,  [0, 1, 4, 6]),
    ("ZOMATO SETTLEMENT",      300, 750,  [0, 2, 6]),
    ("UBER EARNINGS",          350, 1350, [1, 2, 3, 5, 6]),
    ("OLA DRIVER PAYOUT",      300, 900, [0, 2, 4]),
    ("URBAN COMPANY SETTLEMENT", 400, 1500, [2, 3, 5]),
]



# (name, min_amount, max_amount, frequency: "monthly" or "weekly_multi")
EXPENSES = [
    ("RENT TRANSFER TO LANDLORD", 6000, 9000, "monthly"),
    ("MOBILE RECHARGE JIO",        200,  400, "monthly"),
    ("ELECTRICITY BILL PAYMENT",   400, 1200, "monthly"),
    ("GROCERY PAYMENT",            200, 1500, "weekly_multi"),
    ("UPI TRANSFER TO FAMILY",    1000, 5000, "monthly"),
    ("BIKE LOAN EMI",              2500, 2500, "monthly"),
    ("FOOD ORDER PERSONAL",        150,  500, "weekly_multi"),
]


def generate_transactions(start_date: date, num_months: int = 4, opening_balance: float = 4500.0) -> pd.DataFrame:
    rows = []
    d = start_date
    end_date = start_date + timedelta(days=30 * num_months)

    while d <= end_date:
        weekday = d.weekday()

        # --- income: each platform pays out on its typical days, ~85% of the time ---
        for name, lo, hi, days in PLATFORMS:
            if weekday in days and random.random() < 0.85:
                amt = round(random.uniform(lo, hi), 2)
                rows.append({
                    "date": d,
                    "description": f"UPI-{name.replace(' ', '')}-{random.randint(100000, 999999)}@paytm",
                    "debit": 0.0,
                    "credit": amt,
                })

        # --- monthly recurring expenses, fired once early in the month ---
        if d.day in (1, 2, 3, 4, 5):
            for name, lo, hi, freq in EXPENSES:
                if freq == "monthly" and random.random() < 0.25:
                    amt = round(random.uniform(lo, hi), 2)
                    rows.append({
                        "date": d,
                        "description": f"UPI-{name.replace(' ', '-')}-{random.randint(100000, 999999)}@ybl",
                        "debit": amt,
                        "credit": 0.0,
                    })

        # --- small frequent expenses (groceries, food orders) ---
        for name, lo, hi, freq in EXPENSES:
            if freq == "weekly_multi" and random.random() < 0.3:
                amt = round(random.uniform(lo, hi), 2)
                rows.append({
                    "date": d,
                    "description": f"UPI-{name.replace(' ', '-')}-{random.randint(100000, 999999)}@ibl",
                    "debit": amt,
                    "credit": 0.0,
                })

        d += timedelta(days=1)

    df = pd.DataFrame(rows)
    df = df.sort_values("date", kind="stable").reset_index(drop=True)

    # single clean pass to compute the running balance
    balances = []
    bal = opening_balance
    for _, r in df.iterrows():
        bal = bal + r["credit"] - r["debit"]
        balances.append(round(bal, 2))
    df["balance"] = balances

    return df


if __name__ == "__main__":
    df = generate_transactions(date(2026, 1, 1), num_months=4)
    print(df.head(10))
    print(f"\nTotal transactions: {len(df)}")
    print(f"Final balance: {df['balance'].iloc[-1]}")