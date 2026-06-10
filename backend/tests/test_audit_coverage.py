"""Verify representative platform actions emit audit rows."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.artifacts import get_storage
from app.db.session import get_db
from app.main import app
from app.models.artifact import ArtifactStatus
from app.models.audit import AuditLog
from app.models.transformation import TransformationStatus
from app.services.storage_service import LocalStorageBackend
from tests.test_auth import auth_header, create_test_user
from tests.test_cases import login_token


@pytest.fixture
def client(
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


def _audit_actions(db_session: Session, case_id: str) -> set[str]:
    import uuid

    rows = db_session.scalars(
        select(AuditLog.action).where(AuditLog.case_id == uuid.UUID(case_id))
    ).all()
    return set(rows)


def test_audit_coverage_for_representative_actions(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session, email="audit-coverage@local.dev")
    token = login_token(client, user)

    case = client.post(
        "/cases",
        headers=auth_header(token),
        json={"name": "Coverage case", "scenario_type": "financial_fraud"},
    )
    assert case.status_code == 201
    case_id = case.json()["id"]

    update = client.patch(
        f"/cases/{case_id}",
        headers=auth_header(token),
        json={"description": "Updated for audit coverage"},
    )
    assert update.status_code == 200

    bulk = client.post(
        f"/cases/{case_id}/artifacts/bulk-upload",
        headers=auth_header(token),
        files=[
            (
                "files",
                (
                    "payments.csv",
                    b"sender,message,amount,date\nAlice,Transfer,50,2024-06-01\n",
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
        json={"claim_text": "Alice transferred funds on 2024-06-01."},
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
        json={"title": "Coverage report"},
    )
    assert report.status_code == 201

    actions = _audit_actions(db_session, case_id)
    required = {
        "case.created",
        "case.updated",
        "artifact.uploaded",
        "claim.created",
        "claim.resolved",
        "report.generated",
    }
    missing = required - actions
    assert not missing, f"Missing audit actions: {sorted(missing)}"
