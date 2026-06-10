"""Evidence events and normalization API routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_storage
from app.core.auth_deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.event import EvidenceEventPublic, NormalizeResponse
from app.services.normalization_service import list_case_events, normalize_artifact
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
) -> list[EvidenceEventPublic]:
    """List normalized evidence events for a case."""
    events = list_case_events(db, current_user, case_id)
    if events is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or inaccessible",
        )
    return [EvidenceEventPublic.model_validate(event) for event in events]


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
