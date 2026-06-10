"""R3 smoke: timeline filters, claim create, deterministic resolution."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.artifacts import get_storage
from app.db.session import get_db
from app.main import app
from app.models.artifact import ArtifactStatus
from app.models.transformation import TransformationStatus
from app.services.storage_service import LocalStorageBackend
from tests.test_auth import auth_header, create_test_user
from tests.test_cases import login_token

pytestmark = pytest.mark.smoke


@pytest.fixture
def smoke_client(
    db_session: Session,
    tmp_path: Path,
) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    storage = LocalStorageBackend(tmp_path)

    def override_get_storage() -> LocalStorageBackend:
        return storage

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_storage] = override_get_storage
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_r3_timeline_filters_claim_and_resolution_smoke(
    smoke_client: TestClient,
    db_session: Session,
) -> None:
    client = smoke_client
    user = create_test_user(db_session, email="r3-smoke@local.dev")
    token = login_token(client, user)

    case = client.post(
        "/cases",
        headers=auth_header(token),
        json={"name": "R3 smoke", "scenario_type": "financial_fraud"},
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
                    b"sender,message,amount,date\n"
                    b"Alice,Transfer confirmed,50.00,2024-06-01\n",
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

    events = client.get(f"/cases/{case_id}/events", headers=auth_header(token))
    assert events.status_code == 200
    assert len(events.json()) >= 1

    filtered = client.get(
        f"/cases/{case_id}/events",
        headers=auth_header(token),
        params={"event_type": events.json()[0]["event_type"]},
    )
    assert filtered.status_code == 200
    assert len(filtered.json()) >= 1

    claim = client.post(
        f"/cases/{case_id}/claims",
        headers=auth_header(token),
        json={
            "claim_text": "Alice confirmed the transfer on 2024-06-01",
            "claimant": "Alice",
            "claimed_time_text": "2024-06-01",
            "claimed_people": ["Alice"],
            "claim_source": "interview",
        },
    )
    assert claim.status_code == 201
    claim_id = claim.json()["id"]

    resolution = client.post(
        f"/cases/{case_id}/claims/{claim_id}/resolve",
        headers=auth_header(token),
    )
    assert resolution.status_code == 200
    body = resolution.json()
    assert body["result_label"]
    assert body["support_score"] is not None
    assert body["supporting_event_ids"] or body["unresolved_reason"]

    fetched = client.get(
        f"/cases/{case_id}/claims/{claim_id}/resolution",
        headers=auth_header(token),
    )
    assert fetched.status_code == 200
    assert fetched.json()["id"] == body["id"]
