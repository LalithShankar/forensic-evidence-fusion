"""Platform operations summary API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth_deps import require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.operations import OperationsSummaryPublic
from app.services.operations_service import get_operations_summary

router = APIRouter(tags=["operations"])


@router.get(
    "/operations/summary",
    response_model=OperationsSummaryPublic,
)
def get_ops_summary(
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.admin, UserRole.case_manager)),
    ],
    db: Annotated[Session, Depends(get_db)],
) -> OperationsSummaryPublic:
    """Return global processing backlog counts for platform operators."""
    summary = get_operations_summary(db, current_user)
    if summary is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return summary
