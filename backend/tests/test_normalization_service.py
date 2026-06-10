"""Normalization service tests."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.artifacts import get_storage
from app.db.session import get_db
from app.main import app
from app.services.storage_service import LocalStorageBackend
from tests.test_auth import auth_header, create_test_user
from tests.test_cases import login_token
from tests.test_transformations import (
    create_case_for_user,
    upload_and_approve,
)


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


def test_message_like_row_creates_evidence_event(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)
    artifact_id = upload_and_approve(
        client,
        case.id,
        token,
        filename="chat.csv",
        content=b"sender,message,timestamp\nBob,Hello,sometime Tuesday\n",
        mime="text/csv",
    )

    client.post(
        f"/cases/{case.id}/artifacts/{artifact_id}/transformations/start",
        headers=auth_header(token),
    )

    events = client.get(f"/cases/{case.id}/events", headers=auth_header(token))
    assert events.status_code == 200
    body = events.json()
    assert len(body) >= 1
    event = body[0]
    assert event["event_type"] == "message_sent"
    assert event["artifact_id"] == artifact_id
    assert event["provenance_pointer"]
    assert event["original_timestamp_text"] == "sometime Tuesday"
    assert event["normalized_timestamp"] is None
    assert event["source_confidence"] <= 0.5


def test_transaction_like_row_creates_transaction_event(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)
    artifact_id = upload_and_approve(
        client,
        case.id,
        token,
        filename="ledger.csv",
        content=b"name,amount,date\nAlice,99.50,2024-01-15\n",
        mime="text/csv",
    )

    client.post(
        f"/cases/{case.id}/artifacts/{artifact_id}/transformations/start",
        headers=auth_header(token),
    )

    events = client.get(f"/cases/{case.id}/events", headers=auth_header(token))
    assert events.status_code == 200
    assert events.json()[0]["event_type"] == "transaction_observed"
    assert events.json()[0]["normalized_timestamp"] is not None


def test_manual_normalize_endpoint(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = create_case_for_user(db_session, user.id)
    token = login_token(client, user)
    artifact_id = upload_and_approve(
        client,
        case.id,
        token,
        filename="ledger.csv",
        content=b"a,b\n1,2",
        mime="text/csv",
    )
    client.post(
        f"/cases/{case.id}/artifacts/{artifact_id}/transformations/start",
        headers=auth_header(token),
    )

    normalize = client.post(
        f"/cases/{case.id}/artifacts/{artifact_id}/normalize",
        headers=auth_header(token),
    )
    assert normalize.status_code == 201
    assert normalize.json()["events_created"] >= 1


def test_canonical_models_import_without_circular_deps() -> None:
    from app.models import (  # noqa: F401
        AnalystNote,
        Claim,
        ClaimResolution,
        Entity,
        EvidenceEvent,
        Report,
    )

    assert EvidenceEvent.__tablename__ == "evidence_events"
    assert Entity.__tablename__ == "entities"
    assert Claim.__tablename__ == "claims"
