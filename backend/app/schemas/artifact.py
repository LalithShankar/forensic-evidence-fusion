"""Pydantic schemas for artifact upload API."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.artifact import PROVENANCE_UNKNOWN, ArtifactStatus


class ArtifactMetadataInput(BaseModel):
    """Optional provenance metadata supplied at upload or update."""

    source_group: str | None = None
    source_family: str | None = None
    artifact_type: str | None = None
    collection_method: str | None = None
    parser_class: str | None = None
    provenance_notes: str | None = None


def resolve_provenance_field(
    value: str | None,
    *,
    default: str = PROVENANCE_UNKNOWN,
) -> str:
    """Return a non-empty provenance string, applying the manifest default."""
    if value is None or not value.strip():
        return default
    return value.strip()


class ArtifactPublic(BaseModel):
    """Artifact metadata exposed to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    original_filename: str
    file_size_bytes: int
    file_extension: str
    mime_type: str
    uploaded_by: uuid.UUID | None
    uploaded_at: datetime | None
    content_hash: str | None
    status: ArtifactStatus
    source_group: str
    source_family: str
    artifact_type: str
    collection_method: str
    parser_class: str
    provenance_notes: str | None
    upload_batch_id: uuid.UUID | None = None
    classification_confidence: float | None = None
    suggested_source_group: str = PROVENANCE_UNKNOWN
    suggested_source_family: str = PROVENANCE_UNKNOWN
    suggested_artifact_type: str = PROVENANCE_UNKNOWN
    classification_reason: str | None = None
    blocker_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class BulkUploadItemPublic(BaseModel):
    """Per-file outcome from a bulk upload request."""

    filename: str
    artifact: ArtifactPublic | None = None
    error: str | None = None


class BulkUploadResponse(BaseModel):
    """Aggregate response for bulk artifact upload."""

    upload_batch_id: uuid.UUID
    results: list[BulkUploadItemPublic]
    succeeded_count: int
    failed_count: int


class ArtifactUploadError(BaseModel):
    """Error payload when upload cannot complete."""

    detail: str = Field(min_length=1)
