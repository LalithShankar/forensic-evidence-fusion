"""Auth provider abstraction for local credentials and future Entra."""

from __future__ import annotations

import uuid
from typing import Protocol

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.user import User


class AuthProvider(Protocol):
    """Resolve authenticated users from credentials or token subject."""

    def authenticate(
        self,
        db: Session,
        email: str,
        password: str,
    ) -> User | None: ...

    def get_user_by_id(self, db: Session, user_id: uuid.UUID) -> User | None: ...

    def issue_token(self, user: User, settings: Settings) -> tuple[str, int]: ...


class LocalAuthProvider:
    """Local email/password auth backed by the users table."""

    def authenticate(
        self,
        db: Session,
        email: str,
        password: str,
    ) -> User | None:
        from app.services import auth_service

        return auth_service.authenticate(db, email, password)

    def get_user_by_id(self, db: Session, user_id: uuid.UUID) -> User | None:
        from app.services import auth_service

        return auth_service.get_user_by_id(db, user_id)

    def issue_token(self, user: User, settings: Settings) -> tuple[str, int]:
        from app.services import auth_service

        return auth_service.issue_token(user, settings)
