"""Artifact upload and listing API routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth_deps import get_current_user
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.artifact import ArtifactStatus
from app.models.user import User
from app.schemas.artifact import (
    ArtifactMetadataInput,
    ArtifactPublic,
    BulkUploadResponse,
)
from app.schemas.manifest import CaseArtifactManifest
from app.services import artifact_service
from app.services.bulk_upload_service import (
    build_bulk_upload_response,
    bulk_upload_artifacts,
)
from app.services.manifest_service import build_case_manifest
from app.services.storage_service import StorageBackend, get_storage_service

router = APIRouter(tags=["artifacts"])


def get_storage(
    settings: Annotated[Settings, Depends(get_settings)],
) -> StorageBackend:
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
    storage: Annotated[StorageBackend, Depends(get_storage)],
    source_group: Annotated[str | None, Form()] = None,
    source_family: Annotated[str | None, Form()] = None,
    artifact_type: Annotated[str | None, Form()] = None,
    collection_method: Annotated[str | None, Form()] = None,
    parser_class: Annotated[str | None, Form()] = None,
    provenance_notes: Annotated[str | None, Form()] = None,
) -> ArtifactPublic:
    """Upload one evidence file to a case and preserve raw bytes locally."""
    content = await file.read()
    filename = file.filename or ""
    metadata = ArtifactMetadataInput(
        source_group=source_group,
        source_family=source_family,
        artifact_type=artifact_type,
        collection_method=collection_method,
        parser_class=parser_class,
        provenance_notes=provenance_notes,
    )

    try:
        artifact = artifact_service.upload_artifact(
            db,
            current_user,
            case_id,
            original_filename=filename,
            mime_type=file.content_type,
            content=content,
            storage=storage,
            metadata=metadata,
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


@router.post(
    "/cases/{case_id}/artifacts/bulk-upload",
    response_model=BulkUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def bulk_upload(
    case_id: uuid.UUID,
    files: Annotated[list[UploadFile], File(...)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
    source_group: Annotated[str | None, Form()] = None,
    source_family: Annotated[str | None, Form()] = None,
    artifact_type: Annotated[str | None, Form()] = None,
    collection_method: Annotated[str | None, Form()] = None,
    parser_class: Annotated[str | None, Form()] = None,
    provenance_notes: Annotated[str | None, Form()] = None,
) -> BulkUploadResponse:
    """Upload multiple evidence files; preserve successes and report failures."""
    metadata = ArtifactMetadataInput(
        source_group=source_group,
        source_family=source_family,
        artifact_type=artifact_type,
        collection_method=collection_method,
        parser_class=parser_class,
        provenance_notes=provenance_notes,
    )

    file_payloads: list[tuple[str, str | None, bytes]] = []
    for upload in files:
        content = await upload.read()
        file_payloads.append((upload.filename or "", upload.content_type, content))

    try:
        result = bulk_upload_artifacts(
            db,
            current_user,
            case_id,
            files=file_payloads,
            storage=storage,
            metadata=metadata,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    return build_bulk_upload_response(result)


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
    "/cases/{case_id}/artifacts/manifest",
    response_model=CaseArtifactManifest,
)
def get_case_artifact_manifest(
    case_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CaseArtifactManifest:
    """Return a manifest of all artifacts for an accessible case."""
    from app.services.case_service import get_case_for_user

    if get_case_for_user(db, current_user, case_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    artifacts = artifact_service.list_artifacts_for_case(db, current_user, case_id)
    return build_case_manifest(case_id, artifacts)


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
