"""Case model for investigation workspaces."""

from __future__ import annotations

import enum
import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class CaseScenarioType(enum.StrEnum):
    """Supported investigation scenario categories."""

    general_investigation = "general_investigation"
    financial_fraud = "financial_fraud"
    insider_trading = "insider_trading"
    money_laundering = "money_laundering"


class Case(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Investigation case metadata."""

    __tablename__ = "cases"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    scenario_type: Mapped[CaseScenarioType] = mapped_column(
        Enum(CaseScenarioType, name="case_scenario_type", native_enum=False),
        nullable=False,
    )
    date_range_start: Mapped[date | None] = mapped_column(Date(), nullable=True)
    date_range_end: Mapped[date | None] = mapped_column(Date(), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
