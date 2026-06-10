"""Transformation pipeline API routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.artifacts import get_storage
from app.core.auth_deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.transformation import (
    TransformationRecordPublic,
    TransformationStartResponse,
)
from app.services.storage_service import StorageBackend
from app.services.transformation_pipeline import (
    get_latest_transformation,
    start_transformation,
)

router = APIRouter(tags=["transformations"])


@router.post(
    "/cases/{case_id}/artifacts/{artifact_id}/transformations/start",
    response_model=TransformationStartResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_artifact_transformation(
    case_id: uuid.UUID,
    artifact_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> TransformationStartResponse:
    """Start synchronous transformation for a ready artifact."""
    result = start_transformation(
        db,
        current_user,
        case_id,
        artifact_id,
        storage,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found or not ready for transformation",
        )

    record, stages = result
    return TransformationStartResponse(
        record=TransformationRecordPublic.model_validate(record),
        stages_completed=stages,
    )


@router.get(
    "/cases/{case_id}/artifacts/{artifact_id}/transformations/latest",
    response_model=TransformationRecordPublic,
)
def get_latest_artifact_transformation(
    case_id: uuid.UUID,
    artifact_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TransformationRecordPublic:
    """Return the latest transformation status for an artifact."""
    record = get_latest_transformation(db, current_user, case_id, artifact_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transformation record not found",
        )
    return TransformationRecordPublic.model_validate(record)
