"""Audit log write helper for action traceability."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def write_audit_log(
    db: Session,
    *,
    user_id: uuid.UUID,
    action: str,
    object_type: str,
    object_id: uuid.UUID,
    case_id: uuid.UUID | None = None,
    before_json: dict[str, Any] | None = None,
    after_json: dict[str, Any] | None = None,
    reason: str | None = None,
) -> AuditLog:
    """Persist a single audit log entry for the acting user and target object."""
    entry = AuditLog(
        user_id=user_id,
        case_id=case_id,
        action=action,
        object_type=object_type,
        object_id=object_id,
        before_json=before_json,
        after_json=after_json,
        reason=reason,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
