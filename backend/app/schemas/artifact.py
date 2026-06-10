"""Pydantic schemas for artifact upload API."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.artifact import ArtifactStatus


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
    created_at: datetime
    updated_at: datetime


class ArtifactUploadError(BaseModel):
    """Error payload when upload cannot complete."""

    detail: str = Field(min_length=1)
