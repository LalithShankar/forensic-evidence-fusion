"""Synchronous transformation pipeline state machine."""

from __future__ import annotations

import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth_deps import check_case_access
from app.models.artifact import Artifact, ArtifactStatus
from app.models.case_membership import CaseAccessLevel
from app.models.readable_view import ReadableViewStatus, ReadableViewType
from app.models.structured_dataset import StructuredDatasetStatus
from app.models.transformation import (
    TransformationRecord,
    TransformationStage,
    TransformationStatus,
)
from app.models.user import User
from app.parsers import csv_parser, json_parser, pdf_parser
from app.services.audit_service import write_audit_log
from app.services.normalization_service import normalize_artifact
from app.services.readable_view_service import register_readable_view
from app.services.storage_paths import StorageNamespace
from app.services.storage_service import StorageBackend, StorageError
from app.services.structured_dataset_service import register_structured_dataset

_STAGE_ORDER: list[TransformationStage] = [
    TransformationStage.preserved,
    TransformationStage.classified,
    TransformationStage.preprocessed,
    TransformationStage.extracted,
    TransformationStage.readable_generated,
    TransformationStage.structured_generated,
]


def start_transformation(
    db: Session,
    user: User,
    case_id: uuid.UUID,
    artifact_id: uuid.UUID,
    storage: StorageBackend,
) -> tuple[TransformationRecord, list[TransformationStage]] | None:
    """Start or return an idempotent transformation for a ready artifact."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.contributor):
        return None

    artifact = db.get(Artifact, artifact_id)
    if artifact is None or artifact.case_id != case_id:
        return None

    if artifact.status != ArtifactStatus.ready_for_transformation:
        return None

    if not artifact.content_hash:
        return None

    idempotency_key = f"{artifact_id}:{artifact.content_hash}"
    existing = db.scalar(
        select(TransformationRecord).where(
            TransformationRecord.idempotency_key == idempotency_key
        )
    )
    if existing is not None and existing.status == TransformationStatus.completed:
        return existing, _stages_up_to(existing.current_stage)

    record = existing or TransformationRecord(
        artifact_id=artifact_id,
        case_id=case_id,
        current_stage=TransformationStage.preserved.value,
        status=TransformationStatus.running.value,
        idempotency_key=idempotency_key,
    )
    if existing is None:
        db.add(record)
    db.commit()
    db.refresh(record)

    completed_stages: list[TransformationStage] = []
    try:
        _advance_stage(record, TransformationStage.classified)
        completed_stages.append(TransformationStage.preserved)
        completed_stages.append(TransformationStage.classified)
        db.commit()

        raw_bytes = storage.read_raw(artifact.storage_path)
        _advance_stage(record, TransformationStage.preprocessed)
        completed_stages.append(TransformationStage.preprocessed)
        db.commit()

        parser_output = _extract_content(artifact, raw_bytes)
        _advance_stage(record, TransformationStage.extracted)
        completed_stages.append(TransformationStage.extracted)
        db.commit()

        readable_name = _output_filename(artifact.original_filename, "readable.txt")
        record.readable_path = storage.write_output(
            case_id,
            artifact_id,
            readable_name,
            parser_output.readable,
            StorageNamespace.readable,
        )
        _advance_stage(record, TransformationStage.readable_generated)
        completed_stages.append(TransformationStage.readable_generated)
        db.commit()
        register_readable_view(
            db,
            artifact_id=artifact_id,
            transformation_id=record.id,
            view_type=_readable_view_type(artifact),
            storage_path=record.readable_path,
            status=ReadableViewStatus.generated,
        )

        structured_name = _output_filename(
            artifact.original_filename,
            "structured.json",
        )
        record.structured_path = storage.write_output(
            case_id,
            artifact_id,
            structured_name,
            parser_output.structured,
            StorageNamespace.structured,
        )
        _advance_stage(record, TransformationStage.structured_generated)
        record.status = TransformationStatus.completed.value
        record.limitation_notes = parser_output.limitation_notes
        completed_stages.append(TransformationStage.structured_generated)
        db.commit()
        register_structured_dataset(
            db,
            artifact=artifact,
            transformation_id=record.id,
            storage_path=record.structured_path,
            structured_bytes=parser_output.structured,
            status=StructuredDatasetStatus.generated,
        )
        normalize_artifact(
            db,
            user,
            case_id,
            artifact_id,
            storage,
            replace_existing=True,
        )
        db.refresh(record)

        write_audit_log(
            db,
            user_id=user.id,
            action="artifact.transformation.completed",
            object_type="transformation_record",
            object_id=record.id,
            case_id=case_id,
            after_json={
                "artifact_id": str(artifact_id),
                "current_stage": record.current_stage,
                "status": record.status,
            },
        )
        return record, completed_stages
    except (ValueError, StorageError) as exc:
        record.current_stage = TransformationStage.blocked.value
        record.status = TransformationStatus.blocked.value
        record.failure_notes = str(exc)
        record.limitation_notes = record.limitation_notes or "Transformation blocked."
        db.commit()
        db.refresh(record)
        _register_readable_on_failure(
            db,
            artifact=artifact,
            record=record,
            error=str(exc),
        )
        register_structured_dataset(
            db,
            artifact=artifact,
            transformation_id=record.id,
            storage_path=record.structured_path,
            structured_bytes=None,
            status=StructuredDatasetStatus.failed,
            error_notes=str(exc),
        )
        completed_stages.append(TransformationStage.blocked)
        return record, completed_stages


def get_latest_transformation(
    db: Session,
    user: User,
    case_id: uuid.UUID,
    artifact_id: uuid.UUID,
) -> TransformationRecord | None:
    """Return the latest transformation record for an accessible artifact."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.viewer):
        return None

    artifact = db.get(Artifact, artifact_id)
    if artifact is None or artifact.case_id != case_id:
        return None

    stmt = (
        select(TransformationRecord)
        .where(TransformationRecord.artifact_id == artifact_id)
        .order_by(TransformationRecord.created_at.desc())
        .limit(1)
    )
    return db.scalar(stmt)


def _advance_stage(record: TransformationRecord, stage: TransformationStage) -> None:
    record.current_stage = stage.value
    record.status = TransformationStatus.running.value


def _extract_content(artifact: Artifact, raw_bytes: bytes):
    extension = artifact.file_extension.lower()
    filename = artifact.original_filename

    if extension == "csv" or artifact.mime_type == "text/csv":
        return csv_parser.parse_csv(raw_bytes, filename=filename)
    if extension == "json" or artifact.mime_type == "application/json":
        return json_parser.parse_json(raw_bytes, filename=filename)
    if extension == "pdf" or artifact.mime_type == "application/pdf":
        return pdf_parser.parse_pdf(raw_bytes, filename=filename)

    raise ValueError(f"Unsupported artifact format for MVP parser: {extension}")


def _output_filename(original_filename: str, suffix_name: str) -> str:
    stem = Path(original_filename).stem or "artifact"
    return f"{stem}_{suffix_name}"


def _readable_view_type(artifact: Artifact) -> ReadableViewType:
    if artifact.artifact_type in {"archive", "zip"} or artifact.file_extension in {
        "zip",
        "tar",
        "gz",
    }:
        return ReadableViewType.inventory
    return ReadableViewType.extracted_text


def _register_readable_on_failure(
    db: Session,
    *,
    artifact: Artifact,
    record: TransformationRecord,
    error: str,
) -> None:
    if record.readable_path:
        register_readable_view(
            db,
            artifact_id=artifact.id,
            transformation_id=record.id,
            view_type=_readable_view_type(artifact),
            storage_path=record.readable_path,
            status=ReadableViewStatus.partial,
            error_notes=error,
        )
        return

    register_readable_view(
        db,
        artifact_id=artifact.id,
        transformation_id=record.id,
        view_type=_readable_view_type(artifact),
        storage_path=None,
        status=ReadableViewStatus.failed,
        error_notes=error,
    )


def _stages_up_to(current_stage: str) -> list[TransformationStage]:
    stages: list[TransformationStage] = []
    for stage in _STAGE_ORDER:
        stages.append(stage)
        if stage.value == current_stage:
            break
    return stages
