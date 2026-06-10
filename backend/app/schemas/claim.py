"""Claim API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ClaimCreate(BaseModel):
    """Payload for entering a narrative claim."""

    claim_text: str = Field(min_length=1)
    claimant: str | None = Field(default=None, max_length=256)
    claimed_time_text: str | None = Field(default=None, max_length=256)
    claimed_people: list[str] | None = None
    claim_source: str | None = Field(default=None, max_length=64)


class ClaimPublic(BaseModel):
    """Claim returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    claim_text: str
    claim_type: str
    claimant: str | None
    claimed_time_text: str | None
    claimed_time_normalized: datetime | None
    claimed_people: list[str] | None
    claim_source: str | None
    claim_source_artifact_id: uuid.UUID | None
    parse_confidence: float
    created_by: uuid.UUID | None
    status: str
    created_at: datetime
    updated_at: datetime


class ClaimResolutionPublic(BaseModel):
    """Deterministic claim resolution verdict."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    claim_id: uuid.UUID
    resolution_status: str
    result_label: str | None
    support_score: float | None
    contradiction_score: float | None
    supporting_event_ids: list[str] | None
    contradicting_event_ids: list[str] | None
    unresolved_reason: str | None
    resolution_notes: str | None
    created_at: datetime
    updated_at: datetime
