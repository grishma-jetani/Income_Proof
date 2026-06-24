import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.statement import Statement
from app.models.stability_metric import StabilityMetric
from app.models.transaction import Transaction
from app.services.report.pdf_report import build_income_report

router = APIRouter(prefix="/api", tags=["report"])


@router.get("/report")
def download_report(
    start_date: date,
    end_date: date,
    template: str = "loan",
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    if template not in ("loan", "rental"):
        raise HTTPException(
            status_code=400, detail="template must be 'loan' or 'rental'"
        )

    user_uuid = uuid.UUID(current_user)

    txns = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_uuid,
            Transaction.is_duplicate == False,
            Transaction.txn_date >= start_date,
            Transaction.txn_date <= end_date,
        )
        .order_by(Transaction.txn_date.desc())
        .all()
    )

    if not txns:
        raise HTTPException(
            status_code=404,
            detail=(
                "No transactions found for the selected date range. "
                "Upload statements first."
            ),
        )

    txn_dicts = [
        {
            "txn_date": t.txn_date,
            "description": t.description,
            "debit": float(t.debit),
            "credit": float(t.credit),
            "category": t.category,
        }
        for t in txns
    ]

    metric = (
        db.query(StabilityMetric)
        .filter(StabilityMetric.user_id == user_uuid)
        .order_by(StabilityMetric.computed_at.desc())
        .first()
    )

    stability: dict = {}
    if metric:
        stability = {
            "stability_score": float(metric.stability_score),
            "mean_weekly_income": float(metric.mean_weekly_income),
            "cv_pct": float(metric.cv_pct),
            "trend_pct": float(metric.trend_pct),
            "explanation": metric.explanation,
            "action_tip": metric.action_tip or "",
            "platform_breakdown": metric.platform_breakdown or {},
            # ── factor_detail now included so report PDF can render
            # the score breakdown section ──────────────────────────
            "_factor_detail": metric.factor_detail or {},
        }

    # Gather authenticity signals for all statements in this date range
    stmt_ids = list({t.statement_id for t in txns})
    stmts = db.query(Statement).filter(Statement.id.in_(stmt_ids)).all()
    # auth_list = [
    #     {
    #         "filename": s.filename,
    #         **(
    #             s.authenticity_signals
    #             or {
    #                 "overall_signal": "inconclusive",
    #                 "overall_explanation": "Not checked.",
    #                 "checks": [],
    #             }
    #         ),
    #     }
    #     for s in stmts
    #     if s.authenticity_signals is not None
    # ]

    auth_list = [
        {
            "filename": s.filename,
            "has_cross_source_overlap": s.has_cross_source_overlap,
            "overlap_details": s.overlap_details,
            **(
                s.authenticity_signals
                or {
                    "overall_signal": "verified" if s.filename.lower().endswith(".csv") else "inconclusive",
                    "overall_explanation": "CSV export directly from app." if s.filename.lower().endswith(".csv") else "Not checked.",
                    "checks": [],
                }
            ),
        }
        for s in stmts
        if s.authenticity_signals is not None
    ]

    pdf_bytes = build_income_report(
        transactions=txn_dicts,
        stability=stability,
        start_date=start_date,
        end_date=end_date,
        template_type=template,
        authenticity_signals_list=auth_list,
    )

    filename = f"incomeproof_{template}_{start_date}_{end_date}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )