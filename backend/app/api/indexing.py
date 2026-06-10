"""Case indexing API routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_search, get_storage
from app.core.auth_deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.indexing import IndexStatusPublic
from app.services.indexing.indexing_service import get_index_status, index_case
from app.services.indexing.search_backend import SearchBackend
from app.services.storage_service import StorageBackend

router = APIRouter(tags=["indexing"])


@router.post(
    "/cases/{case_id}/index",
    response_model=IndexStatusPublic,
)
def post_index_case(
    case_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    storage: Annotated[StorageBackend, Depends(get_storage)],
    search_backend: Annotated[SearchBackend, Depends(get_search)],
) -> IndexStatusPublic:
    """Build chunks and push them to the search backend."""
    summary = index_case(db, current_user, case_id, storage, search_backend)
    if summary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or inaccessible",
        )
    return IndexStatusPublic.model_validate(summary.__dict__)


@router.get(
    "/cases/{case_id}/index/status",
    response_model=IndexStatusPublic,
)
def get_case_index_status(
    case_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> IndexStatusPublic:
    """Return indexing status counts for a case."""
    summary = get_index_status(db, current_user, case_id)
    if summary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or inaccessible",
        )
    return IndexStatusPublic.model_validate(summary.__dict__)
