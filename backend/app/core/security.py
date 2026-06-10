"""Password hashing and JWT helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext  # type: ignore[import-untyped]

from app.core.config import Settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(password: str) -> str:
    """Return a bcrypt hash for the given plaintext password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(
    *,
    user_id: str,
    role: str,
    settings: Settings,
) -> tuple[str, int]:
    """Create a signed JWT access token and return token plus expiry seconds."""
    expire_minutes = settings.access_token_expire_minutes
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=expire_minutes)
    payload = {
        "sub": user_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
    return token, expire_minutes * 60


def decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
