"""Operations summary API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ArtifactStatusCounts(BaseModel):
    """Artifact counts grouped by status."""

    failed: int = 0
    blocked: int = 0
    needs_review: int = 0
    other: int = 0


class TransformationStatusCounts(BaseModel):
    """Transformation run counts."""

    running: int = 0
    failed: int = 0
    blocked: int = 0
    completed: int = 0


class IndexStatusCounts(BaseModel):
    """Search chunk index status counts."""

    failed: int = 0
    pending: int = 0
    indexed: int = 0


class OperationsSummaryPublic(BaseModel):
    """Global platform operations snapshot."""

    cases_count: int = Field(ge=0)
    artifacts: ArtifactStatusCounts
    transformations: TransformationStatusCounts
    search_chunks: IndexStatusCounts
