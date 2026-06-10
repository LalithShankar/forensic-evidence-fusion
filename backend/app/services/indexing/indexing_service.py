"""Orchestrate chunk building and search index push."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.auth_deps import check_case_access
from app.models.case_membership import CaseAccessLevel
from app.models.search_chunk import IndexStatus, SearchChunk
from app.models.user import User
from app.services.indexing.chunk_service import build_chunks_for_case
from app.services.indexing.search_backend import SearchBackend
from app.services.storage_service import StorageBackend

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IndexStatusSummary:
    """Counts of chunk indexing states for a case."""

    pending: int
    indexed: int
    failed: int
    total: int


def index_case(
    db: Session,
    user: User,
    case_id: uuid.UUID,
    storage: StorageBackend,
    search_backend: SearchBackend,
) -> IndexStatusSummary | None:
    """Build chunks and push them to the configured search backend."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.contributor):
        return None

    build_chunks_for_case(db, case_id, storage)
    chunks = list(
        db.scalars(select(SearchChunk).where(SearchChunk.case_id == case_id)).all()
    )

    pending_chunks = [
        chunk for chunk in chunks if chunk.index_status == IndexStatus.pending.value
    ]
    if pending_chunks:
        try:
            search_backend.upsert_chunks(pending_chunks)
            for chunk in pending_chunks:
                chunk.index_status = IndexStatus.indexed.value
                chunk.index_error = None
        except Exception as exc:
            logger.exception("Search index push failed for case %s", case_id)
            for chunk in pending_chunks:
                chunk.index_status = IndexStatus.failed.value
                chunk.index_error = str(exc)
        db.commit()

    return get_index_status(db, user, case_id)


def get_index_status(
    db: Session,
    user: User,
    case_id: uuid.UUID,
) -> IndexStatusSummary | None:
    """Return chunk index counts for an accessible case."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.viewer):
        return None

    rows = db.execute(
        select(SearchChunk.index_status, func.count())
        .where(SearchChunk.case_id == case_id)
        .group_by(SearchChunk.index_status)
    ).all()
    counts = {status: count for status, count in rows}
    pending = counts.get(IndexStatus.pending.value, 0)
    indexed = counts.get(IndexStatus.indexed.value, 0)
    failed = counts.get(IndexStatus.failed.value, 0)
    return IndexStatusSummary(
        pending=pending,
        indexed=indexed,
        failed=failed,
        total=pending + indexed + failed,
    )
