"""Deterministic case report draft generation."""

from __future__ import annotations

import uuid
from collections import Counter
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth_deps import check_case_access
from app.models.artifact import Artifact, ArtifactStatus
from app.models.case import Case
from app.models.case_membership import CaseAccessLevel
from app.models.claim import Claim, ClaimResolution, Report
from app.models.transformation import TransformationRecord, TransformationStatus
from app.models.user import User
from app.schemas.report import ReportSection
from app.services.artifact_service import list_artifacts_for_case
from app.services.audit_service import write_audit_log
from app.services.claim_service import list_claims
from app.services.event_service import list_timeline_events
from app.services.manifest_service import build_case_manifest


def generate_report_draft(
    db: Session,
    user: User,
    case_id: uuid.UUID,
    *,
    title: str | None = None,
) -> Report | None:
    """Build or replace a draft report from case findings."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.contributor):
        return None

    case = db.get(Case, case_id)
    if case is None:
        return None

    events = list_timeline_events(db, user, case_id) or []
    claims = list_claims(db, user, case_id) or []
    artifacts = list_artifacts_for_case(db, user, case_id)

    resolutions = _load_resolutions(db, case_id, claims)
    transformations = _load_transformations(db, case_id)

    sections = [
        _build_timeline_summary(events),
        _build_claim_matrix(claims, resolutions),
        _build_limitations(claims, artifacts, transformations),
        _build_source_appendix(case_id, artifacts),
    ]

    content_json = {
        "version": 1,
        "generated_at": datetime.now().isoformat(),
        "summary": _build_summary(events, claims, resolutions),
        "sections": [section.model_dump() for section in sections],
    }

    report_title = title or f"Case report — {case.name}"
    existing = db.scalar(
        select(Report)
        .where(Report.case_id == case_id, Report.status == "draft")
        .order_by(Report.updated_at.desc())
        .limit(1)
    )

    if existing is None:
        report = Report(
            case_id=case_id,
            title=report_title,
            content_json=content_json,
            status="draft",
        )
        db.add(report)
    else:
        report = existing
        report.title = report_title
        report.content_json = content_json

    db.commit()
    db.refresh(report)

    write_audit_log(
        db,
        user_id=user.id,
        action="report.generated",
        object_type="report",
        object_id=report.id,
        case_id=case_id,
        after_json={
            "title": report.title,
            "status": report.status,
            "section_keys": [section.key for section in sections],
        },
    )
    return report


def list_reports(
    db: Session,
    user: User,
    case_id: uuid.UUID,
) -> list[Report] | None:
    """List report drafts for an accessible case."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.viewer):
        return None

    stmt = (
        select(Report)
        .where(Report.case_id == case_id)
        .order_by(Report.updated_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_report(
    db: Session,
    user: User,
    case_id: uuid.UUID,
    report_id: uuid.UUID,
) -> Report | None:
    """Return one report when the case is accessible."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.viewer):
        return None

    report = db.get(Report, report_id)
    if report is None or report.case_id != case_id:
        return None
    return report


def _load_resolutions(
    db: Session,
    case_id: uuid.UUID,
    claims: list[Claim],
) -> dict[uuid.UUID, ClaimResolution]:
    if not claims:
        return {}
    claim_ids = [claim.id for claim in claims]
    rows = db.scalars(
        select(ClaimResolution).where(
            ClaimResolution.case_id == case_id,
            ClaimResolution.claim_id.in_(claim_ids),
        )
    ).all()
    return {row.claim_id: row for row in rows}


def _load_transformations(
    db: Session,
    case_id: uuid.UUID,
) -> list[TransformationRecord]:
    return list(
        db.scalars(
            select(TransformationRecord).where(TransformationRecord.case_id == case_id)
        ).all()
    )


def _build_summary(
    events: list[Any],
    claims: list[Claim],
    resolutions: dict[uuid.UUID, ClaimResolution],
) -> str:
    unresolved = sum(
        1
        for claim in claims
        if claim.id not in resolutions
        or (resolutions[claim.id].result_label or "") == "unresolved"
    )
    return (
        f"{len(events)} timeline events, {len(claims)} claims, "
        f"{unresolved} unresolved or untested."
    )


def _build_timeline_summary(events: list[Any]) -> ReportSection:
    timestamps: list[datetime] = []
    event_types: Counter[str] = Counter()

    for event in events:
        event_types[event.event_type] += 1
        ts = event.normalized_timestamp or event.created_at
        if ts is not None:
            timestamps.append(ts)

    date_range: dict[str, str | None] = {"start": None, "end": None}
    if timestamps:
        earliest = min(timestamps)
        latest = max(timestamps)
        date_range = {
            "start": earliest.isoformat(),
            "end": latest.isoformat(),
        }

    key_types = [event_type for event_type, _count in event_types.most_common(5)]

    return ReportSection(
        key="timeline_summary",
        title="Timeline summary",
        content={
            "event_count": len(events),
            "date_range": date_range,
            "key_event_types": key_types,
        },
    )


def _build_claim_matrix(
    claims: list[Claim],
    resolutions: dict[uuid.UUID, ClaimResolution],
) -> ReportSection:
    rows: list[dict[str, Any]] = []
    for claim in claims:
        resolution = resolutions.get(claim.id)
        rows.append(
            {
                "claim_id": str(claim.id),
                "claim_text": claim.claim_text,
                "resolution_label": (
                    resolution.result_label if resolution else "not_resolved"
                ),
                "support_score": resolution.support_score if resolution else None,
                "contradiction_score": (
                    resolution.contradiction_score if resolution else None
                ),
            }
        )

    return ReportSection(
        key="claim_matrix",
        title="Claim matrix",
        content={"claims": rows},
    )


def _build_limitations(
    claims: list[Claim],
    artifacts: list[Artifact],
    transformations: list[TransformationRecord],
) -> ReportSection:
    notes: list[str] = []

    failed_transformations = [
        record
        for record in transformations
        if record.status
        in {
            TransformationStatus.failed.value,
            TransformationStatus.blocked.value,
        }
    ]
    for record in failed_transformations:
        notes.append(
            f"Transformation {record.status} for artifact {record.artifact_id}: "
            f"{record.failure_notes or record.limitation_notes or 'no details'}"
        )

    blocked_artifacts = [
        artifact
        for artifact in artifacts
        if artifact.status in {ArtifactStatus.failed, ArtifactStatus.blocked}
    ]
    for artifact in blocked_artifacts:
        notes.append(
            f"Artifact {artifact.original_filename} status={artifact.status.value}"
            + (f": {artifact.blocker_notes}" if artifact.blocker_notes else "")
        )

    unresolved_claims = [
        claim.claim_text for claim in claims if claim.parse_confidence < 0.4
    ]
    for claim_text in unresolved_claims:
        notes.append(f"Low parse confidence claim: {claim_text[:120]}")

    low_confidence = [claim for claim in claims if 0.4 <= claim.parse_confidence < 0.6]
    for claim in low_confidence:
        notes.append(
            f"Parse confidence warning ({claim.parse_confidence:.2f}): "
            f"{claim.claim_text[:120]}"
        )

    if not notes:
        notes.append("No material limitations identified.")

    return ReportSection(
        key="limitations",
        title="Limitations",
        content={"notes": notes},
    )


def _build_source_appendix(
    case_id: uuid.UUID,
    artifacts: list[Artifact],
) -> ReportSection:
    manifest = build_case_manifest(case_id, artifacts)
    return ReportSection(
        key="source_appendix",
        title="Source appendix",
        content={
            "artifact_count": manifest.artifact_count,
            "artifacts": [
                {
                    "id": str(entry.id),
                    "original_filename": entry.original_filename,
                    "status": entry.status.value,
                    "source_group": entry.source_group,
                    "content_hash": entry.content_hash,
                }
                for entry in manifest.artifacts
            ],
        },
    )
