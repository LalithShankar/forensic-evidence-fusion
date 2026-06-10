"""Pydantic schemas for readable preview API."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.readable_view import ReadableViewStatus, ReadableViewType


class ReadableViewPublic(BaseModel):
    """Readable view metadata exposed to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    artifact_id: uuid.UUID
    transformation_id: uuid.UUID | None
    view_type: ReadableViewType
    storage_path: str | None
    status: ReadableViewStatus
    error_notes: str | None
    created_at: datetime
    updated_at: datetime


class ReadableViewContentPublic(BaseModel):
    """Safe text or JSON preview content."""

    view_id: uuid.UUID
    view_type: ReadableViewType
    content_type: str
    content: str
    truncated: bool = False
