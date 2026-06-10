"""Authentication API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.auth_deps import get_current_user, require_roles
from app.core.auth_provider import LocalAuthProvider
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.user import User, UserRole, UserStatus
from app.schemas.user import LoginRequest, LoginResponse, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])
auth_provider = LocalAuthProvider()


@router.post("/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LoginResponse:
    """Validate credentials and return a JWT access token."""
    user = auth_provider.authenticate(db, request.email, request.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if user.status == UserStatus.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disabled",
        )

    access_token, expires_in = auth_provider.issue_token(user, settings)
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
    )


@router.get("/me", response_model=UserPublic)
def read_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Return the authenticated user's public profile."""
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout() -> Response:
    """Stateless logout hook; frontend clears in-memory token."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/protected/ping")
def protected_ping(
    current_user: Annotated[
        User,
        Depends(require_roles(UserRole.analyst, UserRole.case_manager, UserRole.admin)),
    ],
) -> dict[str, str]:
    """Protected smoke route for auth verification."""
    return {"status": "ok", "user_id": str(current_user.id)}
