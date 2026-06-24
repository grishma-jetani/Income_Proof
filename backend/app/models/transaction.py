import uuid
from datetime import date as date_type, datetime

from sqlalchemy import String, Date, Numeric, ForeignKey, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    statement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("statements.id"))

    txn_date: Mapped[date_type] = mapped_column(Date)
    description: Mapped[str] = mapped_column(String)
    debit: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    credit: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    balance: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    category: Mapped[str | None] = mapped_column(String, nullable=True)
    source_format: Mapped[str] = mapped_column(String)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    txn_hash: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="transactions")
    statement = relationship("Statement", back_populates="transactions")