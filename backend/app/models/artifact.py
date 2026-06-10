"""Artifact model for uploaded evidence files."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class ArtifactStatus(enum.StrEnum):
    """Lifecycle status for raw artifact preservation."""

    pending = "pending"
    preserved = "preserved"
    failed = "failed"
    blocked = "blocked"


class Artifact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Raw evidence artifact linked to a case."""

    __tablename__ = "artifacts"

    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=False,
    )
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    file_extension: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    mime_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="application/octet-stream",
    )
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    uploaded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[ArtifactStatus] = mapped_column(
        String(32),
        nullable=False,
        default=ArtifactStatus.pending,
    )
