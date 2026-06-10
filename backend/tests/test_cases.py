"""Case management API tests."""

from __future__ import annotations

import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.main import app
from app.models.audit import AuditLog
from app.models.case import Case, CaseScenarioType
from app.models.case_membership import CaseAccessLevel, CaseMembership
from app.models.user import User, UserRole
from tests.test_auth import auth_header, create_test_user


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """API client with database session override."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def login_token(
    client: TestClient,
    user: User,
    password: str = "DevPassword123!",
) -> str:
    response = client.post(
        "/auth/login",
        json={"email": user.email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_create_case_sets_created_by_and_timestamps(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    token = login_token(client, user)

    response = client.post(
        "/cases",
        headers=auth_header(token),
        json={
            "name": "Insider Review",
            "description": "Q1 trading review",
            "scenario_type": "insider_trading",
            "date_range_start": "2026-01-01",
            "date_range_end": "2026-03-31",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["name"] == "Insider Review"
    assert payload["created_by"] == str(user.id)
    assert payload["created_at"] is not None
    assert payload["updated_at"] is not None

    case_uuid = uuid.UUID(payload["id"])
    membership = db_session.scalar(
        select(CaseMembership).where(
            CaseMembership.case_id == case_uuid,
            CaseMembership.user_id == user.id,
        )
    )
    assert membership is not None
    assert membership.access_level == CaseAccessLevel.manager


def test_list_cases_filtered_by_membership(
    client: TestClient,
    db_session: Session,
) -> None:
    user_a = create_test_user(db_session, email="a@local.dev")
    user_b = create_test_user(db_session, email="b@local.dev")
    token_a = login_token(client, user_a)

    created = client.post(
        "/cases",
        headers=auth_header(token_a),
        json={
            "name": "Private Case",
            "scenario_type": "financial_fraud",
        },
    )
    assert created.status_code == 201

    list_a = client.get("/cases", headers=auth_header(token_a))
    assert list_a.status_code == 200
    assert len(list_a.json()) == 1

    token_b = login_token(client, user_b)
    list_b = client.get("/cases", headers=auth_header(token_b))
    assert list_b.status_code == 200
    assert list_b.json() == []


def test_create_case_invalid_input_returns_422(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    token = login_token(client, user)

    response = client.post(
        "/cases",
        headers=auth_header(token),
        json={"name": "", "scenario_type": "financial_fraud"},
    )

    assert response.status_code == 422


def test_case_routes_require_authentication(client: TestClient) -> None:
    assert client.get("/cases").status_code == 401
    unauth_create = client.post(
        "/cases",
        json={"name": "X", "scenario_type": "financial_fraud"},
    )
    assert unauth_create.status_code == 401


def test_get_case_returns_details(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    token = login_token(client, user)
    created = client.post(
        "/cases",
        headers=auth_header(token),
        json={
            "name": "Detail Case",
            "description": "Notes",
            "scenario_type": "money_laundering",
            "date_range_start": "2025-06-01",
            "date_range_end": "2025-12-31",
        },
    )
    case_id = created.json()["id"]

    response = client.get(f"/cases/{case_id}", headers=auth_header(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Detail Case"
    assert payload["description"] == "Notes"
    assert payload["scenario_type"] == "money_laundering"
    assert payload["date_range_start"] == "2025-06-01"
    assert payload["date_range_end"] == "2025-12-31"


def test_patch_case_updates_fields_and_updated_at(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    token = login_token(client, user)
    created = client.post(
        "/cases",
        headers=auth_header(token),
        json={"name": "Before", "scenario_type": "general_investigation"},
    )
    case_id = created.json()["id"]
    original_updated_at = created.json()["updated_at"]

    response = client.patch(
        f"/cases/{case_id}",
        headers=auth_header(token),
        json={
            "name": "After",
            "description": "Updated notes",
            "scenario_type": "financial_fraud",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "After"
    assert payload["description"] == "Updated notes"
    assert payload["scenario_type"] == "financial_fraud"
    assert payload["updated_at"] >= original_updated_at

    refetched = client.get(f"/cases/{case_id}", headers=auth_header(token))
    assert refetched.json()["name"] == "After"


def test_get_missing_or_inaccessible_case_returns_404(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = create_test_user(db_session, email="owner@local.dev")
    outsider = create_test_user(db_session, email="outsider@local.dev")
    owner_token = login_token(client, owner)
    outsider_token = login_token(client, outsider)

    created = client.post(
        "/cases",
        headers=auth_header(owner_token),
        json={"name": "Hidden", "scenario_type": "general_investigation"},
    )
    case_id = created.json()["id"]

    missing = client.get(
        "/cases/00000000-0000-0000-0000-000000000099",
        headers=auth_header(outsider_token),
    )
    forbidden = client.get(f"/cases/{case_id}", headers=auth_header(outsider_token))

    assert missing.status_code == 404
    assert forbidden.status_code == 404
    assert missing.json()["detail"] == "Case not found"
    assert forbidden.json()["detail"] == "Case not found"


def test_viewer_cannot_patch_case(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = create_test_user(db_session, email="owner@local.dev")
    viewer = create_test_user(db_session, email="viewer@local.dev")
    case = Case(
        name="Shared",
        scenario_type=CaseScenarioType.general_investigation,
        created_by=owner.id,
    )
    db_session.add(case)
    db_session.flush()
    db_session.add_all(
        [
            CaseMembership(
                case_id=case.id,
                user_id=owner.id,
                access_level=CaseAccessLevel.manager,
            ),
            CaseMembership(
                case_id=case.id,
                user_id=viewer.id,
                access_level=CaseAccessLevel.viewer,
            ),
        ]
    )
    db_session.commit()

    viewer_token = login_token(client, viewer)
    response = client.patch(
        f"/cases/{case.id}",
        headers=auth_header(viewer_token),
        json={"name": "Blocked"},
    )

    assert response.status_code == 404


def test_create_case_writes_audit_log(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    token = login_token(client, user)

    response = client.post(
        "/cases",
        headers=auth_header(token),
        json={"name": "Audited", "scenario_type": "general_investigation"},
    )

    assert response.status_code == 201
    case_id = uuid.UUID(response.json()["id"])

    entry = db_session.scalar(
        select(AuditLog).where(
            AuditLog.object_id == case_id,
            AuditLog.action == "case.created",
        )
    )
    assert entry is not None
    assert entry.user_id == user.id


def test_admin_can_list_all_cases_without_membership(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = create_test_user(db_session, email="owner@local.dev")
    admin = create_test_user(
        db_session,
        email="admin@local.dev",
        role=UserRole.admin,
    )
    owner_token = login_token(client, owner)
    admin_token = login_token(client, admin)

    client.post(
        "/cases",
        headers=auth_header(owner_token),
        json={"name": "Owner Case", "scenario_type": "general_investigation"},
    )

    response = client.get("/cases", headers=auth_header(admin_token))

    assert response.status_code == 200
    assert len(response.json()) == 1
