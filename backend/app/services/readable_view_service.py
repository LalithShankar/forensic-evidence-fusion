"""Readable preview registration and retrieval."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth_deps import check_case_access
from app.models.artifact import Artifact
from app.models.case_membership import CaseAccessLevel
from app.models.readable_view import (
    ReadableView,
    ReadableViewStatus,
    ReadableViewType,
)
from app.models.user import User
from app.services.storage_service import StorageBackend, StorageError

_MAX_PREVIEW_CHARS = 50_000


def register_readable_view(
    db: Session,
    *,
    artifact_id: uuid.UUID,
    transformation_id: uuid.UUID | None,
    view_type: ReadableViewType,
    storage_path: str | None,
    status: ReadableViewStatus,
    error_notes: str | None = None,
) -> ReadableView:
    """Create or update a readable view for a transformation run."""
    if transformation_id is not None:
        existing = db.scalar(
            select(ReadableView).where(
                ReadableView.transformation_id == transformation_id,
                ReadableView.view_type == view_type.value,
            )
        )
        if existing is not None:
            existing.storage_path = storage_path
            existing.status = status.value
            existing.error_notes = error_notes
            db.commit()
            db.refresh(existing)
            return existing

    view = ReadableView(
        artifact_id=artifact_id,
        transformation_id=transformation_id,
        view_type=view_type.value,
        storage_path=storage_path,
        status=status.value,
        error_notes=error_notes,
    )
    db.add(view)
    db.commit()
    db.refresh(view)
    return view


def list_readable_views(
    db: Session,
    user: User,
    case_id: uuid.UUID,
    artifact_id: uuid.UUID,
) -> list[ReadableView] | None:
    """List readable views for an accessible artifact."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.viewer):
        return None

    artifact = db.get(Artifact, artifact_id)
    if artifact is None or artifact.case_id != case_id:
        return None

    stmt = (
        select(ReadableView)
        .where(ReadableView.artifact_id == artifact_id)
        .order_by(ReadableView.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_readable_view_content(
    db: Session,
    user: User,
    case_id: uuid.UUID,
    artifact_id: uuid.UUID,
    view_id: uuid.UUID,
    storage: StorageBackend,
) -> tuple[ReadableView, str, str, bool] | None:
    """Return view, content_type, safe text content, and truncated flag."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.viewer):
        return None

    artifact = db.get(Artifact, artifact_id)
    if artifact is None or artifact.case_id != case_id:
        return None

    view = db.get(ReadableView, view_id)
    if view is None or view.artifact_id != artifact_id:
        return None

    if view.status == ReadableViewStatus.failed.value or not view.storage_path:
        return view, "text/plain", view.error_notes or "Preview unavailable.", False

    try:
        raw = storage.read_raw(view.storage_path)
    except StorageError:
        return (
            view,
            "text/plain",
            "Preview file could not be read from storage.",
            False,
        )

    text = raw.decode("utf-8", errors="replace")
    truncated = len(text) > _MAX_PREVIEW_CHARS
    if truncated:
        text = text[:_MAX_PREVIEW_CHARS] + "\n… [preview truncated]"

    content_type = (
        "application/json"
        if view.storage_path.endswith(".json")
        else "text/plain"
    )
    return view, content_type, text, truncated
