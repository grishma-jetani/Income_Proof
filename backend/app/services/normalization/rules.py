import re

# Each entry: (compiled regex pattern, category label)
# Rules are checked in order — first match wins.
# Patterns are matched against the UPPERCASE description.
RULES: list[tuple[re.Pattern, str]] = [
    # Platform payouts — gig income
    (re.compile(r"SWIGGY|BUNDL\s*TECH"), "Platform Payout"),
    (re.compile(r"ZOMATO"), "Platform Payout"),
    (re.compile(r"UBER"), "Platform Payout"),
    (re.compile(r"\bOLA\b|OLADRIVE|OLA\s*DRIVER"), "Platform Payout"),
    (re.compile(r"URBAN\s*COMPANY|URBANCLAP"), "Platform Payout"),
    (re.compile(r"RAPIDO"), "Platform Payout"),
    (re.compile(r"DUNZO"), "Platform Payout"),
    (re.compile(r"ZEPTO"), "Platform Payout"),
    (re.compile(r"BLINKIT|GROFERS"), "Platform Payout"),
    (re.compile(r"PORTER"), "Platform Payout"),

    # Rent
    (re.compile(r"RENT|LANDLORD|HOUSE\s*OWNER|PGOWNER|PG\s*RENT|FLAT\s*RENT"), "Rent"),

    # Groceries & Food
    (re.compile(r"GROCERY|BIGBASKET|DMart|JIOMART|SPENCERS|MORE\s*SUPERMARKET"), "Groceries & Food"),
    (re.compile(r"FOOD\s*ORDER|RESTAURANT|CAFE|HOTEL|DOMINOS|PIZZA|MCDONALDS|SUBWAY"), "Groceries & Food"),
    (re.compile(r"VEGETABLE|FRUITS|KIRANA"), "Groceries & Food"),

    # Utilities & Bills
    (re.compile(r"JIO|AIRTEL|VODAFONE|VI\b|BSNL|TATA\s*SKY|DISH\s*TV"), "Utilities & EMI"),
    (re.compile(r"ELECTRICITY|BIJLI|BESCOM|MSEDCL|TPDDL|KSEB"), "Utilities & EMI"),
    (re.compile(r"WATER\s*BILL|GAS\s*BILL|LPG|INDANE|HP\s*GAS|BHARAT\s*GAS"), "Utilities & EMI"),
    (re.compile(r"RECHARGE|MOBILE\s*BILL|BROADBAND"), "Utilities & EMI"),

    # Loan EMI
    (re.compile(r"EMI|LOAN|BAJAJ\s*FIN|HDFC\s*BANK.*LOAN|ICICI.*LOAN|NACH|ECS\s*DEBIT"), "Loan EMI"),
    (re.compile(r"BIKE\s*LOAN|CAR\s*LOAN|HOME\s*LOAN|PERSONAL\s*LOAN"), "Loan EMI"),

    # Transfers to family
    (re.compile(r"FAMILY|PARENTS|MOTHER|FATHER|BHAI|SISTER|BROTHER|GHAR"), "Transfers to Family"),

    # Salary (for non-gig income)
    (re.compile(r"SALARY|SAL\b|PAYROLL|NEFT.*SALARY"), "Salary"),

    # ATM / Cash
    (re.compile(r"ATM|CASH\s*WDL|WITHDRAWAL"), "Cash Withdrawal"),
]


def apply_rules(description: str) -> str | None:
    """
    Returns the matched category or None if no rule matched.
    None means this transaction should be sent to the LLM fallback.
    """
    upper = description.upper()
    for pattern, category in RULES:
        if pattern.search(upper):
            return category
    return None


def categorize_batch_rules(transactions: list[dict]) -> list[dict]:
    """
    Runs rules against every transaction.
    Sets category=<matched> or category=None (pending LLM).
    """
    result = []
    for txn in transactions:
        category = apply_rules(txn.get("description", ""))
        result.append({**txn, "category": category})
    return result