"""Deterministic claim resolution against timeline events."""

from __future__ import annotations

import json
import re
import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth_deps import check_case_access
from app.models.case_membership import CaseAccessLevel
from app.models.claim import Claim, ClaimResolution
from app.models.user import User
from app.schemas.event import EvidenceEventPublic
from app.services.audit_service import write_audit_log
from app.services.claim_service import get_claim
from app.services.event_service import list_timeline_events

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def resolve_claim(
    db: Session,
    user: User,
    case_id: uuid.UUID,
    claim_id: uuid.UUID,
) -> ClaimResolution | None:
    """Run deterministic resolution and upsert the claim resolution row."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.contributor):
        return None

    claim = get_claim(db, user, case_id, claim_id)
    if claim is None:
        return None

    events = list_timeline_events(db, user, case_id)
    if events is None:
        return None

    if not events:
        return _upsert_resolution(
            db,
            user,
            claim,
            result_label="unresolved",
            support_score=0.0,
            contradiction_score=0.0,
            supporting_event_ids=[],
            contradicting_event_ids=[],
            unresolved_reason="No evidence events available for comparison.",
        )

    if claim.parse_confidence < 0.4 and not claim.claimed_time_normalized:
        return _upsert_resolution(
            db,
            user,
            claim,
            result_label="not_testable",
            support_score=0.0,
            contradiction_score=0.0,
            supporting_event_ids=[],
            contradicting_event_ids=[],
            unresolved_reason=(
                "Claim lacks structured time or people signals for testing."
            ),
        )

    supporting: list[str] = []
    contradicting: list[str] = []
    support_scores: list[float] = []
    contradiction_scores: list[float] = []

    claim_tokens = _tokenize(claim.claim_text)
    claimed_people = [person.lower() for person in (claim.claimed_people or [])]

    for event in events:
        support, contradiction = _score_event_against_claim(
            claim,
            event,
            claim_tokens=claim_tokens,
            claimed_people=claimed_people,
        )
        if support >= 0.55:
            supporting.append(str(event.id))
            support_scores.append(support)
        if contradiction >= 0.35:
            contradicting.append(str(event.id))
            contradiction_scores.append(contradiction)

    support_score = max(support_scores) if support_scores else 0.0
    contradiction_score = max(contradiction_scores) if contradiction_scores else 0.0

    if not supporting and not contradicting:
        return _upsert_resolution(
            db,
            user,
            claim,
            result_label="unresolved",
            support_score=support_score,
            contradiction_score=contradiction_score,
            supporting_event_ids=[],
            contradicting_event_ids=[],
            unresolved_reason=(
                "No evidence events matched claim time, people, or keywords."
            ),
        )

    result_label = _map_result_label(support_score, contradiction_score)
    return _upsert_resolution(
        db,
        user,
        claim,
        result_label=result_label,
        support_score=support_score,
        contradiction_score=contradiction_score,
        supporting_event_ids=supporting,
        contradicting_event_ids=contradicting,
        unresolved_reason=None,
    )


def get_claim_resolution(
    db: Session,
    user: User,
    case_id: uuid.UUID,
    claim_id: uuid.UUID,
) -> ClaimResolution | None:
    """Return the latest resolution for a claim."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.viewer):
        return None

    return db.scalar(
        select(ClaimResolution).where(
            ClaimResolution.case_id == case_id,
            ClaimResolution.claim_id == claim_id,
        )
    )


def _upsert_resolution(
    db: Session,
    user: User,
    claim: Claim,
    *,
    result_label: str,
    support_score: float,
    contradiction_score: float,
    supporting_event_ids: list[str],
    contradicting_event_ids: list[str],
    unresolved_reason: str | None,
) -> ClaimResolution:
    existing = db.scalar(
        select(ClaimResolution).where(ClaimResolution.claim_id == claim.id)
    )
    if existing is None:
        existing = ClaimResolution(
            case_id=claim.case_id,
            claim_id=claim.id,
        )
        db.add(existing)

    existing.resolution_status = "completed"
    existing.result_label = result_label
    existing.support_score = round(support_score, 3)
    existing.contradiction_score = round(contradiction_score, 3)
    existing.supporting_event_ids = supporting_event_ids
    existing.contradicting_event_ids = contradicting_event_ids
    existing.unresolved_reason = unresolved_reason
    existing.resolution_notes = (
        f"Matched {len(supporting_event_ids)} supporting and "
        f"{len(contradicting_event_ids)} contradicting events."
    )

    db.commit()
    db.refresh(existing)

    write_audit_log(
        db,
        user_id=user.id,
        action="claim.resolved",
        object_type="claim",
        object_id=claim.id,
        case_id=claim.case_id,
        after_json={
            "result_label": existing.result_label,
            "support_score": existing.support_score,
            "contradiction_score": existing.contradiction_score,
        },
    )
    return existing


def _score_event_against_claim(
    claim: Claim,
    event: EvidenceEventPublic,
    *,
    claim_tokens: set[str],
    claimed_people: list[str],
) -> tuple[float, float]:
    support = 0.0
    contradiction = 0.0

    event_text = " ".join(
        filter(
            None,
            [
                event.title,
                event.description,
                json.dumps(event.payload_json or {}, sort_keys=True),
            ],
        )
    ).lower()
    event_tokens = _tokenize(event_text)
    overlap = claim_tokens & event_tokens
    if overlap:
        support += min(0.45, len(overlap) * 0.08)

    if claimed_people:
        people_hits = sum(1 for person in claimed_people if person in event_text)
        if people_hits:
            support += min(0.35, people_hits * 0.2)
        elif overlap:
            contradiction += 0.35

    if claim.claimed_time_normalized and event.normalized_timestamp:
        delta = abs(event.normalized_timestamp - claim.claimed_time_normalized)
        if delta <= timedelta(hours=24):
            support += 0.35
        elif delta >= timedelta(days=7):
            if overlap or claimed_people:
                contradiction += 0.4
        elif delta >= timedelta(days=2):
            contradiction += 0.2

    return min(1.0, support), min(1.0, contradiction)


def _map_result_label(support_score: float, contradiction_score: float) -> str:
    if contradiction_score >= 0.7:
        return "strongly_contradicted"
    if contradiction_score >= 0.4 and support_score < 0.5:
        return "weakly_contradicted"
    if support_score >= 0.7 and contradiction_score < 0.3:
        return "supported"
    if support_score >= 0.5 and contradiction_score < 0.4:
        return "partially_supported"
    return "unresolved"


def _tokenize(text: str) -> set[str]:
    return {
        token
        for token in _TOKEN_RE.findall(text.lower())
        if len(token) > 2 and token not in {"the", "and", "was", "were", "that"}
    }
