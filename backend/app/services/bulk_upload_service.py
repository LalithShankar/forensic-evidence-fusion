"""Orchestrate multi-file artifact uploads with partial failure handling."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.artifact import Artifact, ArtifactStatus
from app.models.user import User
from app.schemas.artifact import ArtifactMetadataInput
from app.services import artifact_service
from app.services.classification_service import classify_artifact
from app.services.storage_service import StorageBackend


@dataclass
class BulkUploadItemResult:
    """Outcome for a single file in a bulk upload batch."""

    filename: str
    artifact: Artifact | None
    error: str | None


@dataclass
class BulkUploadResult:
    """Aggregate result for a bulk upload request."""

    upload_batch_id: uuid.UUID
    results: list[BulkUploadItemResult]
    succeeded_count: int
    failed_count: int


def bulk_upload_artifacts(
    db: Session,
    user: User,
    case_id: uuid.UUID,
    *,
    files: list[tuple[str, str | None, bytes]],
    storage: StorageBackend,
    metadata: ArtifactMetadataInput | None = None,
) -> BulkUploadResult | None:
    """Upload multiple files; preserve successes and report per-file failures."""
    if not files:
        raise ValueError("At least one file is required")

    if not check_case_access_for_bulk(db, user, case_id):
        return None

    batch_id = uuid.uuid4()
    results: list[BulkUploadItemResult] = []
    succeeded = 0
    failed = 0

    for original_filename, mime_type, content in files:
        if not original_filename.strip():
            results.append(
                BulkUploadItemResult(
                    filename=original_filename or "(unnamed)",
                    artifact=None,
                    error="Filename is required",
                )
            )
            failed += 1
            continue

        if not content:
            results.append(
                BulkUploadItemResult(
                    filename=original_filename,
                    artifact=None,
                    error="File content is required",
                )
            )
            failed += 1
            continue

        try:
            artifact = artifact_service.upload_artifact(
                db,
                user,
                case_id,
                original_filename=original_filename,
                mime_type=mime_type,
                content=content,
                storage=storage,
                metadata=metadata,
                upload_batch_id=batch_id,
            )
        except ValueError as exc:
            results.append(
                BulkUploadItemResult(
                    filename=original_filename,
                    artifact=None,
                    error=str(exc),
                )
            )
            failed += 1
            continue

        if artifact is None:
            results.append(
                BulkUploadItemResult(
                    filename=original_filename,
                    artifact=None,
                    error="Case not found or access denied",
                )
            )
            failed += 1
            continue

        if artifact.status == ArtifactStatus.failed:
            results.append(
                BulkUploadItemResult(
                    filename=original_filename,
                    artifact=artifact,
                    error="Artifact preservation failed",
                )
            )
            failed += 1
            continue

        _apply_classification(db, artifact)
        results.append(
            BulkUploadItemResult(
                filename=original_filename,
                artifact=artifact,
                error=None,
            )
        )
        succeeded += 1

    return BulkUploadResult(
        upload_batch_id=batch_id,
        results=results,
        succeeded_count=succeeded,
        failed_count=failed,
    )


def check_case_access_for_bulk(
    db: Session,
    user: User,
    case_id: uuid.UUID,
) -> bool:
    """Return whether the user may upload to the case."""
    from app.core.auth_deps import check_case_access
    from app.models.case_membership import CaseAccessLevel

    return check_case_access(db, user, case_id, CaseAccessLevel.contributor)


def _apply_classification(db: Session, artifact: Artifact) -> None:
    """Run rule-based classification and update artifact fields."""
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
        artifact.source_group != "unknown"
        or artifact.source_family != "unknown"
        or artifact.artifact_type != "unknown"
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

    db.commit()
    db.refresh(artifact)
