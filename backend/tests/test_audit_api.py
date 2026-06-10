"""Audit trail read API tests."""

from __future__ import annotations

import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.main import app
from app.services.audit_service import write_audit_log
from tests.test_auth import auth_header, create_test_user
from tests.test_cases import login_token


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_list_case_audit_logs_with_filters(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session, email="audit-api@local.dev")
    token = login_token(client, user)

    case = client.post(
        "/cases",
        headers=auth_header(token),
        json={"name": "Audit API case", "scenario_type": "financial_fraud"},
    )
    assert case.status_code == 201
    case_id = case.json()["id"]

    case_uuid = uuid.UUID(case_id)
    write_audit_log(
        db_session,
        user_id=user.id,
        action="artifact.uploaded",
        object_type="artifact",
        object_id=case_uuid,
        case_id=case_uuid,
    )

    response = client.get(
        f"/cases/{case_id}/audit",
        headers=auth_header(token),
        params={"action": "case.created"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 1
    assert all(item["action"] == "case.created" for item in payload["items"])


def test_audit_list_is_case_isolated(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session, email="audit-isolate@local.dev")
    token = login_token(client, user)

    case_a = client.post(
        "/cases",
        headers=auth_header(token),
        json={"name": "Case A", "scenario_type": "financial_fraud"},
    ).json()
    case_b = client.post(
        "/cases",
        headers=auth_header(token),
        json={"name": "Case B", "scenario_type": "financial_fraud"},
    ).json()

    response = client.get(
        f"/cases/{case_a['id']}/audit",
        headers=auth_header(token),
    )
    assert response.status_code == 200
    case_ids = {item["case_id"] for item in response.json()["items"]}
    assert case_b["id"] not in case_ids


def test_audit_entries_redact_sensitive_json(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session, email="audit-redact@local.dev")
    token = login_token(client, user)

    case = client.post(
        "/cases",
        headers=auth_header(token),
        json={"name": "Redact case", "scenario_type": "financial_fraud"},
    ).json()

    case_uuid = uuid.UUID(case["id"])
    write_audit_log(
        db_session,
        user_id=user.id,
        action="config.updated",
        object_type="config",
        object_id=case_uuid,
        case_id=case_uuid,
        after_json={"api_key": "super-secret", "name": "visible"},
    )

    response = client.get(
        f"/cases/{case['id']}/audit",
        headers=auth_header(token),
        params={"action": "config.updated"},
    )
    assert response.status_code == 200
    entry = response.json()["items"][0]
    assert entry["after_json"]["api_key"] == "<redacted>"
    assert entry["after_json"]["name"] == "visible"
