"""Indexing API schemas."""

from __future__ import annotations

from pydantic import BaseModel


class IndexStatusPublic(BaseModel):
    """Chunk indexing counts for a case."""

    pending: int
    indexed: int
    failed: int
    total: int
