"""Indexing service and API tests."""

from __future__ import annotations

import uuid
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_search, get_storage
from app.db.session import get_db
from app.main import app
from app.models.artifact import PROVENANCE_UNKNOWN, Artifact, ArtifactStatus
from app.models.case import Case, CaseScenarioType
from app.models.case_membership import CaseAccessLevel, CaseMembership
from app.models.readable_view import ReadableView, ReadableViewStatus, ReadableViewType
from app.models.search_chunk import IndexStatus, SearchChunk
from app.services.indexing.search_backend import InMemorySearchBackend, SearchBackend
from app.services.indexing.search_types import SearchHit
from app.services.storage_paths import StorageNamespace
from app.services.storage_service import LocalStorageBackend
from tests.test_auth import auth_header, create_test_user
from tests.test_cases import login_token


class FailingSearchBackend:
    """Test double that always fails upsert."""

    def upsert_chunks(self, chunks: list[SearchChunk]) -> None:
        raise RuntimeError("simulated index failure")

    def search(
        self,
        case_id: uuid.UUID,
        query: str,
        *,
        top_k: int = 5,
    ) -> list[SearchHit]:
        return []


@pytest.fixture
def search_backend() -> InMemorySearchBackend:
    return InMemorySearchBackend()


@pytest.fixture
def client(
    db_session: Session,
    tmp_path: Path,
    search_backend: InMemorySearchBackend,
) -> Generator[TestClient, None, None]:
    storage = LocalStorageBackend(tmp_path)

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    def override_get_storage() -> LocalStorageBackend:
        return storage

    def override_get_search() -> SearchBackend:
        return search_backend

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_storage] = override_get_storage
    app.dependency_overrides[get_search] = override_get_search
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _seed_indexable_case(
    db_session: Session,
    storage: LocalStorageBackend,
    user_id: uuid.UUID,
) -> Case:
    case = Case(
        name="Index Case",
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
    artifact = Artifact(
        case_id=case.id,
        original_filename="chat.txt",
        file_size_bytes=50,
        file_extension="txt",
        mime_type="text/plain",
        status=ArtifactStatus.ready_for_transformation,
        source_group="Bank",
        source_family=PROVENANCE_UNKNOWN,
        artifact_type=PROVENANCE_UNKNOWN,
        collection_method=PROVENANCE_UNKNOWN,
        parser_class=PROVENANCE_UNKNOWN,
    )
    db_session.add(artifact)
    db_session.flush()
    path = storage.write_output(
        case.id,
        artifact.id,
        "chat_readable.txt",
        b"Alice sent transfer confirmation on Tuesday.",
        StorageNamespace.readable,
    )
    db_session.add(
        ReadableView(
            artifact_id=artifact.id,
            view_type=ReadableViewType.extracted_text.value,
            storage_path=path,
            status=ReadableViewStatus.generated.value,
        )
    )
    db_session.commit()
    return case


def test_index_case_uses_in_memory_backend(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
    search_backend: InMemorySearchBackend,
) -> None:
    user = create_test_user(db_session)
    case = _seed_indexable_case(db_session, LocalStorageBackend(tmp_path), user.id)
    token = login_token(client, user)

    response = client.post(
        f"/cases/{case.id}/index",
        headers=auth_header(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["indexed"] >= 1
    assert body["failed"] == 0

    hits = search_backend.search(case.id, "Alice transfer", top_k=3)
    assert hits
    assert all(hit.case_id == case.id for hit in hits)


def test_index_failure_marks_chunks_failed(
    db_session: Session,
    tmp_path: Path,
) -> None:
    storage = LocalStorageBackend(tmp_path)
    user = create_test_user(db_session)
    case = _seed_indexable_case(db_session, storage, user.id)

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_storage] = lambda: storage
    app.dependency_overrides[get_search] = lambda: FailingSearchBackend()

    with TestClient(app) as client:
        token = login_token(client, user)
        response = client.post(
            f"/cases/{case.id}/index",
            headers=auth_header(token),
        )
        assert response.status_code == 200
        assert response.json()["failed"] >= 1

    app.dependency_overrides.clear()

    chunk = db_session.scalar(select(SearchChunk).limit(1))
    assert chunk is not None
    assert chunk.index_status == IndexStatus.failed.value
    assert chunk.index_error


def test_get_index_status(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
) -> None:
    user = create_test_user(db_session)
    case = _seed_indexable_case(db_session, LocalStorageBackend(tmp_path), user.id)
    token = login_token(client, user)
    client.post(f"/cases/{case.id}/index", headers=auth_header(token))
    status = client.get(
        f"/cases/{case.id}/index/status",
        headers=auth_header(token),
    )
    assert status.status_code == 200
    assert status.json()["total"] >= 1
