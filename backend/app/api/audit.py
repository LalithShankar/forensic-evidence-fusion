"""Case audit trail read API routes."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth_deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.audit import AuditLogListResponse, AuditLogPublic
from app.services.audit_query_service import list_case_audit_logs

router = APIRouter(tags=["audit"])


@router.get(
    "/cases/{case_id}/audit",
    response_model=AuditLogListResponse,
)
def get_case_audit(
    case_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    action: Annotated[str | None, Query()] = None,
    object_type: Annotated[str | None, Query()] = None,
    since: Annotated[datetime | None, Query()] = None,
    until: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AuditLogListResponse:
    """List audit entries for a case with optional filters."""
    result = list_case_audit_logs(
        db,
        current_user,
        case_id,
        action=action,
        object_type=object_type,
        since=since,
        until=until,
        limit=limit,
        offset=offset,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or inaccessible",
        )

    items, total = result
    return AuditLogListResponse(
        items=[AuditLogPublic.from_audit_row(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )
