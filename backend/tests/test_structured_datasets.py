"""Structured dataset API tests."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.artifacts import get_storage
from app.db.session import get_db
from app.main import app
from app.models.structured_dataset import StructuredDatasetStatus
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


def test_transformation_creates_structured_dataset(
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

    datasets = client.get(
        f"/cases/{case.id}/artifacts/{artifact_id}/structured-datasets",
        headers=auth_header(token),
    )
    assert datasets.status_code == 200
    body = datasets.json()
    assert len(body) == 1
    assert body[0]["dataset_type"] == "csv"
    assert body[0]["row_count"] == 1
    assert body[0]["schema_version"] == "1.0"
    assert body[0]["status"] == StructuredDatasetStatus.generated.value
    assert body[0]["confidence"] > 0


def test_structured_dataset_preview_returns_rows(
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
    datasets = client.get(
        f"/cases/{case.id}/artifacts/{artifact_id}/structured-datasets",
        headers=auth_header(token),
    )
    dataset_id = datasets.json()[0]["id"]

    preview = client.get(
        f"/cases/{case.id}/artifacts/{artifact_id}/structured-datasets/{dataset_id}/preview",
        headers=auth_header(token),
    )
    assert preview.status_code == 200
    payload = preview.json()
    assert payload["preview_rows"] is not None
    assert len(payload["preview_rows"]) == 1
    assert payload["confidence"] > 0


def test_failed_transformation_marks_dataset_failed(
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

    import uuid

    from app.models.artifact import Artifact, ArtifactStatus

    artifact = db_session.get(Artifact, uuid.UUID(artifact_id))
    assert artifact is not None
    artifact.status = ArtifactStatus.ready_for_transformation
    db_session.commit()

    client.post(
        f"/cases/{case.id}/artifacts/{artifact_id}/transformations/start",
        headers=auth_header(token),
    )

    datasets = client.get(
        f"/cases/{case.id}/artifacts/{artifact_id}/structured-datasets",
        headers=auth_header(token),
    )
    assert datasets.json()[0]["status"] == StructuredDatasetStatus.failed.value
