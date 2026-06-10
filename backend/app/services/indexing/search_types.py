"""Search hit returned from a case-scoped query."""

from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class SearchHit:
    """A retrieved chunk with relevance score."""

    chunk_id: uuid.UUID
    case_id: uuid.UUID
    artifact_id: uuid.UUID
    event_id: uuid.UUID | None
    chunk_text: str
    source_group: str
    provenance_pointer: str | None
    score: float
