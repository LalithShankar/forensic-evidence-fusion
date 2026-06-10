"""Review queue listing and classification correction."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.auth_deps import check_case_access
from app.models.artifact import PROVENANCE_UNKNOWN, Artifact, ArtifactStatus
from app.models.case_membership import CaseAccessLevel
from app.models.user import User
from app.schemas.artifact import resolve_provenance_field
from app.schemas.review import ReviewActionInput
from app.services.audit_service import write_audit_log


@dataclass
class ReviewQueueEntry:
    """Internal review queue row before schema serialization."""

    artifact: Artifact
    review_reason: str
    suggested_category: str


def list_review_queue(
    db: Session,
    user: User,
    case_id: uuid.UUID,
) -> list[ReviewQueueEntry] | None:
    """Return artifacts needing review for an accessible case."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.viewer):
        return None

    stmt = (
        select(Artifact)
        .where(Artifact.case_id == case_id)
        .where(
            or_(
                Artifact.status == ArtifactStatus.needs_review,
                Artifact.status == ArtifactStatus.blocked,
            )
        )
        .order_by(Artifact.uploaded_at.desc(), Artifact.created_at.desc())
    )
    artifacts = list(db.scalars(stmt))
    return [_to_queue_item(artifact) for artifact in artifacts]


def apply_review_action(
    db: Session,
    user: User,
    case_id: uuid.UUID,
    artifact_id: uuid.UUID,
    action_input: ReviewActionInput,
) -> Artifact | None:
    """Correct metadata, approve, or mark preserve-only for a review item."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.contributor):
        return None

    artifact = db.get(Artifact, artifact_id)
    if artifact is None or artifact.case_id != case_id:
        return None

    if artifact.status not in (
        ArtifactStatus.needs_review,
        ArtifactStatus.blocked,
        ArtifactStatus.preserved,
    ):
        return None

    before = _artifact_snapshot(artifact)
    action = action_input.action.strip().lower()

    if action_input.source_group is not None:
        artifact.source_group = resolve_provenance_field(action_input.source_group)
    if action_input.source_family is not None:
        artifact.source_family = resolve_provenance_field(action_input.source_family)
    if action_input.artifact_type is not None:
        artifact.artifact_type = resolve_provenance_field(action_input.artifact_type)

    if action == "preserve_only":
        artifact.status = ArtifactStatus.preserve_only
    elif action == "approve":
        if artifact.source_group == PROVENANCE_UNKNOWN:
            artifact.source_group = artifact.suggested_source_group
        if artifact.source_family == PROVENANCE_UNKNOWN:
            artifact.source_family = artifact.suggested_source_family
        if artifact.artifact_type == PROVENANCE_UNKNOWN:
            artifact.artifact_type = artifact.suggested_artifact_type
        artifact.status = ArtifactStatus.ready_for_transformation
    elif action == "correct":
        artifact.status = ArtifactStatus.needs_review
    else:
        raise ValueError(f"Unsupported review action: {action_input.action}")

    db.commit()
    db.refresh(artifact)

    write_audit_log(
        db,
        user_id=user.id,
        action=f"artifact.review.{action}",
        object_type="artifact",
        object_id=artifact.id,
        case_id=case_id,
        before_json=before,
        after_json=_artifact_snapshot(artifact),
    )
    return artifact


def _to_queue_item(artifact: Artifact) -> ReviewQueueEntry:
    if artifact.status == ArtifactStatus.blocked:
        reason = artifact.blocker_notes or "Artifact is blocked"
        category = "Blocked"
    elif artifact.classification_reason:
        reason = artifact.classification_reason
        category = (
            f"{artifact.suggested_source_group} / {artifact.suggested_source_family}"
        )
    else:
        reason = "Low classification confidence"
        category = (
            f"{artifact.suggested_source_group} / {artifact.suggested_source_family}"
        )

    return ReviewQueueEntry(
        artifact=artifact,
        review_reason=reason,
        suggested_category=category,
    )


def _artifact_snapshot(artifact: Artifact) -> dict[str, Any]:
    status = (
        artifact.status.value
        if isinstance(artifact.status, ArtifactStatus)
        else artifact.status
    )
    return {
        "id": str(artifact.id),
        "status": status,
        "source_group": artifact.source_group,
        "source_family": artifact.source_family,
        "artifact_type": artifact.artifact_type,
    }
