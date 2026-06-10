"""Case membership model for per-case access control."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


class CaseAccessLevel(enum.StrEnum):
    """Minimum access tiers for case operations."""

    viewer = "viewer"
    contributor = "contributor"
    manager = "manager"


ACCESS_LEVEL_RANK: dict[CaseAccessLevel, int] = {
    CaseAccessLevel.viewer: 1,
    CaseAccessLevel.contributor: 2,
    CaseAccessLevel.manager: 3,
}


class CaseMembership(UUIDPrimaryKeyMixin, Base):
    """Links a user to a case with an access level."""

    __tablename__ = "case_memberships"
    __table_args__ = (
        UniqueConstraint("case_id", "user_id", name="uq_case_memberships_case_user"),
        Index("ix_case_memberships_user_id", "user_id"),
    )

    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cases.id"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    access_level: Mapped[CaseAccessLevel] = mapped_column(
        Enum(CaseAccessLevel, name="case_access_level", native_enum=False),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
