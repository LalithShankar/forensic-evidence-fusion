"""Deterministic claim resolution tests."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.event import EvidenceEvent, ReviewStatus
from app.schemas.claim import ClaimCreate
from app.services.claim_resolution_service import get_claim_resolution, resolve_claim
from app.services.claim_service import create_claim
from tests.test_auth import create_test_user
from tests.test_event_service import _seed_case_with_events


def test_resolve_claim_supported_with_matching_event(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case, artifact, _ = _seed_case_with_events(db_session, user.id)

    event_time = datetime(2024, 6, 1, 10, 0, tzinfo=UTC)
    db_session.add(
        EvidenceEvent(
            case_id=case.id,
            artifact_id=artifact.id,
            event_type="message_sent",
            normalized_timestamp=event_time,
            title="Message from Alice",
            description="Transfer confirmed by Alice",
            payload_json={"sender": "Alice", "message": "Transfer confirmed"},
            source_confidence=0.8,
            provenance_pointer="row:support",
            review_status=ReviewStatus.pending.value,
        )
    )
    db_session.commit()

    claim = create_claim(
        db_session,
        user,
        case.id,
        ClaimCreate(
            claim_text="Alice confirmed the transfer on 2024-06-01",
            claimant="Alice",
            claimed_time_text="2024-06-01T10:00:00+00:00",
            claimed_people=["Alice"],
            claim_source="interview",
        ),
    )
    assert claim is not None

    resolution = resolve_claim(db_session, user, case.id, claim.id)
    assert resolution is not None
    assert resolution.result_label in {"supported", "partially_supported"}
    assert resolution.support_score is not None
    assert resolution.support_score > 0
    assert resolution.supporting_event_ids
    assert len(resolution.supporting_event_ids) >= 1


def test_resolve_claim_unresolved_without_events(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case, _, _ = _seed_case_with_events(db_session, user.id)

    db_session.execute(delete(EvidenceEvent).where(EvidenceEvent.case_id == case.id))
    db_session.commit()

    claim = create_claim(
        db_session,
        user,
        case.id,
        ClaimCreate(claim_text="Something happened"),
    )
    assert claim is not None

    resolution = resolve_claim(db_session, user, case.id, claim.id)
    assert resolution is not None
    assert resolution.result_label == "unresolved"
    assert resolution.unresolved_reason
    assert resolution.support_score == 0.0


def test_resolve_claim_contradicted_by_time_mismatch(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case, artifact, _ = _seed_case_with_events(db_session, user.id)

    db_session.add(
        EvidenceEvent(
            case_id=case.id,
            artifact_id=artifact.id,
            event_type="message_sent",
            normalized_timestamp=datetime(2024, 1, 1, tzinfo=UTC),
            title="Message from Alice",
            description="Alice denied the transfer",
            payload_json={"sender": "Alice", "message": "denied transfer"},
            source_confidence=0.8,
            provenance_pointer="row:deny",
            review_status=ReviewStatus.pending.value,
        )
    )
    db_session.commit()

    claim = create_claim(
        db_session,
        user,
        case.id,
        ClaimCreate(
            claim_text="Alice confirmed the transfer on 2024-06-01",
            claimant="Alice",
            claimed_time_text="2024-06-01T10:00:00+00:00",
            claimed_people=["Alice"],
        ),
    )
    assert claim is not None

    resolution = resolve_claim(db_session, user, case.id, claim.id)
    assert resolution is not None
    assert resolution.contradiction_score is not None
    assert resolution.contradicting_event_ids
    assert resolution.result_label in {
        "weakly_contradicted",
        "strongly_contradicted",
        "unresolved",
    }


def test_re_resolve_updates_existing_row(db_session: Session) -> None:
    user = create_test_user(db_session)
    case, artifact, _ = _seed_case_with_events(db_session, user.id)

    claim = create_claim(
        db_session,
        user,
        case.id,
        ClaimCreate(claim_text="Generic observation"),
    )
    assert claim is not None

    first = resolve_claim(db_session, user, case.id, claim.id)
    assert first is not None

    db_session.add(
        EvidenceEvent(
            case_id=case.id,
            artifact_id=artifact.id,
            event_type="manual_observation",
            normalized_timestamp=datetime.now(UTC),
            title="Generic observation recorded",
            description="observation",
            payload_json={"note": "observation"},
            source_confidence=0.7,
            provenance_pointer="row:generic",
            review_status=ReviewStatus.pending.value,
        )
    )
    db_session.commit()

    second = resolve_claim(db_session, user, case.id, claim.id)
    assert second is not None
    assert second.id == first.id
    fetched = get_claim_resolution(db_session, user, case.id, claim.id)
    assert fetched is not None
    assert fetched.id == first.id
