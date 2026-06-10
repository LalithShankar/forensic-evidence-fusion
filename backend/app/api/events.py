"""Evidence events and normalization API routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_storage
from app.core.auth_deps import get_current_user
from app.db.session import get_db
from app.models.event import ReviewStatus
from app.models.user import User
from app.schemas.event import EvidenceEventPublic, NormalizeResponse
from app.services.event_service import get_timeline_event, list_timeline_events
from app.services.normalization_service import normalize_artifact
from app.services.storage_service import StorageBackend

router = APIRouter(tags=["events"])


@router.get(
    "/cases/{case_id}/events",
    response_model=list[EvidenceEventPublic],
)
def get_case_events(
    case_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    event_type: Annotated[str | None, Query()] = None,
    source_group: Annotated[str | None, Query()] = None,
    review_status: Annotated[ReviewStatus | None, Query()] = None,
) -> list[EvidenceEventPublic]:
    """List normalized evidence events for a case in chronological order."""
    events = list_timeline_events(
        db,
        current_user,
        case_id,
        event_type=event_type,
        source_group=source_group,
        review_status=review_status,
    )
    if events is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or inaccessible",
        )
    return events


@router.get(
    "/cases/{case_id}/events/{event_id}",
    response_model=EvidenceEventPublic,
)
def get_case_event_detail(
    case_id: uuid.UUID,
    event_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> EvidenceEventPublic:
    """Return a single evidence event with provenance enrichment."""
    event = get_timeline_event(db, current_user, case_id, event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found or inaccessible",
        )
    return event


@router.post(
    "/cases/{case_id}/artifacts/{artifact_id}/normalize",
    response_model=NormalizeResponse,
    status_code=status.HTTP_201_CREATED,
)
def normalize_artifact_events(
    case_id: uuid.UUID,
    artifact_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> NormalizeResponse:
    """Normalize structured dataset rows into evidence events."""
    events = normalize_artifact(
        db,
        current_user,
        case_id,
        artifact_id,
        storage,
    )
    if events is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found or inaccessible",
        )
    public = [EvidenceEventPublic.model_validate(event) for event in events]
    return NormalizeResponse(events_created=len(public), events=public)
