"""Shared FastAPI dependencies for API routers."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.services.indexing.search_backend import SearchBackend, get_search_backend
from app.services.storage_service import StorageBackend, get_storage_service


def get_storage(
    settings: Annotated[Settings, Depends(get_settings)],
) -> StorageBackend:
    """Return the active storage backend for the current environment."""
    return get_storage_service(settings)


def get_search(
    settings: Annotated[Settings, Depends(get_settings)],
) -> SearchBackend:
    """Return the active search backend for the current environment."""
    return get_search_backend(settings)
