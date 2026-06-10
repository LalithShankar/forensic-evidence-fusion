"""Artifact upload and preservation API tests."""

from __future__ import annotations

import uuid
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.artifacts import get_storage
from app.db.session import get_db
from app.main import app
from app.models.artifact import Artifact, ArtifactStatus
from app.models.case import Case, CaseScenarioType
from app.models.case_membership import CaseAccessLevel, CaseMembership
from app.services.storage_service import LocalStorageService, StorageError
from tests.test_auth import auth_header, create_test_user
from tests.test_cases import login_token


@pytest.fixture
def client(
    db_session: Session,
    tmp_path: Path,
) -> Generator[TestClient, None, None]:
    """API client with database and local storage overrides."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    storage = LocalStorageService(tmp_path)

    def override_get_storage() -> LocalStorageService:
        return storage

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_storage] = override_get_storage
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def create_case_for_user(db_session: Session, user_id: uuid.UUID) -> Case:
    case = Case(
        name="Evidence Case",
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


def test_upload_creates_artifact_with_metadata(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)

    response = client.post(
        f"/cases/{case.id}/artifacts/upload",
        headers=auth_header(token),
        files={"file": ("report.pdf", b"%PDF-1.4 evidence", "application/pdf")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["original_filename"] == "report.pdf"
    assert payload["file_size_bytes"] == len(b"%PDF-1.4 evidence")
    assert payload["file_extension"] == "pdf"
    assert payload["mime_type"] == "application/pdf"
    assert payload["uploaded_by"] == str(user.id)
    assert payload["uploaded_at"] is not None
    assert payload["status"] == ArtifactStatus.preserved.value
    assert payload["content_hash"] is not None

    stored = db_session.get(Artifact, uuid.UUID(payload["id"]))
    assert stored is not None
    assert stored.storage_path
    raw_file = tmp_path / stored.storage_path
    assert raw_file.read_bytes() == b"%PDF-1.4 evidence"


def test_list_artifacts_requires_case_access(
    client: TestClient,
    db_session: Session,
) -> None:
    owner = create_test_user(db_session, email="owner@local.dev")
    other = create_test_user(db_session, email="other@local.dev")
    case = create_case_for_user(db_session, owner.id)
    owner_token = login_token(client, owner)

    upload = client.post(
        f"/cases/{case.id}/artifacts/upload",
        headers=auth_header(owner_token),
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert upload.status_code == 201

    other_token = login_token(client, other)
    denied = client.get(
        f"/cases/{case.id}/artifacts",
        headers=auth_header(other_token),
    )
    assert denied.status_code == 404


def test_empty_upload_returns_400_without_artifact_row(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)

    response = client.post(
        f"/cases/{case.id}/artifacts/upload",
        headers=auth_header(token),
        files={"file": ("empty.txt", b"", "text/plain")},
    )

    assert response.status_code == 400
    count = db_session.scalar(select(func.count()).select_from(Artifact))
    assert count == 0


def test_preservation_failure_marks_artifact_failed(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)

    def fail_preserve(*args: object, **kwargs: object) -> tuple[str, str]:
        raise StorageError("disk full")

    monkeypatch.setattr(LocalStorageService, "preserve_raw", fail_preserve)

    response = client.post(
        f"/cases/{case.id}/artifacts/upload",
        headers=auth_header(token),
        files={"file": ("broken.bin", b"payload", "application/octet-stream")},
    )

    assert response.status_code == 500
    stored = db_session.scalars(select(Artifact)).all()
    assert len(stored) == 1
    assert stored[0].status == ArtifactStatus.failed
    assert stored[0].content_hash is None


def test_get_artifact_returns_metadata(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)

    created = client.post(
        f"/cases/{case.id}/artifacts/upload",
        headers=auth_header(token),
        files={"file": ("photo.jpg", b"\xff\xd8\xff", "image/jpeg")},
    )
    assert created.status_code == 201
    artifact_id = created.json()["id"]

    fetched = client.get(
        f"/cases/{case.id}/artifacts/{artifact_id}",
        headers=auth_header(token),
    )
    assert fetched.status_code == 200
    assert fetched.json()["original_filename"] == "photo.jpg"
