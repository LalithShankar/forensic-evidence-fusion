"""Structured dataset model."""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class StructuredDatasetStatus(enum.StrEnum):
    """Generation status for structured output."""

    generated = "generated"
    failed = "failed"


class StructuredDataset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Structured parser output linked to an artifact transformation."""

    __tablename__ = "structured_datasets"

    artifact_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("artifacts.id"),
        nullable=False,
        index=True,
    )
    transformation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("transformation_records.id"),
        nullable=True,
    )
    dataset_type: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    error_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
