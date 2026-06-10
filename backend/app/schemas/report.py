"""Report draft API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ReportSection(BaseModel):
    """One deterministic section in a report draft."""

    key: str
    title: str
    content: dict[str, Any]


class GenerateReportRequest(BaseModel):
    """Optional overrides when generating a report draft."""

    title: str | None = Field(default=None, max_length=256)


class ReportDraftPublic(BaseModel):
    """Persisted report draft returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    title: str
    status: str
    content_json: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
