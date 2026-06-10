"""Narrative claims and resolution API routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth_deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.claim import ClaimCreate, ClaimPublic, ClaimResolutionPublic
from app.services.claim_resolution_service import get_claim_resolution, resolve_claim
from app.services.claim_service import create_claim, get_claim, list_claims

router = APIRouter(tags=["claims"])


@router.post(
    "/cases/{case_id}/claims",
    response_model=ClaimPublic,
    status_code=status.HTTP_201_CREATED,
)
def post_claim(
    case_id: uuid.UUID,
    payload: ClaimCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ClaimPublic:
    """Create a narrative claim for contributor+ users."""
    claim = create_claim(db, current_user, case_id, payload)
    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or inaccessible",
        )
    return ClaimPublic.model_validate(claim)


@router.get(
    "/cases/{case_id}/claims",
    response_model=list[ClaimPublic],
)
def get_claims(
    case_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ClaimPublic]:
    """List claims for a case."""
    claims = list_claims(db, current_user, case_id)
    if claims is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or inaccessible",
        )
    return [ClaimPublic.model_validate(claim) for claim in claims]


@router.get(
    "/cases/{case_id}/claims/{claim_id}",
    response_model=ClaimPublic,
)
def get_claim_detail(
    case_id: uuid.UUID,
    claim_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ClaimPublic:
    """Return a single claim."""
    claim = get_claim(db, current_user, case_id, claim_id)
    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found or inaccessible",
        )
    return ClaimPublic.model_validate(claim)


@router.post(
    "/cases/{case_id}/claims/{claim_id}/resolve",
    response_model=ClaimResolutionPublic,
)
def post_resolve_claim(
    case_id: uuid.UUID,
    claim_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ClaimResolutionPublic:
    """Run deterministic claim resolution."""
    resolution = resolve_claim(db, current_user, case_id, claim_id)
    if resolution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found or inaccessible",
        )
    return ClaimResolutionPublic.model_validate(resolution)


@router.get(
    "/cases/{case_id}/claims/{claim_id}/resolution",
    response_model=ClaimResolutionPublic,
)
def get_claim_resolution_detail(
    case_id: uuid.UUID,
    claim_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ClaimResolutionPublic:
    """Return stored resolution for a claim."""
    resolution = get_claim_resolution(db, current_user, case_id, claim_id)
    if resolution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resolution not found or inaccessible",
        )
    return ClaimResolutionPublic.model_validate(resolution)
