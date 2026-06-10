"""Claim create/list/detail service."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth_deps import check_case_access
from app.models.case_membership import CaseAccessLevel
from app.models.claim import Claim
from app.models.user import User
from app.schemas.claim import ClaimCreate
from app.services.audit_service import write_audit_log
from app.services.claim_parse_service import parse_claim_fields


def create_claim(
    db: Session,
    user: User,
    case_id: uuid.UUID,
    payload: ClaimCreate,
) -> Claim | None:
    """Create a narrative claim when the user has contributor access."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.contributor):
        return None

    time_text, normalized_time, people, parse_confidence = parse_claim_fields(
        claim_text=payload.claim_text,
        claimant=payload.claimant,
        claimed_time_text=payload.claimed_time_text,
        claimed_people=payload.claimed_people,
    )

    claim = Claim(
        case_id=case_id,
        claim_text=payload.claim_text.strip(),
        claimant=payload.claimant.strip() if payload.claimant else None,
        claimed_time_text=time_text,
        claimed_time_normalized=normalized_time,
        claimed_people=people or None,
        claim_source=payload.claim_source.strip() if payload.claim_source else None,
        created_by=user.id,
        parse_confidence=parse_confidence,
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)

    write_audit_log(
        db,
        user_id=user.id,
        action="claim.created",
        object_type="claim",
        object_id=claim.id,
        case_id=case_id,
        after_json={
            "claim_text": claim.claim_text,
            "claim_source": claim.claim_source,
        },
    )
    return claim


def list_claims(
    db: Session,
    user: User,
    case_id: uuid.UUID,
) -> list[Claim] | None:
    """List claims for an accessible case."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.viewer):
        return None

    stmt = (
        select(Claim)
        .where(Claim.case_id == case_id, Claim.status == "active")
        .order_by(Claim.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_claim(
    db: Session,
    user: User,
    case_id: uuid.UUID,
    claim_id: uuid.UUID,
) -> Claim | None:
    """Return a single claim when accessible."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.viewer):
        return None

    claim = db.scalar(
        select(Claim).where(
            Claim.id == claim_id,
            Claim.case_id == case_id,
            Claim.status == "active",
        )
    )
    return claim
