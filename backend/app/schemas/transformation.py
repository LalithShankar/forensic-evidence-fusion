"""Pydantic schemas for transformation pipeline API."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.transformation import TransformationStage, TransformationStatus


class TransformationRecordPublic(BaseModel):
    """Transformation run exposed to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    artifact_id: uuid.UUID
    case_id: uuid.UUID
    current_stage: str
    status: TransformationStatus
    idempotency_key: str
    readable_path: str | None
    structured_path: str | None
    failure_notes: str | None
    limitation_notes: str | None
    created_at: datetime
    updated_at: datetime


class TransformationStartResponse(BaseModel):
    """Response after starting or resuming a transformation."""

    record: TransformationRecordPublic
    stages_completed: list[TransformationStage]
