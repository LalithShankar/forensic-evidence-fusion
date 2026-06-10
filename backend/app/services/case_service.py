"""Case business logic and membership-aware queries."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth_deps import check_case_access
from app.models.case import Case
from app.models.case_membership import CaseAccessLevel, CaseMembership
from app.models.user import User, UserRole
from app.schemas.case import CaseCreate, CaseUpdate
from app.services.audit_service import write_audit_log


def list_accessible_cases(db: Session, user: User) -> list[Case]:
    """Return cases the user may view based on membership or admin role."""
    if user.role == UserRole.admin:
        return list(db.scalars(select(Case).order_by(Case.created_at.desc())))

    stmt = (
        select(Case)
        .join(CaseMembership, CaseMembership.case_id == Case.id)
        .where(CaseMembership.user_id == user.id)
        .order_by(Case.created_at.desc())
    )
    return list(db.scalars(stmt))


def get_case_for_user(db: Session, user: User, case_id: uuid.UUID) -> Case | None:
    """Return a case when the user has viewer access; otherwise None."""
    case = db.get(Case, case_id)
    if case is None:
        return None
    if not check_case_access(db, user, case_id, CaseAccessLevel.viewer):
        return None
    return case


def create_case(db: Session, user: User, payload: CaseCreate) -> Case:
    """Create a case, add creator as manager, and audit the action."""
    case = Case(
        name=payload.name,
        description=payload.description,
        scenario_type=payload.scenario_type,
        date_range_start=payload.date_range_start,
        date_range_end=payload.date_range_end,
        created_by=user.id,
    )
    db.add(case)
    db.flush()

    membership = CaseMembership(
        case_id=case.id,
        user_id=user.id,
        access_level=CaseAccessLevel.manager,
    )
    db.add(membership)
    db.commit()
    db.refresh(case)

    write_audit_log(
        db,
        user_id=user.id,
        action="case.created",
        object_type="case",
        object_id=case.id,
        case_id=case.id,
        after_json=_case_snapshot(case),
    )
    return case


def update_case(
    db: Session,
    user: User,
    case_id: uuid.UUID,
    payload: CaseUpdate,
) -> Case | None:
    """Update allowed fields when the user has contributor access."""
    case = get_case_for_user(db, user, case_id)
    if case is None:
        return None
    if not check_case_access(db, user, case_id, CaseAccessLevel.contributor):
        return None

    before = _case_snapshot(case)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(case, field, value)
    case.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(case)

    write_audit_log(
        db,
        user_id=user.id,
        action="case.updated",
        object_type="case",
        object_id=case.id,
        case_id=case.id,
        before_json=before,
        after_json=_case_snapshot(case),
    )
    return case


def _case_snapshot(case: Case) -> dict[str, Any]:
    return {
        "id": str(case.id),
        "name": case.name,
        "description": case.description,
        "scenario_type": case.scenario_type.value,
        "date_range_start": (
            case.date_range_start.isoformat() if case.date_range_start else None
        ),
        "date_range_end": (
            case.date_range_end.isoformat() if case.date_range_end else None
        ),
        "created_by": str(case.created_by),
    }
