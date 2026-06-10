"""Pydantic schemas for case artifact manifest API."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.artifact import ArtifactStatus


class ArtifactManifestEntry(BaseModel):
    """Stable manifest record for one artifact."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    storage_path: str
    status: ArtifactStatus
    content_hash: str | None
    source_group: str
    source_family: str
    artifact_type: str
    collection_method: str
    parser_class: str
    provenance_notes: str | None
    uploaded_at: datetime | None
    uploaded_by: uuid.UUID | None
    original_filename: str
    file_extension: str
    mime_type: str
    file_size_bytes: int


class CaseArtifactManifest(BaseModel):
    """Manifest of all artifacts in a case."""

    case_id: uuid.UUID
    artifact_count: int = Field(ge=0)
    artifacts: list[ArtifactManifestEntry]
