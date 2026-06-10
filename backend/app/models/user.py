"""Placeholder user model for future auth epics."""

from __future__ import annotations

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Minimal user record; expanded in Epic 5."""

    __tablename__ = "users"
