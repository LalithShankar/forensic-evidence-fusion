"""Tests for auth dependency helpers."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.auth_deps import check_case_access
from app.core.security import hash_password
from app.models.case import Case, CaseScenarioType
from app.models.case_membership import CaseAccessLevel, CaseMembership
from app.models.user import User, UserRole, UserStatus


def _create_user(
    db_session: Session,
    *,
    email: str,
    role: UserRole = UserRole.analyst,
    status: UserStatus = UserStatus.active,
) -> User:
    user = User(
        email=email,
        display_name=email.split("@")[0],
        password_hash=hash_password("DevPassword123!"),
        role=role,
        status=status,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_check_case_access_grants_admin_all_cases(db_session: Session) -> None:
    admin = _create_user(db_session, email="admin@local.dev", role=UserRole.admin)

    assert (
        check_case_access(db_session, admin, uuid.uuid4(), CaseAccessLevel.manager)
        is True
    )


def test_check_case_access_rejects_disabled_users(db_session: Session) -> None:
    user = _create_user(
        db_session,
        email="disabled@local.dev",
        status=UserStatus.disabled,
    )

    assert (
        check_case_access(db_session, user, uuid.uuid4(), CaseAccessLevel.viewer)
        is False
    )


def test_check_case_access_enforces_membership_level(db_session: Session) -> None:
    owner = _create_user(db_session, email="owner@local.dev")
    viewer = _create_user(db_session, email="viewer@local.dev")
    case = Case(
        name="Membership Test",
        scenario_type=CaseScenarioType.general_investigation,
        created_by=owner.id,
    )
    db_session.add(case)
    db_session.flush()
    db_session.add(
        CaseMembership(
            case_id=case.id,
            user_id=viewer.id,
            access_level=CaseAccessLevel.viewer,
        )
    )
    db_session.commit()

    assert (
        check_case_access(db_session, viewer, case.id, CaseAccessLevel.viewer) is True
    )
    assert (
        check_case_access(db_session, viewer, case.id, CaseAccessLevel.contributor)
        is False
    )


def test_check_case_access_denies_without_membership(db_session: Session) -> None:
    owner = _create_user(db_session, email="owner@local.dev")
    outsider = _create_user(db_session, email="outsider@local.dev")
    case = Case(
        name="Private",
        scenario_type=CaseScenarioType.general_investigation,
        created_by=owner.id,
    )
    db_session.add(case)
    db_session.commit()

    assert (
        check_case_access(db_session, outsider, case.id, CaseAccessLevel.viewer)
        is False
    )
