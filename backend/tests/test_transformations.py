"""Transformation pipeline API tests."""

from __future__ import annotations

import uuid
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.artifacts import get_storage
from app.db.session import get_db
from app.main import app
from app.models.artifact import ArtifactStatus
from app.models.case import Case, CaseScenarioType
from app.models.case_membership import CaseAccessLevel, CaseMembership
from app.models.transformation import TransformationStage, TransformationStatus
from app.services.storage_service import LocalStorageBackend
from tests.test_auth import auth_header, create_test_user
from tests.test_cases import login_token


@pytest.fixture
def client(
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


def create_case_for_user(db_session: Session, user_id: uuid.UUID) -> Case:
    case = Case(
        name="Transform Case",
        scenario_type=CaseScenarioType.general_investigation,
        created_by=user_id,
    )
    db_session.add(case)
    db_session.flush()
    db_session.add(
        CaseMembership(
            case_id=case.id,
            user_id=user_id,
            access_level=CaseAccessLevel.manager,
        )
    )
    db_session.commit()
    db_session.refresh(case)
    return case


def upload_and_approve_csv(
    client: TestClient,
    case_id: uuid.UUID,
    token: str,
) -> str:
    upload = client.post(
        f"/cases/{case_id}/artifacts/bulk-upload",
        headers=auth_header(token),
        files=[("files", ("ledger.csv", b"a,b\n1,2", "text/csv"))],
    )
    assert upload.status_code == 201
    artifact_id = upload.json()["results"][0]["artifact"]["id"]
    approve = client.patch(
        f"/cases/{case_id}/review-queue/{artifact_id}",
        headers=auth_header(token),
        json={"action": "approve"},
    )
    assert approve.status_code == 200
    return artifact_id


def test_start_transformation_creates_record_with_stages(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)
    artifact_id = upload_and_approve_csv(client, case.id, token)

    response = client.post(
        f"/cases/{case.id}/artifacts/{artifact_id}/transformations/start",
        headers=auth_header(token),
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["record"]["artifact_id"] == artifact_id
    assert payload["record"]["status"] == TransformationStatus.completed.value
    stage_values = [stage for stage in payload["stages_completed"]]
    assert TransformationStage.structured_generated.value in stage_values
    assert payload["record"]["readable_path"]
    assert payload["record"]["structured_path"]

    readable_file = tmp_path / payload["record"]["readable_path"]
    structured_file = tmp_path / payload["record"]["structured_path"]
    assert readable_file.exists()
    assert structured_file.exists()


def test_transformation_idempotent_for_same_artifact(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)
    artifact_id = upload_and_approve_csv(client, case.id, token)

    first = client.post(
        f"/cases/{case.id}/artifacts/{artifact_id}/transformations/start",
        headers=auth_header(token),
    )
    second = client.post(
        f"/cases/{case.id}/artifacts/{artifact_id}/transformations/start",
        headers=auth_header(token),
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["record"]["id"] == second.json()["record"]["id"]


def test_transformation_blocked_stores_failure_notes(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)

    upload = client.post(
        f"/cases/{case.id}/artifacts/bulk-upload",
        headers=auth_header(token),
        files=[("files", ("mystery.bin", b"\x00\x01", "application/octet-stream"))],
    )
    artifact_id = upload.json()["results"][0]["artifact"]["id"]
    approve = client.patch(
        f"/cases/{case.id}/review-queue/{artifact_id}",
        headers=auth_header(token),
        json={
            "action": "approve",
            "source_group": "Generic",
            "source_family": "Binary",
            "artifact_type": "unknown",
        },
    )
    assert approve.status_code == 200

    # Force ready status for unsupported format test
    from app.models.artifact import Artifact

    artifact = db_session.get(Artifact, uuid.UUID(artifact_id))
    assert artifact is not None
    artifact.status = ArtifactStatus.ready_for_transformation
    db_session.commit()

    response = client.post(
        f"/cases/{case.id}/artifacts/{artifact_id}/transformations/start",
        headers=auth_header(token),
    )
    assert response.status_code == 201
    record = response.json()["record"]
    assert record["status"] == TransformationStatus.blocked.value
    assert record["failure_notes"] is not None
    assert record["current_stage"] == TransformationStage.blocked.value


def upload_and_approve(
    client: TestClient,
    case_id: uuid.UUID,
    token: str,
    *,
    filename: str,
    content: bytes,
    mime: str,
) -> str:
    upload = client.post(
        f"/cases/{case_id}/artifacts/bulk-upload",
        headers=auth_header(token),
        files=[("files", (filename, content, mime))],
    )
    assert upload.status_code == 201
    artifact_id = upload.json()["results"][0]["artifact"]["id"]
    approve = client.patch(
        f"/cases/{case_id}/review-queue/{artifact_id}",
        headers=auth_header(token),
        json={"action": "approve"},
    )
    assert approve.status_code == 200
    return artifact_id


def test_json_transformation_generates_readable_and_structured(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)
    artifact_id = upload_and_approve(
        client,
        case.id,
        token,
        filename="events.json",
        content=b'{"event":"login","user":"alice"}',
        mime="application/json",
    )

    response = client.post(
        f"/cases/{case.id}/artifacts/{artifact_id}/transformations/start",
        headers=auth_header(token),
    )
    assert response.status_code == 201
    record = response.json()["record"]
    assert record["status"] == TransformationStatus.completed.value
    assert (tmp_path / record["readable_path"]).exists()
    assert (tmp_path / record["structured_path"]).exists()


def test_pdf_transformation_generates_text_preview(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)
    artifact_id = upload_and_approve(
        client,
        case.id,
        token,
        filename="memo.pdf",
        content=b"%PDF-1.4 BT (Hello PDF evidence) Tj ET",
        mime="application/pdf",
    )

    response = client.post(
        f"/cases/{case.id}/artifacts/{artifact_id}/transformations/start",
        headers=auth_header(token),
    )
    assert response.status_code == 201
    record = response.json()["record"]
    assert record["status"] == TransformationStatus.completed.value
    readable = (tmp_path / record["readable_path"]).read_text()
    assert "Hello PDF evidence" in readable


def test_transformation_rejects_unready_artifact(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)

    upload = client.post(
        f"/cases/{case.id}/artifacts/bulk-upload",
        headers=auth_header(token),
        files=[("files", ("ledger.csv", b"a,b\n1,2", "text/csv"))],
    )
    artifact_id = upload.json()["results"][0]["artifact"]["id"]

    # Not approved → still preserved, not ready_for_transformation.
    response = client.post(
        f"/cases/{case.id}/artifacts/{artifact_id}/transformations/start",
        headers=auth_header(token),
    )
    assert response.status_code == 404


def test_get_latest_transformation_status(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)
    artifact_id = upload_and_approve_csv(client, case.id, token)

    client.post(
        f"/cases/{case.id}/artifacts/{artifact_id}/transformations/start",
        headers=auth_header(token),
    )

    latest = client.get(
        f"/cases/{case.id}/artifacts/{artifact_id}/transformations/latest",
        headers=auth_header(token),
    )
    assert latest.status_code == 200
    assert latest.json()["artifact_id"] == artifact_id
