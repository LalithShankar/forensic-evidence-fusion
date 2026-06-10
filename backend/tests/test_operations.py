"""Operations summary API tests."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.main import app
from app.models.user import UserRole
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


def test_operations_summary_for_case_manager(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(
        db_session,
        email="ops-manager@local.dev",
        role=UserRole.case_manager,
    )
    token = login_token(client, user)

    response = client.get("/operations/summary", headers=auth_header(token))
    assert response.status_code == 200
    payload = response.json()
    assert "cases_count" in payload
    assert "artifacts" in payload
    assert "transformations" in payload
    assert "search_chunks" in payload


def test_operations_summary_denied_for_analyst(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session, email="ops-analyst@local.dev")
    token = login_token(client, user)

    response = client.get("/operations/summary", headers=auth_header(token))
    assert response.status_code == 403
