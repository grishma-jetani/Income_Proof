import logging
import os
import uuid
from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.stability_metric import StabilityMetric
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.services.analytics.stability_metrics import compute_stability
from app.services.categorization.llm_categorizer import apply_llm_categories, categorize_with_llm
from app.services.categorization.rules import categorize_batch_rules
from app.services.normalization.authenticity import verify_pdf_authenticity
from app.services.normalization.dedupe import get_existing_hashes, mark_duplicates
from app.services.normalization.normalize import check_balance_continuity, normalize
from app.services.parsing.csv_parser import parse_phonepe_csv
from app.services.parsing.pdf_parser import parse_pdf

logger = logging.getLogger(__name__)

SOURCE_GROUPS = {
    "boi_pdf": "bank",
    "unknown_pdf": "bank",
    "phonepe_pdf": "upi",
    "upi_csv": "upi",
}


def _detect_cross_source_overlap(
    db: Session,
    user_uuid: uuid.UUID,
    new_txn_dates: list,
    new_source_format: str,
) -> dict:
    if not new_txn_dates:
        return {}

    new_min = min(new_txn_dates)
    new_max = max(new_txn_dates)
    new_group = SOURCE_GROUPS.get(new_source_format, "unknown")

    rows = (
        db.query(Transaction.source_format, Transaction.txn_date)
        .filter(
            Transaction.user_id == user_uuid,
            Transaction.is_duplicate == False,
        )
        .all()
    )

    by_source: dict[str, list] = defaultdict(list)
    for src, dt in rows:
        by_source[src].append(dt)

    overlapping_sources = []
    for existing_fmt, dates in by_source.items():
        existing_group = SOURCE_GROUPS.get(existing_fmt, "unknown")
        if existing_group == new_group:
            continue
        if existing_group == "unknown" or new_group == "unknown":
            continue

        existing_min = min(dates)
        existing_max = max(dates)
        overlap_start = max(new_min, existing_min)
        overlap_end = min(new_max, existing_max)

        if overlap_start <= overlap_end:
            overlapping_sources.append({
                "existing_source": existing_fmt,
                "existing_range": f"{existing_min} → {existing_max}",
                "overlap_range": f"{overlap_start} → {overlap_end}",
                "risk": (
                    "UPI payouts from platform apps appear in BOTH bank statements "
                    "and UPI app exports. Income in the overlapping period may be "
                    "double-counted."
                ),
            })

    if not overlapping_sources:
        return {}

    return {
        "detected": True,
        "new_source": new_source_format,
        "new_range": f"{new_min} → {new_max}",
        "conflicts": overlapping_sources,
        "recommendation": (
            "To avoid double-counting, consider re-uploading this file "
            "starting from the day after your latest existing data ends."
        ),
    }


def run_pipeline(statement_id: uuid.UUID, filepath: str, user_id: str):
    db: Session = SessionLocal()
    try:
        stmt = db.get(Statement, statement_id)
        if stmt is None:
            logger.error("Statement %s not found", statement_id)
            return

        stmt.status = "processing"
        db.commit()

        user_uuid = uuid.UUID(user_id)
        ext = os.path.splitext(filepath)[1].lower()

        # ── 1. Authenticity check (PDFs only) ─────────────────────────────
        if ext == ".pdf":
            auth_result = verify_pdf_authenticity(filepath)
            stmt.authenticity_signals = auth_result
            db.commit()
            logger.info(
                "Authenticity signal for statement %s: %s",
                statement_id,
                auth_result.get("overall_signal"),
            )

        # ── 2. Parse ───────────────────────────────────────────────────────
        if ext == ".csv":
            raw_txns = parse_phonepe_csv(filepath)
            detected_format = "upi_csv"
        else:
            raw_txns, detected_format = parse_pdf(filepath)

        logger.info("Parsed %d raw transactions (%s)", len(raw_txns), detected_format)

        # ── 3. Normalize ───────────────────────────────────────────────────
        normalized = normalize(raw_txns)

        # ── 4. Balance continuity check ────────────────────────────────────
        continuity_result = check_balance_continuity(normalized)
        stmt.balance_check_passed = continuity_result["passed"]
        stmt.balance_check_details = continuity_result

        if not continuity_result["passed"]:
            logger.warning(
                "Balance continuity FAILED for statement %s — %d issue(s)",
                statement_id,
                len(continuity_result["issues"]),
            )

        # ── 5. Cross-source overlap detection ─────────────────────────────
        new_dates = [t["txn_date"] for t in normalized]
        overlap = _detect_cross_source_overlap(
            db, user_uuid, new_dates, detected_format
        )
        if overlap:
            stmt.has_cross_source_overlap = True
            stmt.overlap_details = overlap
            logger.warning(
                "Cross-source overlap detected for statement %s", statement_id
            )

        # ── 6. Deduplicate ─────────────────────────────────────────────────
        existing_hashes = get_existing_hashes(db, user_uuid)
        deduped = mark_duplicates(normalized, existing_hashes)

        # ── 7. Categorize ──────────────────────────────────────────────────
        after_rules = categorize_batch_rules(deduped)
        uncategorized = [t for t in after_rules if t["category"] is None]
        if uncategorized:
            llm_mapping = categorize_with_llm(uncategorized)
            after_rules = apply_llm_categories(after_rules, llm_mapping)

        # ── 8. Persist transactions ────────────────────────────────────────
        txn_objects = [
            Transaction(
                id=uuid.uuid4(),
                user_id=user_uuid,
                statement_id=statement_id,
                txn_date=t["txn_date"],
                description=t["description"],
                debit=t["debit"],
                credit=t["credit"],
                balance=t.get("balance"),
                category=t.get("category"),
                source_format=detected_format,
                is_duplicate=t["is_duplicate"],
                txn_hash=t["txn_hash"],
            )
            for t in after_rules
        ]
        db.add_all(txn_objects)
        db.flush()

        # ── 9. Stability metrics ───────────────────────────────────────────
        all_non_dup = (
            db.query(Transaction)
            .filter(
                Transaction.user_id == user_uuid,
                Transaction.is_duplicate == False,
            )
            .all()
        )
        all_txn_dicts = [
            {
                "txn_date": t.txn_date,
                "description": t.description,
                "debit": float(t.debit),
                "credit": float(t.credit),
                "category": t.category,
            }
            for t in all_non_dup
        ]

        metrics = compute_stability(all_txn_dicts)

        # ── CRITICAL: extract _factor_detail before **metrics spread ───────
        # _factor_detail is an internal key — not a DB column.
        # Passing it via **metrics to the ORM would raise an error.
        factor_detail = metrics.pop("_factor_detail", {})

        db.query(StabilityMetric).filter(
            StabilityMetric.user_id == user_uuid
        ).delete()

        db.add(
            StabilityMetric(
                id=uuid.uuid4(),
                user_id=user_uuid,
                factor_detail=factor_detail,
                **metrics,
            )
        )

        # ── 10. Finalize ───────────────────────────────────────────────────
        stmt.status = "done"
        stmt.processed_at = datetime.utcnow()
        db.commit()
        logger.info(
            "Pipeline complete for statement %s (user %s)",
            statement_id,
            user_id,
        )

    except Exception as exc:
        logger.exception(
            "Pipeline failed for statement %s: %s", statement_id, exc
        )
        db.rollback()
        stmt = db.get(Statement, statement_id)
        if stmt:
            stmt.status = "failed"
            db.commit()
    finally:
        db.close()