"""Bulk upload API and classification tests."""

from __future__ import annotations

import uuid
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.artifacts import get_storage
from app.db.session import get_db
from app.main import app
from app.models.artifact import Artifact, ArtifactStatus
from app.models.case import Case, CaseScenarioType
from app.models.case_membership import CaseAccessLevel, CaseMembership
from app.services.storage_service import LocalStorageBackend, StorageError
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
        name="Bulk Case",
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


def test_bulk_upload_creates_artifact_per_file(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)

    response = client.post(
        f"/cases/{case.id}/artifacts/bulk-upload",
        headers=auth_header(token),
        files=[
            ("files", ("notes.txt", b"hello", "text/plain")),
            ("files", ("data.csv", b"a,b\n1,2", "text/csv")),
        ],
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["succeeded_count"] == 2
    assert payload["failed_count"] == 0
    assert payload["upload_batch_id"] is not None
    assert len(payload["results"]) == 2

    artifacts = db_session.scalars(select(Artifact)).all()
    assert len(artifacts) == 2
    batch_ids = {artifact.upload_batch_id for artifact in artifacts}
    assert len(batch_ids) == 1


def test_bulk_upload_partial_failure_preserves_successes(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)

    response = client.post(
        f"/cases/{case.id}/artifacts/bulk-upload",
        headers=auth_header(token),
        files=[
            ("files", ("good.csv", b"a,b\n1,2", "text/csv")),
            ("files", ("empty.txt", b"", "text/plain")),
        ],
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["succeeded_count"] == 1
    assert payload["failed_count"] == 1
    assert payload["results"][0]["artifact"] is not None
    assert payload["results"][1]["error"] is not None

    artifacts = db_session.scalars(select(Artifact)).all()
    assert len(artifacts) == 1
    assert artifacts[0].status != ArtifactStatus.failed
    assert artifacts[0].storage_path


def test_bulk_upload_denied_without_case_access(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = create_test_user(db_session, email="owner@local.dev")
    other = create_test_user(db_session, email="other@local.dev")
    case = create_case_for_user(db_session, owner.id)
    other_token = login_token(client, other)

    response = client.post(
        f"/cases/{case.id}/artifacts/bulk-upload",
        headers=auth_header(other_token),
        files=[("files", ("secret.txt", b"x", "text/plain"))],
    )

    assert response.status_code == 404


def test_whatsapp_filename_classified_with_confidence(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)

    response = client.post(
        f"/cases/{case.id}/artifacts/bulk-upload",
        headers=auth_header(token),
        files=[
            ("files", ("WhatsApp Chat with Alice.txt", b"msg", "text/plain")),
        ],
    )

    assert response.status_code == 201
    artifact_data = response.json()["results"][0]["artifact"]
    assert artifact_data["suggested_source_group"] == "ThirdParty"
    assert artifact_data["suggested_source_family"] == "WhatsApp"
    assert artifact_data["classification_confidence"] >= 0.7
    assert artifact_data["status"] == ArtifactStatus.preserved.value


def test_takeout_zip_classified_with_confidence(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)

    response = client.post(
        f"/cases/{case.id}/artifacts/bulk-upload",
        headers=auth_header(token),
        files=[
            ("files", ("takeout-20240101.zip", b"PK\x03\x04", "application/zip")),
        ],
    )

    assert response.status_code == 201
    artifact_data = response.json()["results"][0]["artifact"]
    assert artifact_data["suggested_source_group"] == "Google"
    assert artifact_data["suggested_source_family"] == "Takeout"
    assert artifact_data["classification_confidence"] >= 0.7


def test_low_confidence_marks_needs_review(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)

    response = client.post(
        f"/cases/{case.id}/artifacts/bulk-upload",
        headers=auth_header(token),
        files=[
            ("files", ("mystery_file.bin", b"\x00\x01", "application/octet-stream")),
        ],
    )

    assert response.status_code == 201
    artifact_data = response.json()["results"][0]["artifact"]
    assert artifact_data["status"] == ArtifactStatus.needs_review.value
    assert artifact_data["classification_confidence"] is not None
    assert artifact_data["classification_confidence"] < 0.7


def test_storage_failure_in_batch_reports_error(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)
    call_count = 0

    original = LocalStorageBackend.preserve_raw

    def flaky_preserve(
        self: LocalStorageBackend,
        *args: object,
        **kwargs: object,
    ) -> tuple[str, str]:
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise StorageError("disk full")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(LocalStorageBackend, "preserve_raw", flaky_preserve)

    response = client.post(
        f"/cases/{case.id}/artifacts/bulk-upload",
        headers=auth_header(token),
        files=[
            ("files", ("first.txt", b"ok", "text/plain")),
            ("files", ("second.txt", b"fail", "text/plain")),
        ],
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["succeeded_count"] == 1
    assert payload["failed_count"] == 1
