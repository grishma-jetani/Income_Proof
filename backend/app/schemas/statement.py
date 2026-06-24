import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class StatementUploadResponse(BaseModel):
    statement_id: uuid.UUID
    filename: str
    status: str


class StatementStatusResponse(BaseModel):
    statement_id: uuid.UUID
    status: str
    balance_check_passed: bool | None
    balance_check_details: dict[str, Any] | None
    authenticity_signals: dict[str, Any] | None
    has_cross_source_overlap: bool
    overlap_details: dict[str, Any] | None
    transaction_count: int


class StatementCoverage(BaseModel):
    """Date range coverage per source, for the upload-page warning."""
    source_format: str
    source_label: str
    min_date: str   # ISO date string
    max_date: str
    transaction_count: int


class UserCoverageResponse(BaseModel):
    coverage: list[StatementCoverage]
    warning: str | None   # pre-built human-readable warning if overlap risk exists