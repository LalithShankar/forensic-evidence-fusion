"""Placeholder case model for future case management epics."""

from __future__ import annotations

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Case(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Minimal case record; expanded in Epic 6."""

    __tablename__ = "cases"
