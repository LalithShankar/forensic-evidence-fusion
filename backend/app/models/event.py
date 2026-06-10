"""Canonical evidence event model."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class ReviewStatus(enum.StrEnum):
    """Analyst review state for an event."""

    pending = "pending"
    reviewed = "reviewed"
    disputed = "disputed"


class EvidenceEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Normalized time-based observation derived from structured evidence."""

    __tablename__ = "evidence_events"

    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=False,
        index=True,
    )
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
    structured_dataset_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("structured_datasets.id"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    event_subtype: Mapped[str | None] = mapped_column(String(64), nullable=True)
    original_timestamp_text: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
    )
    normalized_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    source_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    provenance_pointer: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    review_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ReviewStatus.pending.value,
    )
