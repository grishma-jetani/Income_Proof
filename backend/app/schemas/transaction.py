import uuid
from datetime import date

from pydantic import BaseModel


class TransactionOut(BaseModel):
    id: uuid.UUID
    statement_id: uuid.UUID
    txn_date: date
    description: str
    debit: float
    credit: float
    balance: float | None
    category: str | None
    source_format: str
    is_duplicate: bool

    class Config:
        from_attributes = True


class CategoryUpdateRequest(BaseModel):
    category: str


class DashboardResponse(BaseModel):
    total_income: float
    total_expenses: float
    net_savings: float
    weekly_trend: list[dict]
    category_breakdown: list[dict]
    recent_transactions: list[dict]


class StabilityResponse(BaseModel):
    stability_score: float
    mean_weekly_income: float
    cv_pct: float
    trend_pct: float
    explanation: str
    action_tip: str
    platform_breakdown: dict[str, float]
    factor_detail: dict | None = None
    period_start: date | None
    period_end: date | None