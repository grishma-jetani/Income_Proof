import hashlib
import re
from datetime import date


def _make_hash(txn: dict) -> str:
    """
    Stable fingerprint for deduplication.
    Uses date + cleaned description + debit + credit.
    Same transaction appearing in two different uploads will produce the same hash.
    """
    raw = f"{txn['txn_date']}|{txn['description'].lower().strip()}|{txn['debit']:.2f}|{txn['credit']:.2f}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _clean_description(desc: str) -> str:
    """Collapse multiple spaces/newlines and strip."""
    return re.sub(r"\s+", " ", desc).strip()


def normalize(raw_transactions: list[dict]) -> list[dict]:
    """
    Takes the raw output from any parser and returns a clean, uniform list.
    Adds:  txn_hash (for dedup)
    Cleans: description (collapse whitespace)
    Validates: skips rows with no date or zero amount on both sides
    """
    normalized = []
    for txn in raw_transactions:
        # Skip rows with no date
        if not isinstance(txn.get("txn_date"), date):
            continue
        # Skip rows where both debit and credit are zero
        if txn.get("debit", 0) == 0.0 and txn.get("credit", 0) == 0.0:
            continue

        clean = {
            "txn_date": txn["txn_date"],
            "description": _clean_description(txn.get("description", "")),
            "debit": round(float(txn.get("debit", 0)), 2),
            "credit": round(float(txn.get("credit", 0)), 2),
            "balance": round(float(txn["balance"]), 2) if txn.get("balance") is not None else None,
            "source_format": txn.get("source_format", "unknown"),
        }
        clean["txn_hash"] = _make_hash(clean)
        normalized.append(clean)

    return normalized


def check_balance_continuity(normalized_txns: list[dict]) -> dict:
    """
    For statements that include a running balance column (BOI PDF),
    verify that each row's balance = previous_balance + credit - debit.

    Returns:
      {
        "passed": bool,
        "issues": [{"row": int, "description": str,
                    "expected": float, "actual": float, "discrepancy": float}]
      }
    """
    # Only check transactions that have a balance field
    balance_txns = [(i, t) for i, t in enumerate(normalized_txns) if t["balance"] is not None]

    if len(balance_txns) < 2:
        # Not enough balance-bearing rows to check
        return {"passed": True, "issues": []}

    issues = []
    for idx in range(1, len(balance_txns)):
        row_num, curr = balance_txns[idx]
        _, prev = balance_txns[idx - 1]

        expected = round(prev["balance"] + curr["credit"] - curr["debit"], 2)
        actual = curr["balance"]

        # Allow ₹1 tolerance for rounding differences across different systems
        if abs(expected - actual) > 1.0:
            issues.append({
                "row": row_num,
                "description": curr["description"],
                "expected": expected,
                "actual": actual,
                "discrepancy": round(actual - expected, 2),
            })

    return {"passed": len(issues) == 0, "issues": issues}