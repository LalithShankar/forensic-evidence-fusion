"""Tests for placeholder ORM models."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Artifact, AuditLog, Case, User


def test_metadata_loads_without_circular_imports() -> None:
    table_names = set(Base.metadata.tables.keys())

    assert table_names == {"users", "cases", "artifacts", "audit_log"}


def test_placeholder_models_have_ids_and_timestamps(db_session: Session) -> None:
    user = User()
    case = Case()
    db_session.add_all([user, case])
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(case)

    artifact = Artifact(case_id=case.id)
    db_session.add(artifact)
    db_session.commit()
    db_session.refresh(artifact)

    for entity in (user, case, artifact):
        assert isinstance(entity.id, uuid.UUID)
        assert entity.created_at is not None
        assert entity.updated_at is not None


def test_audit_log_model_has_required_columns() -> None:
    columns = {column.name for column in AuditLog.__table__.columns}

    assert columns == {
        "audit_id",
        "case_id",
        "user_id",
        "action",
        "object_type",
        "object_id",
        "before_json",
        "after_json",
        "timestamp",
        "reason",
    }
