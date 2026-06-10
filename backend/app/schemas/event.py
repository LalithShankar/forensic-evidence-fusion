"""Pydantic schemas for evidence events API."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.event import ReviewStatus


class EvidenceEventPublic(BaseModel):
    """Normalized evidence event exposed to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    artifact_id: uuid.UUID
    transformation_id: uuid.UUID | None
    structured_dataset_id: uuid.UUID | None
    event_type: str
    event_subtype: str | None
    original_timestamp_text: str | None
    normalized_timestamp: datetime | None
    title: str | None
    description: str | None
    payload_json: dict[str, Any] | None
    source_confidence: float
    provenance_pointer: str | None
    review_status: ReviewStatus
    source_group: str | None = None
    created_at: datetime
    updated_at: datetime


class NormalizeResponse(BaseModel):
    """Result of normalization for an artifact."""

    events_created: int
    events: list[EvidenceEventPublic]
