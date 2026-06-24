import uuid
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.schemas.statement import (
    StatementCoverage,
    StatementStatusResponse,
    UserCoverageResponse,
)
from app.schemas.transaction import CategoryUpdateRequest, TransactionOut

router = APIRouter(prefix="/api", tags=["statements"])

SOURCE_LABELS = {
    "boi_pdf": "Bank of India",
    "phonepe_pdf": "PhonePe",
    "upi_csv": "UPI CSV Export",
    "unknown_pdf": "Unknown Bank",
}


@router.get("/statements/{statement_id}/status", response_model=StatementStatusResponse)
def get_statement_status(
    statement_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    stmt = (
        db.query(Statement)
        .filter(
            Statement.id == statement_id,
            Statement.user_id == uuid.UUID(current_user),
        )
        .first()
    )
    if stmt is None:
        raise HTTPException(status_code=404, detail="Statement not found.")

    txn_count = (
        db.query(Transaction)
        .filter(Transaction.statement_id == statement_id)
        .count()
    )

    return StatementStatusResponse(
        statement_id=stmt.id,
        status=stmt.status,
        balance_check_passed=stmt.balance_check_passed,
        balance_check_details=stmt.balance_check_details,
        authenticity_signals=stmt.authenticity_signals,
        has_cross_source_overlap=stmt.has_cross_source_overlap or False,
        overlap_details=stmt.overlap_details,
        transaction_count=txn_count,
    )


@router.get("/statements/coverage", response_model=UserCoverageResponse)
def get_coverage(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    Returns date-range coverage per source format already uploaded by this user.
    The frontend uses this to show a smart warning before processing new uploads.
    """
    user_uuid = uuid.UUID(current_user)

    rows = (
        db.query(
            Transaction.source_format,
            Transaction.txn_date,
        )
        .filter(
            Transaction.user_id == user_uuid,
            Transaction.is_duplicate == False,
        )
        .all()
    )

    if not rows:
        return UserCoverageResponse(coverage=[], warning=None)

    # Group by source_format
    by_source: dict[str, list] = defaultdict(list)
    for source_format, txn_date in rows:
        by_source[source_format].append(txn_date)

    coverage = []
    for fmt, dates in by_source.items():
        coverage.append(
            StatementCoverage(
                source_format=fmt,
                source_label=SOURCE_LABELS.get(fmt, fmt),
                min_date=str(min(dates)),
                max_date=str(max(dates)),
                transaction_count=len(dates),
            )
        )

    # Build a pre-composed warning if multiple source types exist
    warning = _build_coverage_warning(coverage)

    return UserCoverageResponse(coverage=coverage, warning=warning)


def _build_coverage_warning(coverage: list[StatementCoverage]) -> str | None:
    if len(coverage) <= 1:
        return None

    # Check for overlapping date ranges across different sources
    parts = []
    for c in coverage:
        parts.append(f"{c.source_label} ({c.min_date} → {c.max_date})")

    # Find the overall safest start date for a new upload
    # = day after the latest max_date across all sources
    from datetime import date, timedelta
    max_dates = [date.fromisoformat(c.max_date) for c in coverage]
    overall_max = max(max_dates)
    recommended_start = (overall_max + timedelta(days=1)).isoformat()

    existing_summary = " | ".join(parts)
    return (
        f"You already have data from: {existing_summary}. "
        f"To avoid double-counting income, we recommend your next upload "
        f"starts from {recommended_start}. "
        "If you upload an overlapping period from a different source "
        "(e.g., PhonePe after Bank of India), the same UPI payouts "
        "may appear in both files and be counted twice."
    )


@router.get("/transactions", response_model=list[TransactionOut])
def list_transactions(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    return (
        db.query(Transaction)
        .filter(Transaction.user_id == uuid.UUID(current_user))
        .order_by(Transaction.txn_date.desc())
        .all()
    )


@router.patch("/transactions/{txn_id}/category")
def update_category(
    txn_id: uuid.UUID,
    body: CategoryUpdateRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    txn = (
        db.query(Transaction)
        .filter(
            Transaction.id == txn_id,
            Transaction.user_id == uuid.UUID(current_user),
        )
        .first()
    )
    if txn is None:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    txn.category = body.category
    db.commit()
    return {"id": str(txn_id), "category": body.category}