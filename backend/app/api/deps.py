"""Shared FastAPI dependencies for API routers."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.services.storage_service import StorageBackend, get_storage_service


def get_storage(
    settings: Annotated[Settings, Depends(get_settings)],
) -> StorageBackend:
    """Return the active storage backend for the current environment."""
    return get_storage_service(settings)
