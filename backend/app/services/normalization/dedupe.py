import uuid

from sqlalchemy.orm import Session

from app.models.transaction import Transaction


def get_existing_hashes(db: Session, user_id: uuid.UUID) -> set[str]:
    """Fetch all txn_hashes already stored for this specific user."""
    rows = (
        db.query(Transaction.txn_hash)
        .filter(
            Transaction.user_id == user_id,
            Transaction.txn_hash.isnot(None),
        )
        .all()
    )
    return {row[0] for row in rows}


def mark_duplicates(normalized_txns: list[dict], existing_hashes: set[str]) -> list[dict]:
    seen_in_batch: set[str] = set()
    result = []
    for txn in normalized_txns:
        h = txn.get("txn_hash", "")
        is_dup = h in existing_hashes or h in seen_in_batch
        seen_in_batch.add(h)
        result.append({**txn, "is_duplicate": is_dup})
    return result