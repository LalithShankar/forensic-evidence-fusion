"""Readable preview view model."""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class ReadableViewType(enum.StrEnum):
    """Human-readable preview categories."""

    extracted_text = "extracted_text"
    inventory = "inventory"


class ReadableViewStatus(enum.StrEnum):
    """Generation status for a readable view."""

    generated = "generated"
    partial = "partial"
    failed = "failed"


class ReadableView(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """DB-backed readable preview linked to an artifact transformation."""

    __tablename__ = "readable_views"

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
    view_type: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    error_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
