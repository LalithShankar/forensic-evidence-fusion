"""Build source-linked search chunks from readable views and events."""

from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.artifact import PROVENANCE_UNKNOWN, Artifact
from app.models.event import EvidenceEvent
from app.models.readable_view import ReadableView, ReadableViewStatus
from app.models.search_chunk import IndexStatus, SearchChunk
from app.services.storage_service import StorageBackend, StorageError

_CHUNK_SIZE = 800
_CHUNK_OVERLAP = 100


def build_chunks_for_artifact(
    db: Session,
    case_id: uuid.UUID,
    artifact_id: uuid.UUID,
    storage: StorageBackend,
) -> list[SearchChunk]:
    """Create pending chunks for one artifact's readable views and events."""
    artifact = db.get(Artifact, artifact_id)
    if artifact is None or artifact.case_id != case_id:
        return []

    db.execute(
        delete(SearchChunk).where(
            SearchChunk.case_id == case_id,
            SearchChunk.artifact_id == artifact_id,
        )
    )

    chunks: list[SearchChunk] = []
    views = db.scalars(
        select(ReadableView)
        .where(ReadableView.artifact_id == artifact_id)
        .order_by(ReadableView.created_at.desc())
    ).all()

    for view in views:
        if view.status != ReadableViewStatus.generated.value or not view.storage_path:
            continue
        try:
            text = storage.read_raw(view.storage_path).decode("utf-8", errors="replace")
        except StorageError:
            continue

        provenance = f"readable_view:{view.id}"
        for index, piece in enumerate(_split_text(text)):
            chunk = SearchChunk(
                case_id=case_id,
                artifact_id=artifact_id,
                readable_view_id=view.id,
                chunk_text=piece,
                chunk_index=index,
                source_group=artifact.source_group or PROVENANCE_UNKNOWN,
                provenance_pointer=provenance,
                filter_metadata={"chunk_kind": "readable_text"},
                index_status=IndexStatus.pending.value,
            )
            db.add(chunk)
            chunks.append(chunk)

    events = db.scalars(
        select(EvidenceEvent)
        .where(
            EvidenceEvent.case_id == case_id,
            EvidenceEvent.artifact_id == artifact_id,
        )
        .order_by(EvidenceEvent.created_at.asc())
    ).all()

    for event in events:
        summary = _event_summary(event)
        if not summary.strip():
            continue
        chunk = SearchChunk(
            case_id=case_id,
            artifact_id=artifact_id,
            event_id=event.id,
            chunk_text=summary,
            chunk_index=0,
            source_group=artifact.source_group or PROVENANCE_UNKNOWN,
            provenance_pointer=event.provenance_pointer,
            filter_metadata={
                "chunk_kind": "event_summary",
                "event_type": event.event_type,
                "event_id": str(event.id),
            },
            index_status=IndexStatus.pending.value,
        )
        db.add(chunk)
        chunks.append(chunk)

    db.commit()
    for chunk in chunks:
        db.refresh(chunk)
    return chunks


def build_chunks_for_case(
    db: Session,
    case_id: uuid.UUID,
    storage: StorageBackend,
) -> list[SearchChunk]:
    """Build pending chunks for every artifact in a case."""
    artifact_ids = db.scalars(
        select(Artifact.id).where(Artifact.case_id == case_id)
    ).all()
    all_chunks: list[SearchChunk] = []
    for artifact_id in artifact_ids:
        all_chunks.extend(build_chunks_for_artifact(db, case_id, artifact_id, storage))
    return all_chunks


def _split_text(text: str) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []
    if len(cleaned) <= _CHUNK_SIZE:
        return [cleaned]

    pieces: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + _CHUNK_SIZE)
        pieces.append(cleaned[start:end])
        if end >= len(cleaned):
            break
        start = max(end - _CHUNK_OVERLAP, start + 1)
    return pieces


def _event_summary(event: EvidenceEvent) -> str:
    parts = [
        event.title,
        event.description,
        event.original_timestamp_text,
        event.event_type,
    ]
    return " · ".join(part for part in parts if part)
