"""Artifact provenance metadata API tests."""

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
from app.models.artifact import PROVENANCE_UNKNOWN, Artifact
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


def test_upload_with_metadata_persisted(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)

    response = client.post(
        f"/cases/{case.id}/artifacts/upload",
        headers=auth_header(token),
        data={
            "source_group": "financial",
            "source_family": "bank_statements",
            "artifact_type": "pdf_export",
            "collection_method": "manual_export",
            "parser_class": "direct_structured",
            "provenance_notes": "Exported by analyst from portal.",
        },
        files={"file": ("statement.pdf", b"%PDF-1.4", "application/pdf")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["source_group"] == "financial"
    assert payload["source_family"] == "bank_statements"
    assert payload["artifact_type"] == "pdf_export"
    assert payload["collection_method"] == "manual_export"
    assert payload["parser_class"] == "direct_structured"
    assert payload["provenance_notes"] == "Exported by analyst from portal."

    stored = db_session.get(Artifact, uuid.UUID(payload["id"]))
    assert stored is not None
    assert stored.source_group == "financial"
    assert stored.parser_class == "direct_structured"


def test_upload_without_metadata_applies_defaults(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)

    response = client.post(
        f"/cases/{case.id}/artifacts/upload",
        headers=auth_header(token),
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["source_group"] == PROVENANCE_UNKNOWN
    assert payload["source_family"] == PROVENANCE_UNKNOWN
    assert payload["artifact_type"] == PROVENANCE_UNKNOWN
    assert payload["collection_method"] == PROVENANCE_UNKNOWN
    assert payload["parser_class"] == PROVENANCE_UNKNOWN
    assert payload["provenance_notes"] is None


def test_get_artifact_returns_provenance_fields(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)

    created = client.post(
        f"/cases/{case.id}/artifacts/upload",
        headers=auth_header(token),
        data={
            "source_group": "communications",
            "provenance_notes": "Seized device backup.",
        },
        files={"file": ("chat.db", b"sqlite", "application/octet-stream")},
    )
    assert created.status_code == 201
    artifact_id = created.json()["id"]

    fetched = client.get(
        f"/cases/{case.id}/artifacts/{artifact_id}",
        headers=auth_header(token),
    )
    assert fetched.status_code == 200
    body = fetched.json()
    assert body["source_group"] == "communications"
    assert body["provenance_notes"] == "Seized device backup."
    assert body["source_family"] == PROVENANCE_UNKNOWN
