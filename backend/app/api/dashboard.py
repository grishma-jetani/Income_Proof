import uuid

import pandas as pd
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.stability_metric import StabilityMetric
from app.models.transaction import Transaction
from app.schemas.transaction import DashboardResponse, StabilityResponse

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    user_uuid = uuid.UUID(current_user)
    txns = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_uuid,
            Transaction.is_duplicate == False,
        )
        .all()
    )

    if not txns:
        return DashboardResponse(
            total_income=0,
            total_expenses=0,
            net_savings=0,
            weekly_trend=[],
            category_breakdown=[],
            recent_transactions=[],
        )

    total_income = sum(float(t.credit) for t in txns)
    total_expenses = sum(float(t.debit) for t in txns)
    net_savings = total_income - total_expenses

    df = pd.DataFrame([
        {
            "txn_date": t.txn_date,
            "credit": float(t.credit),
            "debit": float(t.debit),
        }
        for t in txns
    ])
    df["txn_date"] = pd.to_datetime(df["txn_date"])
    df = df.set_index("txn_date")
    weekly = df.resample("W").sum().reset_index()

    avg_weekly_expenses = (
        float(weekly["debit"].mean()) if len(weekly) > 0 else 0
    )

    weekly_trend = [
        {
            "week": row["txn_date"].strftime("Wk %U"),
            "income": round(row["credit"], 2),
            "expenses": round(row["debit"], 2),
            "avg_expenses": round(avg_weekly_expenses, 2),
        }
        for _, row in weekly.iterrows()
    ]

    category_totals: dict[str, float] = {}
    for t in txns:
        if float(t.credit) > 0:
            cat = t.category or "Personal / Other"
            category_totals[cat] = category_totals.get(cat, 0) + float(t.credit)

    COLORS = [
        "#2D4A43", "#C2654A", "#C8A560", "#5B8A72", "#9CA3AF",
        "#3E635B", "#E3D2AC", "#1F3530", "#6B7280", "#A3B18A",
        "#588157", "#3A5A40",
    ]
    category_breakdown = []
    if total_income > 0:
        for i, (cat, val) in enumerate(
            sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
        ):
            category_breakdown.append({
                "name": cat,
                "value": round(val / total_income * 100, 1),
                "color": COLORS[i % len(COLORS)],
            })

    recent_txns_raw = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_uuid,
            Transaction.is_duplicate == False,
        )
        .order_by(Transaction.txn_date.desc())
        .limit(10)
        .all()
    )
    recent_transactions = [
        {
            "date": str(t.txn_date),
            "description": t.description,
            "category": t.category or "Personal / Other",
            "amount": float(t.credit) if float(t.credit) > 0 else float(t.debit),
            "type": "credit" if float(t.credit) > 0 else "debit",
        }
        for t in recent_txns_raw
    ]

    return DashboardResponse(
        total_income=round(total_income, 2),
        total_expenses=round(total_expenses, 2),
        net_savings=round(net_savings, 2),
        weekly_trend=weekly_trend,
        category_breakdown=category_breakdown,
        recent_transactions=recent_transactions,
    )


@router.get("/stability", response_model=StabilityResponse)
def get_stability(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    user_uuid = uuid.UUID(current_user)
    metric = (
        db.query(StabilityMetric)
        .filter(StabilityMetric.user_id == user_uuid)
        .order_by(StabilityMetric.computed_at.desc())
        .first()
    )
    if metric is None:
        return StabilityResponse(
            stability_score=0,
            mean_weekly_income=0,
            cv_pct=0,
            trend_pct=0,
            explanation="No statements processed yet.",
            action_tip="Upload your bank statements or UPI exports to get started.",
            platform_breakdown={},
            factor_detail=None,
            period_start=None,
            period_end=None,
        )
    return StabilityResponse(
        stability_score=float(metric.stability_score),
        mean_weekly_income=float(metric.mean_weekly_income),
        cv_pct=float(metric.cv_pct),
        trend_pct=float(metric.trend_pct),
        explanation=metric.explanation,
        action_tip=metric.action_tip or "",
        platform_breakdown=metric.platform_breakdown or {},
        factor_detail=metric.factor_detail or {},   # ← was missing after auth rewrite
        period_start=metric.period_start,
        period_end=metric.period_end,
    )