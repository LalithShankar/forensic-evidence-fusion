"""Assistant Q&A audit log model."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class AssistantLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Stored assistant interaction for audit and review."""

    __tablename__ = "assistant_logs"

    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    limitation_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    insufficient_evidence: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    retrieval_chunk_ids: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    source_references: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
