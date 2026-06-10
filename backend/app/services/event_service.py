"""Timeline event listing and detail queries."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.auth_deps import check_case_access
from app.models.artifact import Artifact
from app.models.case_membership import CaseAccessLevel
from app.models.event import EvidenceEvent, ReviewStatus
from app.models.user import User
from app.schemas.event import EvidenceEventPublic


def event_to_public(
    event: EvidenceEvent,
    source_group: str | None = None,
) -> EvidenceEventPublic:
    """Build API payload with optional artifact source_group enrichment."""
    payload = EvidenceEventPublic.model_validate(event)
    if source_group is not None:
        return payload.model_copy(update={"source_group": source_group})
    return payload


def list_timeline_events(
    db: Session,
    user: User,
    case_id: uuid.UUID,
    *,
    event_type: str | None = None,
    source_group: str | None = None,
    review_status: ReviewStatus | None = None,
) -> list[EvidenceEventPublic] | None:
    """List case events chronologically with optional filters."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.viewer):
        return None

    stmt = (
        select(EvidenceEvent, Artifact.source_group)
        .join(Artifact, EvidenceEvent.artifact_id == Artifact.id)
        .where(EvidenceEvent.case_id == case_id)
    )

    if event_type is not None:
        stmt = stmt.where(EvidenceEvent.event_type == event_type)
    if source_group is not None:
        stmt = stmt.where(Artifact.source_group == source_group)
    if review_status is not None:
        stmt = stmt.where(EvidenceEvent.review_status == review_status.value)

    stmt = stmt.order_by(
        func.coalesce(
            EvidenceEvent.normalized_timestamp,
            EvidenceEvent.created_at,
        ).asc(),
        EvidenceEvent.created_at.asc(),
    )

    rows = db.execute(stmt).all()
    return [
        event_to_public(event, artifact_source_group)
        for event, artifact_source_group in rows
    ]


def get_timeline_event(
    db: Session,
    user: User,
    case_id: uuid.UUID,
    event_id: uuid.UUID,
) -> EvidenceEventPublic | None:
    """Return a single timeline event when the case and event are accessible."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.viewer):
        return None

    row = db.execute(
        select(EvidenceEvent, Artifact.source_group)
        .join(Artifact, EvidenceEvent.artifact_id == Artifact.id)
        .where(
            EvidenceEvent.id == event_id,
            EvidenceEvent.case_id == case_id,
        )
    ).first()
    if row is None:
        return None

    event, artifact_source_group = row
    return event_to_public(event, artifact_source_group)
