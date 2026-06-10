"""Platform-wide operations summary queries."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.artifact import Artifact, ArtifactStatus
from app.models.case import Case
from app.models.search_chunk import IndexStatus, SearchChunk
from app.models.transformation import TransformationRecord, TransformationStatus
from app.models.user import User, UserRole
from app.schemas.operations import (
    ArtifactStatusCounts,
    IndexStatusCounts,
    OperationsSummaryPublic,
    TransformationStatusCounts,
)


def get_operations_summary(db: Session, user: User) -> OperationsSummaryPublic | None:
    """Return global ops counts for admin or case_manager roles."""
    if user.role not in {UserRole.admin, UserRole.case_manager}:
        return None

    cases_count = db.scalar(select(func.count()).select_from(Case)) or 0

    artifact_rows = db.execute(
        select(Artifact.status, func.count()).group_by(Artifact.status)
    ).all()
    artifact_counts = ArtifactStatusCounts()
    for status, count in artifact_rows:
        if status == ArtifactStatus.failed:
            artifact_counts.failed = count
        elif status == ArtifactStatus.blocked:
            artifact_counts.blocked = count
        elif status == ArtifactStatus.needs_review:
            artifact_counts.needs_review = count
        else:
            artifact_counts.other += count

    transform_rows = db.execute(
        select(TransformationRecord.status, func.count()).group_by(
            TransformationRecord.status
        )
    ).all()
    transform_counts = TransformationStatusCounts()
    for status, count in transform_rows:
        if status == TransformationStatus.running.value:
            transform_counts.running = count
        elif status == TransformationStatus.failed.value:
            transform_counts.failed = count
        elif status == TransformationStatus.blocked.value:
            transform_counts.blocked = count
        elif status == TransformationStatus.completed.value:
            transform_counts.completed = count

    chunk_rows = db.execute(
        select(SearchChunk.index_status, func.count()).group_by(
            SearchChunk.index_status
        )
    ).all()
    chunk_counts = IndexStatusCounts()
    for status, count in chunk_rows:
        if status == IndexStatus.failed.value:
            chunk_counts.failed = count
        elif status == IndexStatus.pending.value:
            chunk_counts.pending = count
        elif status == IndexStatus.indexed.value:
            chunk_counts.indexed = count

    return OperationsSummaryPublic(
        cases_count=cases_count,
        artifacts=artifact_counts,
        transformations=transform_counts,
        search_chunks=chunk_counts,
    )
