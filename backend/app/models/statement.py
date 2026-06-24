import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Statement(Base):
    __tablename__ = "statements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    filename: Mapped[str] = mapped_column(String)
    source_label: Mapped[str] = mapped_column(String)
    file_path: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="pending")

    # Balance continuity check
    balance_check_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    balance_check_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # PDF authenticity check
    authenticity_signals: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Cross-source overlap flag (set by pipeline when overlap detected)
    has_cross_source_overlap: Mapped[bool] = mapped_column(Boolean, default=False)
    overlap_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user = relationship("User", back_populates="statements")
    transactions = relationship("Transaction", back_populates="statement")