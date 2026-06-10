"""Case API schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.case import CaseScenarioType


class CaseCreate(BaseModel):
    """Payload for creating a new case."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    scenario_type: CaseScenarioType
    date_range_start: date | None = None
    date_range_end: date | None = None


class CaseUpdate(BaseModel):
    """Payload for updating case metadata."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    scenario_type: CaseScenarioType | None = None
    date_range_start: date | None = None
    date_range_end: date | None = None


class CasePublic(BaseModel):
    """Case record returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    scenario_type: CaseScenarioType
    date_range_start: date | None
    date_range_end: date | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
