"""FastAPI auth dependencies."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.auth_provider import LocalAuthProvider
from app.core.config import Settings, get_settings
from app.core.logging import bind_log_context
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole, UserStatus

security = HTTPBearer(auto_error=False)
auth_provider = LocalAuthProvider()


def check_case_access(
    user: User,
    case_id: uuid.UUID,
    min_level: str = "viewer",
) -> bool:
    """Permissive stub until Epic 6 implements case_memberships."""
    _ = case_id, min_level
    return user.status == UserStatus.active


def get_current_user(
    request: Request,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(security),
    ],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    """Resolve the authenticated user from a Bearer JWT."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = decode_access_token(credentials.credentials, settings)
        user_id = uuid.UUID(str(payload["sub"]))
    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        ) from None

    user = auth_provider.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    if user.status == UserStatus.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account disabled",
        )

    user_id = str(user.id)
    bind_log_context(user_id=user_id)
    request.state.user_id = user_id
    return user


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    """Return a dependency that enforces one of the given roles."""

    def _require_roles(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return _require_roles
