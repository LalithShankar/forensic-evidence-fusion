"""Pydantic schemas for artifact review queue API."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.artifact import ArtifactPublic


class ReviewQueueItem(BaseModel):
    """Artifact surfaced in the review queue with context."""

    artifact: ArtifactPublic
    review_reason: str
    suggested_category: str


class ReviewQueueResponse(BaseModel):
    """List of artifacts needing manual review."""

    items: list[ReviewQueueItem]
    total: int


class ReviewActionInput(BaseModel):
    """Manual correction or approval for a review-queue artifact."""

    source_group: str | None = None
    source_family: str | None = None
    artifact_type: str | None = None
    action: str = Field(
        description="approve, preserve_only, or correct (metadata only)",
    )


class ReviewActionResponse(BaseModel):
    """Updated artifact after a review action."""

    artifact: ArtifactPublic
    message: str
