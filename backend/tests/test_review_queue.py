"""Review queue API tests."""

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
from app.models.artifact import Artifact, ArtifactStatus
from app.models.case import Case, CaseScenarioType
from app.models.case_membership import CaseAccessLevel, CaseMembership
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
        name="Review Case",
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


def test_review_queue_lists_low_confidence_artifacts(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)

    upload = client.post(
        f"/cases/{case.id}/artifacts/bulk-upload",
        headers=auth_header(token),
        files=[("files", ("mystery.bin", b"\x00", "application/octet-stream"))],
    )
    assert upload.status_code == 201
    artifact_id = upload.json()["results"][0]["artifact"]["id"]

    response = client.get(
        f"/cases/{case.id}/review-queue",
        headers=auth_header(token),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["artifact"]["id"] == artifact_id
    assert (
        "reason" in payload["items"][0]["review_reason"].lower()
        or payload["items"][0]["review_reason"]
    )


def test_review_queue_shows_blocked_artifact_notes(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)

    upload = client.post(
        f"/cases/{case.id}/artifacts/upload",
        headers=auth_header(token),
        files={"file": ("blocked.txt", b"data", "text/plain")},
    )
    assert upload.status_code == 201
    artifact = db_session.get(Artifact, uuid.UUID(upload.json()["id"]))
    assert artifact is not None
    artifact.status = ArtifactStatus.blocked
    artifact.blocker_notes = "Checksum mismatch detected"
    db_session.commit()

    response = client.get(
        f"/cases/{case.id}/review-queue",
        headers=auth_header(token),
    )
    assert response.status_code == 200
    item = response.json()["items"][0]
    assert "Checksum mismatch" in item["review_reason"]
    assert item["suggested_category"] == "Blocked"


def test_review_queue_empty_state(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)

    response = client.get(
        f"/cases/{case.id}/review-queue",
        headers=auth_header(token),
    )
    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["items"] == []


def test_approve_sets_ready_for_transformation(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)

    upload = client.post(
        f"/cases/{case.id}/artifacts/bulk-upload",
        headers=auth_header(token),
        files=[("files", ("mystery.bin", b"\x00", "application/octet-stream"))],
    )
    artifact_id = upload.json()["results"][0]["artifact"]["id"]

    response = client.patch(
        f"/cases/{case.id}/review-queue/{artifact_id}",
        headers=auth_header(token),
        json={"action": "approve"},
    )
    assert response.status_code == 200
    assert (
        response.json()["artifact"]["status"]
        == ArtifactStatus.ready_for_transformation.value
    )


def test_correct_metadata_updates_artifact(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)

    upload = client.post(
        f"/cases/{case.id}/artifacts/bulk-upload",
        headers=auth_header(token),
        files=[("files", ("mystery.bin", b"\x00", "application/octet-stream"))],
    )
    artifact_id = upload.json()["results"][0]["artifact"]["id"]

    response = client.patch(
        f"/cases/{case.id}/review-queue/{artifact_id}",
        headers=auth_header(token),
        json={
            "action": "correct",
            "source_group": "ThirdParty",
            "source_family": "WhatsApp",
            "artifact_type": "chat_export",
        },
    )
    assert response.status_code == 200
    artifact = response.json()["artifact"]
    assert artifact["source_group"] == "ThirdParty"
    assert artifact["source_family"] == "WhatsApp"
    assert artifact["artifact_type"] == "chat_export"


def test_preserve_only_excludes_from_transformation(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)

    upload = client.post(
        f"/cases/{case.id}/artifacts/bulk-upload",
        headers=auth_header(token),
        files=[("files", ("mystery.bin", b"\x00", "application/octet-stream"))],
    )
    artifact_id = upload.json()["results"][0]["artifact"]["id"]

    response = client.patch(
        f"/cases/{case.id}/review-queue/{artifact_id}",
        headers=auth_header(token),
        json={"action": "preserve_only"},
    )
    assert response.status_code == 200
    assert response.json()["artifact"]["status"] == ArtifactStatus.preserve_only.value
