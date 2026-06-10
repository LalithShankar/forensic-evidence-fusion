"""Tests for audit log write helper."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import AuditLog, Case, User
from app.services.audit_service import write_audit_log


def test_write_audit_log_persists_acting_user_and_target(db_session: Session) -> None:
    user = User(
        email="audit@local.dev",
        display_name="Audit User",
        password_hash=hash_password("DevPassword123!"),
    )
    case = Case()
    db_session.add_all([user, case])
    db_session.commit()

    target_id = uuid.uuid4()
    entry = write_audit_log(
        db_session,
        user_id=user.id,
        case_id=case.id,
        action="artifact.uploaded",
        object_type="artifact",
        object_id=target_id,
        before_json=None,
        after_json={"status": "received"},
        reason="simulated upload",
    )

    stored = db_session.get(AuditLog, entry.audit_id)
    assert stored is not None
    assert stored.user_id == user.id
    assert stored.case_id == case.id
    assert stored.object_id == target_id
    assert stored.action == "artifact.uploaded"
    assert stored.object_type == "artifact"


def test_simulated_audited_action_creates_exactly_one_row(db_session: Session) -> None:
    user = User(
        email="audit2@local.dev",
        display_name="Audit User 2",
        password_hash=hash_password("DevPassword123!"),
    )
    db_session.add(user)
    db_session.commit()

    write_audit_log(
        db_session,
        user_id=user.id,
        action="case.created",
        object_type="case",
        object_id=uuid.uuid4(),
    )

    rows = db_session.query(AuditLog).all()
    assert len(rows) == 1
    assert rows[0].action == "case.created"
    assert rows[0].timestamp is not None
