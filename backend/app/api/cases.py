"""Case management API routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth_deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.case import CaseCreate, CasePublic, CaseUpdate
from app.services import case_service

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", response_model=CasePublic, status_code=status.HTTP_201_CREATED)
def create_case(
    payload: CaseCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CasePublic:
    """Create a case and grant the creator manager membership."""
    case = case_service.create_case(db, current_user, payload)
    return CasePublic.model_validate(case)


@router.get("", response_model=list[CasePublic])
def list_cases(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[CasePublic]:
    """List cases the current user is allowed to access."""
    cases = case_service.list_accessible_cases(db, current_user)
    return [CasePublic.model_validate(case) for case in cases]


@router.get("/{case_id}", response_model=CasePublic)
def get_case(
    case_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CasePublic:
    """Return case details when the user has viewer access."""
    case = case_service.get_case_for_user(db, current_user, case_id)
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    return CasePublic.model_validate(case)


@router.patch("/{case_id}", response_model=CasePublic)
def update_case(
    case_id: uuid.UUID,
    payload: CaseUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CasePublic:
    """Update case metadata when the user has contributor access."""
    case = case_service.update_case(db, current_user, case_id, payload)
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    return CasePublic.model_validate(case)
