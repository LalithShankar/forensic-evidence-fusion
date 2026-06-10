"""User-facing auth schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole, UserStatus


class UserPublic(BaseModel):
    """Public user profile without sensitive fields."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    display_name: str
    role: UserRole
    status: UserStatus


class LoginRequest(BaseModel):
    """Credentials submitted to the login endpoint."""

    email: EmailStr
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    """Successful login payload."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
