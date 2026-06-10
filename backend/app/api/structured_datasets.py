"""Structured dataset API routes."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_storage
from app.core.auth_deps import get_current_user
from app.db.session import get_db
from app.models.structured_dataset import StructuredDataset
from app.models.user import User
from app.schemas.structured_dataset import (
    StructuredDatasetPreviewPublic,
    StructuredDatasetPublic,
)
from app.services.structured_dataset_service import (
    get_structured_dataset_preview,
    list_structured_datasets,
)
from app.services.storage_service import StorageBackend

router = APIRouter(tags=["structured-datasets"])


@router.get(
    "/cases/{case_id}/artifacts/{artifact_id}/structured-datasets",
    response_model=list[StructuredDatasetPublic],
)
def list_artifact_structured_datasets(
    case_id: uuid.UUID,
    artifact_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[StructuredDatasetPublic]:
    """List structured datasets for an artifact."""
    datasets = list_structured_datasets(db, current_user, case_id, artifact_id)
    if datasets is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found or inaccessible",
        )
    return [StructuredDatasetPublic.model_validate(item) for item in datasets]


@router.get(
    "/cases/{case_id}/artifacts/{artifact_id}/structured-datasets/{dataset_id}/preview",
    response_model=StructuredDatasetPreviewPublic,
)
def get_artifact_structured_dataset_preview(
    case_id: uuid.UUID,
    artifact_id: uuid.UUID,
    dataset_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
) -> StructuredDatasetPreviewPublic:
    """Return safe preview rows or JSON for a structured dataset."""
    result = get_structured_dataset_preview(
        db,
        current_user,
        case_id,
        artifact_id,
        dataset_id,
        storage,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Structured dataset not found or inaccessible",
        )

    dataset: StructuredDataset = result["dataset"]  # type: ignore[assignment]
    preview_rows: list[dict[str, Any]] | None = result.get("preview_rows")  # type: ignore[assignment]
    preview_json: str | None = result.get("preview_json")  # type: ignore[assignment]
    truncated: bool = bool(result.get("truncated"))
    total_rows: int | None = result.get("total_rows")  # type: ignore[assignment]

    return StructuredDatasetPreviewPublic(
        dataset_id=dataset.id,
        dataset_type=dataset.dataset_type,
        confidence=dataset.confidence,
        row_count=dataset.row_count,
        preview_rows=preview_rows,
        preview_json=preview_json,
        truncated=truncated,
        total_rows=total_rows,
    )
