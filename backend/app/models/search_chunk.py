"""Search chunk model for RAG indexing."""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class IndexStatus(enum.StrEnum):
    """Indexing lifecycle for a search chunk."""

    pending = "pending"
    indexed = "indexed"
    failed = "failed"


class SearchChunk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Source-linked text chunk for case-scoped retrieval."""

    __tablename__ = "search_chunks"

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
    readable_view_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("readable_views.id"),
        nullable=True,
    )
    event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("evidence_events.id"),
        nullable=True,
    )
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_group: Mapped[str] = mapped_column(String(128), nullable=False)
    provenance_pointer: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    filter_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    index_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=IndexStatus.pending.value,
    )
    index_error: Mapped[str | None] = mapped_column(Text, nullable=True)
