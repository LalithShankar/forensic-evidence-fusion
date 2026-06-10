"""Pydantic schemas for structured dataset API."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.structured_dataset import StructuredDatasetStatus


class StructuredDatasetPublic(BaseModel):
    """Structured dataset metadata exposed to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    artifact_id: uuid.UUID
    transformation_id: uuid.UUID | None
    dataset_type: str
    storage_path: str | None
    row_count: int | None
    schema_version: str
    confidence: float
    status: StructuredDatasetStatus
    error_notes: str | None
    created_at: datetime
    updated_at: datetime


class StructuredDatasetPreviewPublic(BaseModel):
    """Safe paginated preview of structured content."""

    dataset_id: uuid.UUID
    dataset_type: str
    confidence: float
    row_count: int | None
    preview_rows: list[dict[str, Any]] | None = None
    preview_json: str | None = None
    truncated: bool = False
    total_rows: int | None = None
