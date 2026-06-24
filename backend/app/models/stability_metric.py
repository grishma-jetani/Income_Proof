import uuid
from datetime import date as date_type, datetime

from sqlalchemy import Date, Numeric, ForeignKey, DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StabilityMetric(Base):
    __tablename__ = "stability_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    period_start: Mapped[date_type] = mapped_column(Date)
    period_end: Mapped[date_type] = mapped_column(Date)

    mean_weekly_income: Mapped[float] = mapped_column(Numeric(12, 2))
    income_variance: Mapped[float] = mapped_column(Numeric(12, 2))
    cv_pct: Mapped[float] = mapped_column(Numeric(8, 2))
    trend_pct: Mapped[float] = mapped_column(Numeric(8, 4))
    stability_score: Mapped[float] = mapped_column(Numeric(5, 2))
    explanation: Mapped[str] = mapped_column(Text)
    action_tip: Mapped[str] = mapped_column(Text, default="")
    platform_breakdown: Mapped[dict] = mapped_column(JSONB, default=dict)
    factor_detail: Mapped[dict] = mapped_column(JSONB, default=dict)  # ← new

    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )