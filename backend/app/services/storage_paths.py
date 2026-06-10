"""Object key conventions for raw, readable, and structured storage namespaces."""

from __future__ import annotations

import uuid
from enum import StrEnum
from pathlib import Path


class StorageNamespace(StrEnum):
    """Logical storage namespaces for artifact outputs."""

    raw = "raw"
    readable = "readable"
    structured = "structured"


class InvalidFilenameError(ValueError):
    """Raised when a filename cannot be sanitized to a safe basename."""


def sanitize_filename(filename: str) -> str:
    """Return basename-only filename; reject empty results."""
    safe_name = Path(filename).name
    if not safe_name:
        raise InvalidFilenameError("Invalid filename")
    return safe_name


def build_object_key(
    case_id: uuid.UUID,
    artifact_id: uuid.UUID,
    filename: str,
    namespace: StorageNamespace,
) -> str:
    """Build a stable object key for local filesystem or blob storage."""
    safe_name = sanitize_filename(filename)
    return f"{namespace.value}/{case_id}/{artifact_id}/{safe_name}"
