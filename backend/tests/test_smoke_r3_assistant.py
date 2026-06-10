"""R3 smoke: index case and ask grounded assistant."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_llm, get_search, get_storage
from app.db.session import get_db
from app.main import app
from app.models.artifact import ArtifactStatus
from app.models.transformation import TransformationStatus
from app.services.indexing.search_backend import InMemorySearchBackend
from app.services.llm_backend import MockLLMBackend
from app.services.storage_service import LocalStorageBackend
from tests.test_auth import auth_header, create_test_user
from tests.test_cases import login_token

pytestmark = pytest.mark.smoke


@pytest.fixture
def smoke_client(
    db_session: Session,
    tmp_path: Path,
) -> Generator[TestClient, None, None]:
    storage = LocalStorageBackend(tmp_path)
    search_backend = InMemorySearchBackend()
    llm_backend = MockLLMBackend()

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_storage] = lambda: storage
    app.dependency_overrides[get_search] = lambda: search_backend
    app.dependency_overrides[get_llm] = lambda: llm_backend
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_r3_assistant_smoke(
    smoke_client: TestClient,
    db_session: Session,
) -> None:
    client = smoke_client
    user = create_test_user(db_session, email="r3-assistant@local.dev")
    token = login_token(client, user)

    case = client.post(
        "/cases",
        headers=auth_header(token),
        json={"name": "Assistant smoke", "scenario_type": "financial_fraud"},
    )
    assert case.status_code == 201
    case_id = case.json()["id"]

    bulk = client.post(
        f"/cases/{case_id}/artifacts/bulk-upload",
        headers=auth_header(token),
        files=[
            (
                "files",
                (
                    "payments.csv",
                    (
                        b"sender,message,amount,date\n"
                        b"Alice,Transfer confirmed,50.00,2024-06-01\n"
                    ),
                    "text/csv",
                ),
            ),
        ],
    )
    assert bulk.status_code == 201
    artifact_id = bulk.json()["results"][0]["artifact"]["id"]

    review = client.patch(
        f"/cases/{case_id}/review-queue/{artifact_id}",
        headers=auth_header(token),
        json={"action": "approve"},
    )
    assert (
        review.json()["artifact"]["status"]
        == ArtifactStatus.ready_for_transformation.value
    )

    transform = client.post(
        f"/cases/{case_id}/artifacts/{artifact_id}/transformations/start",
        headers=auth_header(token),
    )
    assert transform.status_code == 201
    assert transform.json()["record"]["status"] == TransformationStatus.completed.value

    index = client.post(f"/cases/{case_id}/index", headers=auth_header(token))
    assert index.status_code == 200
    assert index.json()["indexed"] >= 1

    ask = client.post(
        f"/cases/{case_id}/assistant/ask",
        headers=auth_header(token),
        json={"question": "What did Alice transfer?"},
    )
    assert ask.status_code == 200
    body = ask.json()
    assert body["answer_text"]
    assert body["insufficient_evidence"] is False or body["source_references"]
    if not body["insufficient_evidence"]:
        assert body["source_references"]

    logs = client.get(
        f"/cases/{case_id}/assistant/logs",
        headers=auth_header(token),
    )
    assert logs.status_code == 200
    assert len(logs.json()) >= 1
