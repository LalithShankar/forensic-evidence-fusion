"""Artifact upload and listing API routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth_deps import get_current_user
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.artifact import ArtifactStatus
from app.models.user import User
from app.schemas.artifact import ArtifactPublic
from app.services import artifact_service
from app.services.storage_service import LocalStorageService, get_storage_service

router = APIRouter(tags=["artifacts"])


def get_storage(
    settings: Annotated[Settings, Depends(get_settings)],
) -> LocalStorageService:
    return get_storage_service(settings)


@router.post(
    "/cases/{case_id}/artifacts/upload",
    response_model=ArtifactPublic,
    status_code=status.HTTP_201_CREATED,
)
async def upload_artifact(
    case_id: uuid.UUID,
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[LocalStorageService, Depends(get_storage)],
) -> ArtifactPublic:
    """Upload one evidence file to a case and preserve raw bytes locally."""
    content = await file.read()
    filename = file.filename or ""

    try:
        artifact = artifact_service.upload_artifact(
            db,
            current_user,
            case_id,
            original_filename=filename,
            mime_type=file.content_type,
            content=content,
            storage=storage,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    if artifact.status == ArtifactStatus.failed:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Artifact preservation failed",
        )

    return ArtifactPublic.model_validate(artifact)


@router.get("/cases/{case_id}/artifacts", response_model=list[ArtifactPublic])
def list_artifacts(
    case_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ArtifactPublic]:
    """List artifacts for a case the user can view."""
    from app.services.case_service import get_case_for_user

    if get_case_for_user(db, current_user, case_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    artifacts = artifact_service.list_artifacts_for_case(db, current_user, case_id)
    return [ArtifactPublic.model_validate(item) for item in artifacts]


@router.get(
    "/cases/{case_id}/artifacts/{artifact_id}",
    response_model=ArtifactPublic,
)
def get_artifact(
    case_id: uuid.UUID,
    artifact_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ArtifactPublic:
    """Return artifact metadata for an accessible case."""
    artifact = artifact_service.get_artifact_for_user(
        db,
        current_user,
        case_id,
        artifact_id,
    )
    if artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found",
        )
    return ArtifactPublic.model_validate(artifact)
