"""Transformation pipeline record model."""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class TransformationStage(enum.StrEnum):
    """Pipeline stages visible to clients."""

    preserved = "preserved"
    classified = "classified"
    preprocessed = "preprocessed"
    extracted = "extracted"
    readable_generated = "readable_generated"
    structured_generated = "structured_generated"
    blocked = "blocked"


class TransformationStatus(enum.StrEnum):
    """Overall transformation run status."""

    running = "running"
    completed = "completed"
    failed = "failed"
    blocked = "blocked"


class TransformationRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Auditable transformation run for one artifact."""

    __tablename__ = "transformation_records"

    artifact_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("artifacts.id"),
        nullable=False,
        index=True,
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=False,
    )
    current_stage: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,
    )
    readable_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    structured_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    failure_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    limitation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
