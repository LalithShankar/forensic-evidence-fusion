"""Canonical claim and related stub models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Claim(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Narrative claim stub for future claim-testing workflows."""

    __tablename__ = "claims"

    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=False,
    )
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="general",
    )
    claim_source_artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("artifacts.id"),
        nullable=True,
    )
    parse_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)


class ClaimResolution(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Claim resolution stub."""

    __tablename__ = "claim_resolutions"

    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=False,
    )
    claim_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("claims.id"),
        nullable=False,
    )
    resolution_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
    )
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class AnalystNote(UUIDPrimaryKeyMixin, Base):
    """Analyst note stub."""

    __tablename__ = "analyst_notes"

    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=False,
    )
    author_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    note_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class Report(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Report stub."""

    __tablename__ = "reports"

    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    content_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
