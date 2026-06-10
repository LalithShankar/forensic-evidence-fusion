"""User model with role and status for auth and future RBAC."""

from __future__ import annotations

import enum

from sqlalchemy import Enum, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class UserRole(enum.StrEnum):
    """MVP roles; full enforcement deferred to Epic 6+."""

    analyst = "analyst"
    case_manager = "case_manager"
    admin = "admin"


class UserStatus(enum.StrEnum):
    """Account lifecycle status."""

    active = "active"
    disabled = "disabled"


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Local auth user record."""

    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email", "email", unique=True),
        Index("ix_users_status", "status"),
    )

    email: Mapped[str] = mapped_column(String(320), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False),
        nullable=False,
        default=UserRole.analyst,
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status", native_enum=False),
        nullable=False,
        default=UserStatus.active,
    )
