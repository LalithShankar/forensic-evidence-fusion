"""Readable preview API tests."""

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
from app.models.readable_view import ReadableViewStatus, ReadableViewType
from app.models.transformation import TransformationStatus
from app.services.storage_service import LocalStorageBackend
from tests.test_auth import auth_header, create_test_user
from tests.test_cases import login_token
from tests.test_transformations import create_case_for_user, upload_and_approve_csv


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


def test_transformation_creates_readable_view(
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

    views = client.get(
        f"/cases/{case.id}/artifacts/{artifact_id}/readable-views",
        headers=auth_header(token),
    )
    assert views.status_code == 200
    body = views.json()
    assert len(body) == 1
    assert body[0]["view_type"] == ReadableViewType.extracted_text.value
    assert body[0]["status"] == ReadableViewStatus.generated.value
    assert body[0]["storage_path"]


def test_readable_view_content_returns_text(
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
    views = client.get(
        f"/cases/{case.id}/artifacts/{artifact_id}/readable-views",
        headers=auth_header(token),
    )
    view_id = views.json()[0]["id"]

    content = client.get(
        f"/cases/{case.id}/artifacts/{artifact_id}/readable-views/{view_id}/content",
        headers=auth_header(token),
    )
    assert content.status_code == 200
    payload = content.json()
    assert "CSV summary" in payload["content"]
    assert payload["content_type"] == "text/plain"


def test_failed_transformation_shows_failed_readable_view(
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
    client.patch(
        f"/cases/{case.id}/review-queue/{artifact_id}",
        headers=auth_header(token),
        json={
            "action": "approve",
            "source_group": "Generic",
            "source_family": "Binary",
            "artifact_type": "unknown",
        },
    )

    from app.models.artifact import Artifact

    artifact = db_session.get(Artifact, uuid.UUID(artifact_id))
    assert artifact is not None
    artifact.status = ArtifactStatus.ready_for_transformation
    db_session.commit()

    transform = client.post(
        f"/cases/{case.id}/artifacts/{artifact_id}/transformations/start",
        headers=auth_header(token),
    )
    assert transform.json()["record"]["status"] == TransformationStatus.blocked.value

    views = client.get(
        f"/cases/{case.id}/artifacts/{artifact_id}/readable-views",
        headers=auth_header(token),
    )
    assert views.status_code == 200
    assert views.json()[0]["status"] == ReadableViewStatus.failed.value
    assert views.json()[0]["error_notes"]


def test_no_readable_views_returns_empty_list(
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

    views = client.get(
        f"/cases/{case.id}/artifacts/{artifact_id}/readable-views",
        headers=auth_header(token),
    )
    assert views.status_code == 200
    assert views.json() == []
