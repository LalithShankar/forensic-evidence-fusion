"""Case artifact manifest API and service tests."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.artifacts import get_storage
from app.db.session import get_db
from app.main import app
from app.models.artifact import PROVENANCE_UNKNOWN, Artifact, ArtifactStatus
from app.services.manifest_service import build_case_manifest
from app.services.storage_service import LocalStorageBackend
from tests.test_artifacts import create_case_for_user
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

    storage = LocalStorageBackend(tmp_path)

    def override_get_storage() -> LocalStorageBackend:
        return storage

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_storage] = override_get_storage
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_manifest_includes_all_artifacts_for_case(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)

    for name in ("a.txt", "b.txt"):
        response = client.post(
            f"/cases/{case.id}/artifacts/upload",
            headers=auth_header(token),
            files={"file": (name, b"payload", "text/plain")},
        )
        assert response.status_code == 201

    manifest = client.get(
        f"/cases/{case.id}/artifacts/manifest",
        headers=auth_header(token),
    )
    assert manifest.status_code == 200
    body = manifest.json()
    assert body["case_id"] == str(case.id)
    assert body["artifact_count"] == 2
    assert len(body["artifacts"]) == 2
    filenames = {entry["original_filename"] for entry in body["artifacts"]}
    assert filenames == {"a.txt", "b.txt"}


def test_manifest_required_fields_populated_with_defaults(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)

    upload = client.post(
        f"/cases/{case.id}/artifacts/upload",
        headers=auth_header(token),
        files={"file": ("data.csv", b"a,b\n1,2", "text/csv")},
    )
    assert upload.status_code == 201

    manifest = client.get(
        f"/cases/{case.id}/artifacts/manifest",
        headers=auth_header(token),
    ).json()
    entry = manifest["artifacts"][0]
    for field in (
        "source_group",
        "source_family",
        "artifact_type",
        "collection_method",
        "parser_class",
    ):
        assert entry[field] == PROVENANCE_UNKNOWN
    assert entry["storage_path"]
    assert entry["status"] == ArtifactStatus.preserved.value
    assert entry["content_hash"] is not None


def test_manifest_reflects_status_change(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    artifact = Artifact(
        case_id=case.id,
        original_filename="pending.bin",
        file_size_bytes=4,
        file_extension="bin",
        mime_type="application/octet-stream",
        uploaded_by=user.id,
        storage_path="raw/test/pending.bin",
        content_hash="abc",
        status=ArtifactStatus.pending,
    )
    db_session.add(artifact)
    db_session.commit()
    db_session.refresh(artifact)

    manifest = build_case_manifest(case.id, [artifact])
    assert manifest.artifacts[0].status == ArtifactStatus.pending

    artifact.status = ArtifactStatus.preserved
    db_session.commit()
    db_session.refresh(artifact)

    updated = build_case_manifest(case.id, [artifact])
    assert updated.artifacts[0].status == ArtifactStatus.preserved


def test_manifest_requires_case_access(
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
        files={"file": ("secret.txt", b"data", "text/plain")},
    )
    assert upload.status_code == 201

    other_token = login_token(client, other)
    denied = client.get(
        f"/cases/{case.id}/artifacts/manifest",
        headers=auth_header(other_token),
    )
    assert denied.status_code == 404
