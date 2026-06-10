"""Case-scoped audit log read queries."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.auth_deps import check_case_access
from app.models.audit import AuditLog
from app.models.case_membership import CaseAccessLevel
from app.models.user import User


def list_case_audit_logs(
    db: Session,
    user: User,
    case_id: uuid.UUID,
    *,
    action: str | None = None,
    object_type: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[AuditLog], int] | None:
    """Return paginated audit rows for a case when the user has viewer access."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.viewer):
        return None

    filters = [AuditLog.case_id == case_id]
    if action is not None:
        filters.append(AuditLog.action == action)
    if object_type is not None:
        filters.append(AuditLog.object_type == object_type)
    if since is not None:
        filters.append(AuditLog.timestamp >= since)
    if until is not None:
        filters.append(AuditLog.timestamp <= until)

    total = db.scalar(select(func.count()).select_from(AuditLog).where(*filters)) or 0

    stmt = (
        select(AuditLog)
        .where(*filters)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
        .offset(offset)
    )
    items = list(db.scalars(stmt).all())
    return items, total
