"""Tests for placeholder ORM models."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Artifact, AuditLog, Case, User
from app.models.artifact import ArtifactStatus
from app.models.case import CaseScenarioType


def test_metadata_loads_without_circular_imports() -> None:
    table_names = set(Base.metadata.tables.keys())

    assert table_names == {
        "users",
        "cases",
        "case_memberships",
        "artifacts",
        "audit_log",
        "transformation_records",
        "readable_views",
        "structured_datasets",
        "entities",
        "evidence_events",
        "claims",
        "claim_resolutions",
        "analyst_notes",
        "reports",
        "search_chunks",
        "assistant_logs",
    }


def test_placeholder_models_have_ids_and_timestamps(db_session: Session) -> None:
    from app.core.security import hash_password

    user = User(
        email="user@local.dev",
        display_name="Placeholder User",
        password_hash=hash_password("DevPassword123!"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    case = Case(
        name="Placeholder Case",
        scenario_type=CaseScenarioType.general_investigation,
        created_by=user.id,
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(case)

    artifact = Artifact(
        case_id=case.id,
        original_filename="placeholder.bin",
        file_size_bytes=0,
        file_extension="bin",
        mime_type="application/octet-stream",
        status=ArtifactStatus.pending,
    )
    db_session.add(artifact)
    db_session.commit()
    db_session.refresh(artifact)

    for entity in (user, case, artifact):
        assert isinstance(entity.id, uuid.UUID)
        assert entity.created_at is not None
        assert entity.updated_at is not None

    assert user.email == "user@local.dev"
    assert user.role.value == "analyst"
    assert user.status.value == "active"


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
