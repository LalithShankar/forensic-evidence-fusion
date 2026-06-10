"""Event service and timeline API tests."""

from __future__ import annotations

import uuid
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.artifacts import get_storage
from app.db.session import get_db
from app.main import app
from app.models.artifact import PROVENANCE_UNKNOWN, Artifact, ArtifactStatus
from app.models.case import Case, CaseScenarioType
from app.models.case_membership import CaseAccessLevel, CaseMembership
from app.models.event import EvidenceEvent, ReviewStatus
from app.services.event_service import get_timeline_event, list_timeline_events
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


def _seed_case_with_events(
    db_session: Session,
    user_id: uuid.UUID,
) -> tuple[Case, Artifact, list[EvidenceEvent]]:
    case = Case(
        name="Timeline Case",
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

    artifact_a = Artifact(
        case_id=case.id,
        original_filename="chat.csv",
        file_size_bytes=100,
        file_extension="csv",
        mime_type="text/csv",
        status=ArtifactStatus.ready_for_transformation,
        source_group="ThirdParty",
        source_family=PROVENANCE_UNKNOWN,
        artifact_type=PROVENANCE_UNKNOWN,
        collection_method=PROVENANCE_UNKNOWN,
        parser_class=PROVENANCE_UNKNOWN,
    )
    artifact_b = Artifact(
        case_id=case.id,
        original_filename="ledger.csv",
        file_size_bytes=100,
        file_extension="csv",
        mime_type="text/csv",
        status=ArtifactStatus.ready_for_transformation,
        source_group="Bank",
        source_family=PROVENANCE_UNKNOWN,
        artifact_type=PROVENANCE_UNKNOWN,
        collection_method=PROVENANCE_UNKNOWN,
        parser_class=PROVENANCE_UNKNOWN,
    )
    db_session.add_all([artifact_a, artifact_b])
    db_session.flush()

    base = datetime(2024, 6, 1, tzinfo=UTC)
    events = [
        EvidenceEvent(
            case_id=case.id,
            artifact_id=artifact_a.id,
            event_type="message_sent",
            normalized_timestamp=base + timedelta(hours=2),
            title="Later message",
            source_confidence=0.8,
            provenance_pointer="row:1",
            review_status=ReviewStatus.pending.value,
        ),
        EvidenceEvent(
            case_id=case.id,
            artifact_id=artifact_a.id,
            event_type="message_sent",
            normalized_timestamp=base,
            title="Earlier message",
            source_confidence=0.7,
            provenance_pointer="row:0",
            review_status=ReviewStatus.reviewed.value,
        ),
        EvidenceEvent(
            case_id=case.id,
            artifact_id=artifact_b.id,
            event_type="transaction_observed",
            normalized_timestamp=None,
            title="Unparsed transaction",
            source_confidence=0.6,
            provenance_pointer="row:0",
            review_status=ReviewStatus.pending.value,
            created_at=base - timedelta(days=1),
        ),
    ]
    db_session.add_all(events)
    db_session.commit()
    for event in events:
        db_session.refresh(event)
    return case, artifact_a, events


def test_list_timeline_events_chronological(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case, _, events = _seed_case_with_events(db_session, user.id)

    result = list_timeline_events(db_session, user, case.id)
    assert result is not None
    titles = [event.title for event in result]
    assert titles == [
        "Unparsed transaction",
        "Earlier message",
        "Later message",
    ]
    assert all(event.provenance_pointer for event in result)
    assert all(event.artifact_id for event in result)
    assert result[1].source_group == "ThirdParty"
    assert result[2].source_group == "ThirdParty"
    assert result[0].source_group == "Bank"


def test_list_timeline_events_filter_by_type_and_source_group(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case, _, _ = _seed_case_with_events(db_session, user.id)

    filtered = list_timeline_events(
        db_session,
        user,
        case.id,
        event_type="message_sent",
        source_group="ThirdParty",
    )
    assert filtered is not None
    assert len(filtered) == 2
    assert all(event.event_type == "message_sent" for event in filtered)
    assert all(event.source_group == "ThirdParty" for event in filtered)


def test_list_timeline_events_filter_by_review_status(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case, _, _ = _seed_case_with_events(db_session, user.id)

    filtered = list_timeline_events(
        db_session,
        user,
        case.id,
        review_status=ReviewStatus.reviewed,
    )
    assert filtered is not None
    assert len(filtered) == 1
    assert filtered[0].title == "Earlier message"


def test_get_timeline_event_returns_detail(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case, _, events = _seed_case_with_events(db_session, user.id)

    detail = get_timeline_event(db_session, user, case.id, events[1].id)
    assert detail is not None
    assert detail.title == "Earlier message"
    assert detail.source_group == "ThirdParty"
    assert detail.provenance_pointer == "row:0"


def test_inaccessible_case_returns_none(db_session: Session) -> None:
    owner = create_test_user(db_session, email="owner@local.dev")
    outsider = create_test_user(db_session, email="outsider@local.dev")
    case, _, events = _seed_case_with_events(db_session, owner.id)

    assert list_timeline_events(db_session, outsider, case.id) is None
    assert get_timeline_event(db_session, outsider, case.id, events[0].id) is None


def test_events_api_supports_filters(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case, _, _ = _seed_case_with_events(db_session, user.id)
    token = login_token(client, user)

    response = client.get(
        f"/cases/{case.id}/events",
        headers=auth_header(token),
        params={"event_type": "transaction_observed", "source_group": "Bank"},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["event_type"] == "transaction_observed"
    assert body[0]["source_group"] == "Bank"
    assert body[0]["provenance_pointer"]


def test_event_detail_api_returns_404_for_missing_event(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case, _, _ = _seed_case_with_events(db_session, user.id)
    token = login_token(client, user)

    response = client.get(
        f"/cases/{case.id}/events/{uuid.uuid4()}",
        headers=auth_header(token),
    )
    assert response.status_code == 404
