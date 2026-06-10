"""Assistant API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AssistantAskInput(BaseModel):
    """Question payload for the case assistant."""

    question: str = Field(min_length=1, max_length=4000)


class SourceReferencePublic(BaseModel):
    """Linked artifact/event/chunk reference."""

    chunk_id: uuid.UUID
    artifact_id: uuid.UUID
    event_id: uuid.UUID | None = None
    provenance_pointer: str | None = None
    source_group: str | None = None


class AssistantAnswerPublic(BaseModel):
    """Grounded assistant response."""

    answer_text: str
    confidence: float
    limitation_text: str | None = None
    insufficient_evidence: bool = False
    source_references: list[SourceReferencePublic] = Field(default_factory=list)
    log_id: uuid.UUID


class AssistantLogPublic(BaseModel):
    """Audit log entry for assistant Q&A."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    user_id: uuid.UUID
    question: str
    answer_text: str
    model_name: str
    confidence: float
    limitation_text: str | None
    insufficient_evidence: bool
    retrieval_chunk_ids: list[str] | None
    source_references: list[dict] | None
    created_at: datetime
