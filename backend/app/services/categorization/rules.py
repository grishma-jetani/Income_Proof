import re

# Shared constant — imported by stability_metrics.py
# Add any new platform name here and it automatically counts as income everywhere.
PLATFORM_PAYOUT_CATEGORIES = {
    "Swiggy Payout",
    "Zomato Payout",
    "Uber Earnings",
    "Ola Earnings",
    "Urban Company Payout",
    "Rapido Earnings",
    "Dunzo Payout",
    "Zepto Payout",
    "Blinkit Payout",
    "Porter Payout",
}

INCOME_CATEGORIES = PLATFORM_PAYOUT_CATEGORIES | {"Salary"}

RULES: list[tuple[re.Pattern, str]] = [
    # --- Gig platforms (specific names) ---
    (re.compile(r"SWIGGY|BUNDL\s*TECH"),              "Swiggy Payout"),
    (re.compile(r"ZOMATO"),                             "Zomato Payout"),
    (re.compile(r"UBER"),                               "Uber Earnings"),
    (re.compile(r"\bOLA\b|OLADRIVE|OLA\s*DRIVER"),     "Ola Earnings"),
    (re.compile(r"URBAN\s*COMPANY|URBANCLAP"),          "Urban Company Payout"),
    (re.compile(r"RAPIDO"),                             "Rapido Earnings"),
    (re.compile(r"DUNZO"),                              "Dunzo Payout"),
    (re.compile(r"ZEPTO"),                              "Zepto Payout"),
    (re.compile(r"BLINKIT|GROFERS"),                    "Blinkit Payout"),
    (re.compile(r"PORTER"),                             "Porter Payout"),

    # --- Rent ---
    (re.compile(r"RENT|LANDLORD|HOUSE\s*OWNER|PGOWNER|PG\s*RENT|FLAT\s*RENT"), "Rent"),

    # --- Groceries & Food ---
    (re.compile(r"GROCERY|BIGBASKET|DMART|JIOMART|SPENCERS|MORE\s*SUPERMARKET"), "Groceries & Food"),
    (re.compile(r"FOOD\s*ORDER|RESTAURANT|CAFE|HOTEL|DOMINOS|PIZZA|MCDONALDS|SUBWAY"), "Groceries & Food"),
    (re.compile(r"VEGETABLE|FRUITS|KIRANA"), "Groceries & Food"),

    # --- Utilities & Bills ---
    (re.compile(r"JIO|AIRTEL|VODAFONE|\bVI\b|BSNL|TATA\s*SKY|DISH\s*TV"),   "Utilities & EMI"),
    (re.compile(r"ELECTRICITY|BIJLI|BESCOM|MSEDCL|TPDDL|KSEB"),              "Utilities & EMI"),
    (re.compile(r"WATER\s*BILL|GAS\s*BILL|LPG|INDANE|HP\s*GAS|BHARAT\s*GAS"), "Utilities & EMI"),
    (re.compile(r"RECHARGE|MOBILE\s*BILL|BROADBAND"),                         "Utilities & EMI"),

    # --- Loan EMI ---
    (re.compile(r"EMI|LOAN|BAJAJ\s*FIN|NACH|ECS\s*DEBIT"),          "Loan EMI"),
    (re.compile(r"BIKE\s*LOAN|CAR\s*LOAN|HOME\s*LOAN|PERSONAL\s*LOAN"), "Loan EMI"),

    # --- Transfers to family ---
    (re.compile(r"FAMILY|PARENTS|MOTHER|FATHER|BHAI|SISTER|BROTHER|GHAR"), "Transfers to Family"),

    # --- Salary ---
    (re.compile(r"SALARY|SAL\b|PAYROLL|NEFT.*SALARY"), "Salary"),

    # --- Cash ---
    (re.compile(r"ATM|CASH\s*WDL|WITHDRAWAL"), "Cash Withdrawal"),
]


def apply_rules(description: str) -> str | None:
    upper = description.upper()
    for pattern, category in RULES:
        if pattern.search(upper):
            return category
    return None


def categorize_batch_rules(transactions: list[dict]) -> list[dict]:
    result = []
    for txn in transactions:
        category = apply_rules(txn.get("description", ""))
        result.append({**txn, "category": category})
    return result