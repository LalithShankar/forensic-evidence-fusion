"""Artifact upload and preservation business logic."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth_deps import check_case_access
from app.models.artifact import Artifact, ArtifactStatus
from app.models.case_membership import CaseAccessLevel
from app.models.user import User
from app.services.audit_service import write_audit_log
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
) -> Artifact | None:
    """Upload and preserve a raw artifact for an authorized case contributor."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.contributor):
        return None

    if not original_filename.strip():
        raise ValueError("Filename is required")
    if not content:
        raise ValueError("File content is required")

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
    artifact.status = ArtifactStatus.preserved
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
    }
