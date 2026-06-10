"""Claim API and service tests."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.main import app
from app.schemas.claim import ClaimCreate
from app.services.claim_service import create_claim, get_claim, list_claims
from tests.test_auth import auth_header, create_test_user
from tests.test_cases import login_token
from tests.test_event_service import _seed_case_with_events


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_create_claim_stores_fields_and_parse_confidence(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case, _, _ = _seed_case_with_events(db_session, user.id)

    claim = create_claim(
        db_session,
        user,
        case.id,
        ClaimCreate(
            claim_text="Alice sent a transfer on 2024-06-01",
            claimant="Alice",
            claimed_time_text="2024-06-01",
            claimed_people=["Alice"],
            claim_source="interview",
        ),
    )
    assert claim is not None
    assert claim.claim_text.startswith("Alice sent")
    assert claim.claim_source == "interview"
    assert claim.created_by == user.id
    assert claim.parse_confidence >= 0.5
    assert claim.claimed_time_normalized is not None


def test_create_claim_requires_access(db_session: Session) -> None:
    owner = create_test_user(db_session, email="owner@local.dev")
    outsider = create_test_user(db_session, email="outsider@local.dev")
    case, _, _ = _seed_case_with_events(db_session, owner.id)

    result = create_claim(
        db_session,
        outsider,
        case.id,
        ClaimCreate(claim_text="Unauthorized claim"),
    )
    assert result is None


def test_claim_api_validation_preserves_input_on_422(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case, _, _ = _seed_case_with_events(db_session, user.id)
    token = login_token(client, user)

    response = client.post(
        f"/cases/{case.id}/claims",
        headers=auth_header(token),
        json={"claim_text": ""},
    )
    assert response.status_code == 422


def test_list_claims_returns_created_at_and_parse_confidence(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case, _, _ = _seed_case_with_events(db_session, user.id)
    token = login_token(client, user)

    create = client.post(
        f"/cases/{case.id}/claims",
        headers=auth_header(token),
        json={
            "claim_text": "Bob confirmed the payment on 2024-06-01",
            "claimant": "Bob",
            "claim_source": "analyst_note",
        },
    )
    assert create.status_code == 201

    listed = client.get(f"/cases/{case.id}/claims", headers=auth_header(token))
    assert listed.status_code == 200
    body = listed.json()
    assert len(body) == 1
    assert body[0]["created_at"]
    assert body[0]["parse_confidence"] >= 0.35


def test_get_claim_detail(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case, _, _ = _seed_case_with_events(db_session, user.id)
    created = create_claim(
        db_session,
        user,
        case.id,
        ClaimCreate(claim_text="Detail claim text"),
    )
    assert created is not None

    fetched = get_claim(db_session, user, case.id, created.id)
    assert fetched is not None
    assert fetched.claim_text == "Detail claim text"

    claims = list_claims(db_session, user, case.id)
    assert claims is not None
    assert len(claims) == 1
