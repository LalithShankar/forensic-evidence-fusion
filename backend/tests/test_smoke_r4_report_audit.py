"""R4 smoke: report draft generation and audit trail browse."""

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
    storage = LocalStorageBackend(tmp_path)

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_storage] = lambda: storage
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_r4_report_and_audit_smoke(
    smoke_client: TestClient,
    db_session: Session,
) -> None:
    client = smoke_client
    user = create_test_user(db_session, email="r4-report@local.dev")
    token = login_token(client, user)

    case = client.post(
        "/cases",
        headers=auth_header(token),
        json={"name": "R4 report smoke", "scenario_type": "financial_fraud"},
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

    claim = client.post(
        f"/cases/{case_id}/claims",
        headers=auth_header(token),
        json={"claim_text": "Alice confirmed the transfer on 2024-06-01."},
    )
    assert claim.status_code == 201
    claim_id = claim.json()["id"]

    resolve = client.post(
        f"/cases/{case_id}/claims/{claim_id}/resolve",
        headers=auth_header(token),
    )
    assert resolve.status_code == 200

    report = client.post(
        f"/cases/{case_id}/reports/generate",
        headers=auth_header(token),
    )
    assert report.status_code == 201
    content = report.json()["content_json"]
    section_keys = [section["key"] for section in content["sections"]]
    assert "timeline_summary" in section_keys
    assert "claim_matrix" in section_keys
    assert "limitations" in section_keys
    assert "source_appendix" in section_keys

    audit = client.get(f"/cases/{case_id}/audit", headers=auth_header(token))
    assert audit.status_code == 200
    actions = {item["action"] for item in audit.json()["items"]}
    assert "report.generated" in actions
    assert "case.created" in actions
