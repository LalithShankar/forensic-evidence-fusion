"""Authentication service for local credentials."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import create_access_token, verify_password
from app.models.user import User


def authenticate(db: Session, email: str, password: str) -> User | None:
    """Validate email/password and return the user when credentials match."""
    normalized_email = email.strip().lower()
    user = db.scalar(select(User).where(User.email == normalized_email))
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    """Load a user by primary key."""
    return db.get(User, user_id)


def issue_token(user: User, settings: Settings) -> tuple[str, int]:
    """Issue a JWT access token for the given user."""
    return create_access_token(
        user_id=str(user.id),
        role=user.role.value,
        settings=settings,
    )
