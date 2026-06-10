"""Review queue API for low-confidence and blocked artifacts."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth_deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.artifact import ArtifactPublic
from app.schemas.review import (
    ReviewActionInput,
    ReviewActionResponse,
    ReviewQueueItem,
    ReviewQueueResponse,
)
from app.services import review_service

router = APIRouter(tags=["review"])


@router.get(
    "/cases/{case_id}/review-queue",
    response_model=ReviewQueueResponse,
)
def get_review_queue(
    case_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ReviewQueueResponse:
    """List artifacts needing manual review for an accessible case."""
    from app.services.case_service import get_case_for_user

    if get_case_for_user(db, current_user, case_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    items = review_service.list_review_queue(db, current_user, case_id)
    if items is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    queue_items = [
        ReviewQueueItem(
            artifact=ArtifactPublic.model_validate(item.artifact),
            review_reason=item.review_reason,
            suggested_category=item.suggested_category,
        )
        for item in items
    ]
    return ReviewQueueResponse(items=queue_items, total=len(queue_items))


@router.patch(
    "/cases/{case_id}/review-queue/{artifact_id}",
    response_model=ReviewActionResponse,
)
def patch_review_item(
    case_id: uuid.UUID,
    artifact_id: uuid.UUID,
    body: ReviewActionInput,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ReviewActionResponse:
    """Correct classification metadata or approve a review-queue artifact."""
    try:
        artifact = review_service.apply_review_action(
            db,
            current_user,
            case_id,
            artifact_id,
            body,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found or not eligible for review",
        )

    action = body.action.strip().lower()
    if action == "preserve_only":
        message = "Artifact marked preserve-only."
    elif action == "approve":
        message = "Artifact approved for transformation."
    else:
        message = "Artifact metadata updated."

    return ReviewActionResponse(
        artifact=ArtifactPublic.model_validate(artifact),
        message=message,
    )
