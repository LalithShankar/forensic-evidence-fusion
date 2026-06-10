"""R2 integration smoke: upload → review → transform → previews → canonical event."""

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


def test_r2_full_chain_smoke(smoke_client: TestClient, db_session: Session) -> None:
    """R2 gate: bulk upload through canonical evidence event."""
    client = smoke_client
    user = create_test_user(db_session, email="r2-smoke@local.dev")
    token = login_token(client, user)

    case = client.post(
        "/cases",
        headers=auth_header(token),
        json={"name": "R2 smoke", "scenario_type": "financial_fraud"},
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
                    b"sender,message,amount,date\nAlice,Transfer,50.00,2024-06-01\n",
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

    readable_views = client.get(
        f"/cases/{case_id}/artifacts/{artifact_id}/readable-views",
        headers=auth_header(token),
    )
    assert readable_views.status_code == 200
    assert len(readable_views.json()) >= 1
    view_id = readable_views.json()[0]["id"]
    readable_content = client.get(
        f"/cases/{case_id}/artifacts/{artifact_id}/readable-views/{view_id}/content",
        headers=auth_header(token),
    )
    assert readable_content.status_code == 200
    assert readable_content.json()["content"]

    datasets = client.get(
        f"/cases/{case_id}/artifacts/{artifact_id}/structured-datasets",
        headers=auth_header(token),
    )
    assert datasets.status_code == 200
    assert datasets.json()[0]["row_count"] == 1
    dataset_id = datasets.json()[0]["id"]
    preview = client.get(
        f"/cases/{case_id}/artifacts/{artifact_id}/structured-datasets/{dataset_id}/preview",
        headers=auth_header(token),
    )
    assert preview.status_code == 200
    assert preview.json()["preview_rows"]

    events = client.get(f"/cases/{case_id}/events", headers=auth_header(token))
    assert events.status_code == 200
    assert len(events.json()) >= 1
    event = events.json()[0]
    assert event["artifact_id"] == artifact_id
    assert event["event_type"] in {"message_sent", "transaction_observed"}
    assert event["provenance_pointer"]
