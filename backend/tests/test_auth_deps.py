"""Tests for auth dependency helpers."""

from __future__ import annotations

import uuid

from app.core.auth_deps import check_case_access
from app.models.user import User, UserRole, UserStatus


def test_check_case_access_stub_allows_active_users() -> None:
    user = User(
        email="analyst@local.dev",
        display_name="Analyst",
        password_hash="hash",
        role=UserRole.analyst,
        status=UserStatus.active,
    )

    assert check_case_access(user, uuid.uuid4(), "viewer") is True


def test_check_case_access_stub_rejects_disabled_users() -> None:
    user = User(
        email="disabled@local.dev",
        display_name="Disabled",
        password_hash="hash",
        role=UserRole.analyst,
        status=UserStatus.disabled,
    )

    assert check_case_access(user, uuid.uuid4(), "viewer") is False
