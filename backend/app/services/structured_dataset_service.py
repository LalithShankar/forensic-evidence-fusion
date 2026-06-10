"""Structured dataset registration and preview retrieval."""

from __future__ import annotations

import json
import uuid
from typing import Any, TypedDict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth_deps import check_case_access
from app.models.artifact import Artifact
from app.models.case_membership import CaseAccessLevel
from app.models.structured_dataset import (
    StructuredDataset,
    StructuredDatasetStatus,
)
from app.models.user import User
from app.services.storage_service import StorageBackend, StorageError

_SCHEMA_VERSION = "1.0"
_DEFAULT_CONFIDENCE = 0.75
_MAX_PREVIEW_ROWS = 50
_MAX_PREVIEW_CHARS = 50_000


class StructuredDatasetPreviewResult(TypedDict):
    """Preview payload returned by get_structured_dataset_preview."""

    dataset: StructuredDataset
    preview_rows: list[dict[str, Any]] | None
    preview_json: str | None
    truncated: bool
    total_rows: int | None


def register_structured_dataset(
    db: Session,
    *,
    artifact: Artifact,
    transformation_id: uuid.UUID | None,
    storage_path: str | None,
    structured_bytes: bytes | None,
    status: StructuredDatasetStatus,
    error_notes: str | None = None,
) -> StructuredDataset:
    """Create or update a structured dataset for a transformation run."""
    dataset_type = "unknown"
    row_count: int | None = None
    confidence = artifact.classification_confidence or _DEFAULT_CONFIDENCE

    if structured_bytes and status == StructuredDatasetStatus.generated:
        try:
            payload = json.loads(structured_bytes.decode("utf-8"))
            dataset_type = str(payload.get("format", "unknown"))
            if "row_count" in payload:
                row_count = int(payload["row_count"])
            elif dataset_type == "json":
                row_count = 1
            elif dataset_type == "pdf":
                row_count = payload.get("page_count")
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            status = StructuredDatasetStatus.failed
            error_notes = f"Invalid structured metadata: {exc}"
            storage_path = None

    if transformation_id is not None:
        existing = db.scalar(
            select(StructuredDataset).where(
                StructuredDataset.transformation_id == transformation_id
            )
        )
        if existing is not None:
            existing.dataset_type = dataset_type
            existing.storage_path = storage_path
            existing.row_count = row_count
            existing.schema_version = _SCHEMA_VERSION
            existing.confidence = confidence
            existing.status = status.value
            existing.error_notes = error_notes
            db.commit()
            db.refresh(existing)
            return existing

    dataset = StructuredDataset(
        artifact_id=artifact.id,
        transformation_id=transformation_id,
        dataset_type=dataset_type,
        storage_path=storage_path,
        row_count=row_count,
        schema_version=_SCHEMA_VERSION,
        confidence=confidence,
        status=status.value,
        error_notes=error_notes,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def list_structured_datasets(
    db: Session,
    user: User,
    case_id: uuid.UUID,
    artifact_id: uuid.UUID,
) -> list[StructuredDataset] | None:
    """List structured datasets for an accessible artifact."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.viewer):
        return None

    artifact = db.get(Artifact, artifact_id)
    if artifact is None or artifact.case_id != case_id:
        return None

    stmt = (
        select(StructuredDataset)
        .where(StructuredDataset.artifact_id == artifact_id)
        .order_by(StructuredDataset.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_structured_dataset_preview(
    db: Session,
    user: User,
    case_id: uuid.UUID,
    artifact_id: uuid.UUID,
    dataset_id: uuid.UUID,
    storage: StorageBackend,
) -> StructuredDatasetPreviewResult | None:
    """Return dataset plus safe preview payload."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.viewer):
        return None

    artifact = db.get(Artifact, artifact_id)
    if artifact is None or artifact.case_id != case_id:
        return None

    dataset = db.get(StructuredDataset, dataset_id)
    if dataset is None or dataset.artifact_id != artifact_id:
        return None

    if (
        dataset.status == StructuredDatasetStatus.failed.value
        or not dataset.storage_path
    ):
        return {
            "dataset": dataset,
            "preview_rows": None,
            "preview_json": dataset.error_notes or "Dataset unavailable.",
            "truncated": False,
            "total_rows": dataset.row_count,
        }

    try:
        raw = storage.read_raw(dataset.storage_path)
        payload = json.loads(raw.decode("utf-8"))
    except (StorageError, json.JSONDecodeError, UnicodeDecodeError):
        return {
            "dataset": dataset,
            "preview_rows": None,
            "preview_json": "Structured file could not be read.",
            "truncated": False,
            "total_rows": dataset.row_count,
        }

    if dataset.dataset_type == "csv" and "rows" in payload:
        rows = payload["rows"]
        total = len(rows)
        preview_rows = rows[:_MAX_PREVIEW_ROWS]
        return {
            "dataset": dataset,
            "preview_rows": preview_rows,
            "preview_json": None,
            "truncated": total > _MAX_PREVIEW_ROWS,
            "total_rows": total,
        }

    preview_text = json.dumps(payload, indent=2, ensure_ascii=False)
    truncated = len(preview_text) > _MAX_PREVIEW_CHARS
    if truncated:
        preview_text = preview_text[:_MAX_PREVIEW_CHARS] + "\n… [preview truncated]"
    return {
        "dataset": dataset,
        "preview_rows": None,
        "preview_json": preview_text,
        "truncated": truncated,
        "total_rows": dataset.row_count,
    }
