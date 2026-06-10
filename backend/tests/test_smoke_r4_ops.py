"""R4 smoke: operations summary for authorized operators."""

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

pytestmark = pytest.mark.smoke


@pytest.fixture
def smoke_client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_r4_operations_summary_smoke(
    smoke_client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(
        db_session,
        email="r4-ops@local.dev",
        role=UserRole.admin,
    )
    token = login_token(smoke_client, user)

    response = smoke_client.get("/operations/summary", headers=auth_header(token))
    assert response.status_code == 200
    payload = response.json()
    assert payload["cases_count"] >= 0
    assert payload["artifacts"]["failed"] >= 0
