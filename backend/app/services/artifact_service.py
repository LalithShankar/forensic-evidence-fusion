"""Artifact upload and preservation business logic."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth_deps import check_case_access
from app.models.artifact import PROVENANCE_UNKNOWN, Artifact, ArtifactStatus
from app.models.case_membership import CaseAccessLevel
from app.models.user import User
from app.schemas.artifact import ArtifactMetadataInput, resolve_provenance_field
from app.services.audit_service import write_audit_log
from app.services.classification_service import classify_artifact
from app.services.storage_service import StorageBackend, StorageError


def _split_filename(filename: str) -> tuple[str, str]:
    path = Path(filename)
    extension = path.suffix.lstrip(".").lower()
    return path.name, extension


def list_artifacts_for_case(
    db: Session,
    user: User,
    case_id: uuid.UUID,
) -> list[Artifact]:
    """Return artifacts for a case when the user has viewer access."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.viewer):
        return []

    stmt = (
        select(Artifact)
        .where(Artifact.case_id == case_id)
        .order_by(Artifact.uploaded_at.desc(), Artifact.created_at.desc())
    )
    return list(db.scalars(stmt))


def get_artifact_for_user(
    db: Session,
    user: User,
    case_id: uuid.UUID,
    artifact_id: uuid.UUID,
) -> Artifact | None:
    """Return artifact metadata when the user has viewer access."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.viewer):
        return None

    artifact = db.get(Artifact, artifact_id)
    if artifact is None or artifact.case_id != case_id:
        return None
    return artifact


def upload_artifact(
    db: Session,
    user: User,
    case_id: uuid.UUID,
    *,
    original_filename: str,
    mime_type: str | None,
    content: bytes,
    storage: StorageBackend,
    metadata: ArtifactMetadataInput | None = None,
    upload_batch_id: uuid.UUID | None = None,
) -> Artifact | None:
    """Upload and preserve a raw artifact for an authorized case contributor."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.contributor):
        return None

    if not original_filename.strip():
        raise ValueError("Filename is required")
    if not content:
        raise ValueError("File content is required")

    meta = metadata or ArtifactMetadataInput()
    safe_name, extension = _split_filename(original_filename)
    now = datetime.now(UTC)

    artifact = Artifact(
        case_id=case_id,
        original_filename=safe_name,
        file_size_bytes=len(content),
        file_extension=extension,
        mime_type=mime_type or "application/octet-stream",
        uploaded_by=user.id,
        uploaded_at=now,
        status=ArtifactStatus.pending,
        source_group=resolve_provenance_field(meta.source_group),
        source_family=resolve_provenance_field(meta.source_family),
        artifact_type=resolve_provenance_field(meta.artifact_type),
        collection_method=resolve_provenance_field(meta.collection_method),
        parser_class=resolve_provenance_field(meta.parser_class),
        provenance_notes=meta.provenance_notes,
        upload_batch_id=upload_batch_id,
    )
    db.add(artifact)
    db.flush()

    try:
        storage_path, content_hash = storage.preserve_raw(
            case_id,
            artifact.id,
            safe_name,
            content,
        )
    except StorageError:
        artifact.status = ArtifactStatus.failed
        db.commit()
        db.refresh(artifact)
        return artifact

    artifact.storage_path = storage_path
    artifact.content_hash = content_hash
    _apply_post_preserve_classification(artifact)
    db.commit()
    db.refresh(artifact)

    write_audit_log(
        db,
        user_id=user.id,
        action="artifact.uploaded",
        object_type="artifact",
        object_id=artifact.id,
        case_id=case_id,
        after_json=_artifact_snapshot(artifact),
    )
    return artifact


def _apply_post_preserve_classification(artifact: Artifact) -> None:
    """Classify artifact after preservation when not part of a bulk batch."""
    if artifact.upload_batch_id is not None:
        artifact.status = ArtifactStatus.preserved
        return

    result = classify_artifact(
        original_filename=artifact.original_filename,
        file_extension=artifact.file_extension,
        mime_type=artifact.mime_type,
    )
    artifact.suggested_source_group = result.source_group
    artifact.suggested_source_family = result.source_family
    artifact.suggested_artifact_type = result.artifact_type
    artifact.classification_confidence = result.confidence
    artifact.classification_reason = result.reason

    user_provided = (
        artifact.source_group != PROVENANCE_UNKNOWN
        or artifact.source_family != PROVENANCE_UNKNOWN
        or artifact.artifact_type != PROVENANCE_UNKNOWN
    )

    if user_provided:
        artifact.status = ArtifactStatus.preserved
    elif result.needs_review:
        artifact.status = ArtifactStatus.needs_review
    else:
        artifact.source_group = result.source_group
        artifact.source_family = result.source_family
        artifact.artifact_type = result.artifact_type
        artifact.status = ArtifactStatus.preserved


def _artifact_snapshot(artifact: Artifact) -> dict[str, Any]:
    status = (
        artifact.status.value
        if isinstance(artifact.status, ArtifactStatus)
        else artifact.status
    )
    return {
        "id": str(artifact.id),
        "case_id": str(artifact.case_id),
        "original_filename": artifact.original_filename,
        "file_size_bytes": artifact.file_size_bytes,
        "status": status,
        "content_hash": artifact.content_hash,
        "source_group": artifact.source_group or PROVENANCE_UNKNOWN,
        "source_family": artifact.source_family or PROVENANCE_UNKNOWN,
        "artifact_type": artifact.artifact_type or PROVENANCE_UNKNOWN,
        "collection_method": artifact.collection_method or PROVENANCE_UNKNOWN,
        "parser_class": artifact.parser_class or PROVENANCE_UNKNOWN,
        "provenance_notes": artifact.provenance_notes,
        "upload_batch_id": (
            str(artifact.upload_batch_id) if artifact.upload_batch_id else None
        ),
        "classification_confidence": artifact.classification_confidence,
        "suggested_source_group": artifact.suggested_source_group,
        "suggested_source_family": artifact.suggested_source_family,
        "suggested_artifact_type": artifact.suggested_artifact_type,
        "classification_reason": artifact.classification_reason,
    }
