"""Canonical entity model (MVP generic table)."""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class EntityType(enum.StrEnum):
    """Canonical entity categories."""

    person = "person"
    account = "account"
    device = "device"
    app = "app"
    location = "location"


class Entity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Generic canonical entity linked to a case."""

    __tablename__ = "entities"

    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    display_name: Mapped[str] = mapped_column(String(256), nullable=False)
    source_artifact_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("artifacts.id"),
        nullable=True,
    )
    attributes_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
