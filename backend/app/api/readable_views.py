"""Readable preview API routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_storage
from app.core.auth_deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.readable_view import (
    ReadableViewContentPublic,
    ReadableViewPublic,
)
from app.services.readable_view_service import (
    get_readable_view_content,
    list_readable_views,
)
from app.services.storage_service import StorageBackend

router = APIRouter(tags=["readable-views"])


@router.get(
    "/cases/{case_id}/artifacts/{artifact_id}/readable-views",
    response_model=list[ReadableViewPublic],
)
def list_artifact_readable_views(
    case_id: uuid.UUID,
    artifact_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ReadableViewPublic]:
    """List readable previews for an artifact."""
    views = list_readable_views(db, current_user, case_id, artifact_id)
    if views is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found or inaccessible",
        )
    return [ReadableViewPublic.model_validate(view) for view in views]


@router.get(
    "/cases/{case_id}/artifacts/{artifact_id}/readable-views/{view_id}/content",
    response_model=ReadableViewContentPublic,
)
def get_artifact_readable_view_content(
    case_id: uuid.UUID,
    artifact_id: uuid.UUID,
    view_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> ReadableViewContentPublic:
    """Return safe preview text for a readable view."""
    result = get_readable_view_content(
        db,
        current_user,
        case_id,
        artifact_id,
        view_id,
        storage,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Readable view not found or inaccessible",
        )

    view, content_type, content, truncated = result
    return ReadableViewContentPublic(
        view_id=view.id,
        view_type=view.view_type,  # type: ignore[arg-type]
        content_type=content_type,
        content=content,
        truncated=truncated,
    )
