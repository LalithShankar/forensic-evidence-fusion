"""Map structured datasets to canonical evidence events."""

from __future__ import annotations

import json
import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.auth_deps import check_case_access
from app.models.artifact import Artifact
from app.models.case_membership import CaseAccessLevel
from app.models.event import EvidenceEvent, ReviewStatus
from app.models.structured_dataset import StructuredDataset, StructuredDatasetStatus
from app.models.user import User
from app.services.storage_service import StorageBackend, StorageError

_MESSAGE_KEYS = frozenset(
    {"message", "body", "text", "content", "chat", "msg", "sender", "from"}
)
_TRANSACTION_KEYS = frozenset(
    {"amount", "transaction", "payment", "debit", "credit", "value", "total"}
)
_TIMESTAMP_KEYS = frozenset(
    {"timestamp", "datetime", "date", "time", "occurred_at", "created_at"}
)

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2})?)?")


def normalize_artifact(
    db: Session,
    user: User,
    case_id: uuid.UUID,
    artifact_id: uuid.UUID,
    storage: StorageBackend,
    *,
    replace_existing: bool = True,
) -> list[EvidenceEvent] | None:
    """Normalize latest structured dataset rows into evidence events."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.contributor):
        return None

    artifact = db.get(Artifact, artifact_id)
    if artifact is None or artifact.case_id != case_id:
        return None

    dataset = db.scalar(
        select(StructuredDataset)
        .where(
            StructuredDataset.artifact_id == artifact_id,
            StructuredDataset.status == StructuredDatasetStatus.generated.value,
        )
        .order_by(StructuredDataset.created_at.desc())
        .limit(1)
    )
    if dataset is None or not dataset.storage_path:
        return []

    if replace_existing:
        db.execute(
            delete(EvidenceEvent).where(EvidenceEvent.artifact_id == artifact_id)
        )
        db.commit()

    try:
        raw = storage.read_raw(dataset.storage_path)
        payload = json.loads(raw.decode("utf-8"))
    except (StorageError, json.JSONDecodeError, UnicodeDecodeError):
        return []

    rows = _extract_rows(payload)
    events: list[EvidenceEvent] = []
    base_confidence = dataset.confidence

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        event = _row_to_event(
            row,
            case_id=case_id,
            artifact_id=artifact_id,
            transformation_id=dataset.transformation_id,
            structured_dataset_id=dataset.id,
            base_confidence=base_confidence,
            row_index=index,
        )
        if event is not None:
            db.add(event)
            events.append(event)

    if not events and payload.get("format") == "json":
        event = _json_object_to_event(
            payload.get("data", payload),
            case_id=case_id,
            artifact_id=artifact_id,
            transformation_id=dataset.transformation_id,
            structured_dataset_id=dataset.id,
            base_confidence=base_confidence,
        )
        if event is not None:
            db.add(event)
            events.append(event)

    db.commit()
    for event in events:
        db.refresh(event)
    return events


def list_case_events(
    db: Session,
    user: User,
    case_id: uuid.UUID,
) -> list[EvidenceEvent] | None:
    """List normalized events for an accessible case in chronological order."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.viewer):
        return None

    stmt = (
        select(EvidenceEvent)
        .where(EvidenceEvent.case_id == case_id)
        .order_by(
            func.coalesce(
                EvidenceEvent.normalized_timestamp,
                EvidenceEvent.created_at,
            ).asc(),
            EvidenceEvent.created_at.asc(),
        )
    )
    return list(db.scalars(stmt).all())


def _extract_rows(payload: dict[str, object]) -> list[dict[str, object]]:
    rows = payload.get("rows")
    if isinstance(rows, list):
        return [row for row in rows if isinstance(row, dict)]
    data = payload.get("data")
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        return [data]
    return []


def _row_to_event(
    row: dict[str, object],
    *,
    case_id: uuid.UUID,
    artifact_id: uuid.UUID,
    transformation_id: uuid.UUID | None,
    structured_dataset_id: uuid.UUID,
    base_confidence: float,
    row_index: int,
) -> EvidenceEvent | None:
    lowered = {str(key).lower(): value for key, value in row.items()}
    keys = set(lowered.keys())

    timestamp_text, normalized_ts, ts_confidence = _parse_timestamp(lowered)
    confidence = min(base_confidence, ts_confidence)

    if keys & _TRANSACTION_KEYS:
        amount = (
            lowered.get("amount")
            or lowered.get("value")
            or lowered.get("total")
            or lowered.get("payment")
        )
        return EvidenceEvent(
            case_id=case_id,
            artifact_id=artifact_id,
            transformation_id=transformation_id,
            structured_dataset_id=structured_dataset_id,
            event_type="transaction_observed",
            event_subtype=str(lowered.get("type", "generic")),
            original_timestamp_text=timestamp_text,
            normalized_timestamp=normalized_ts,
            title=f"Transaction row {row_index + 1}",
            description=str(amount) if amount is not None else None,
            payload_json=row,
            source_confidence=confidence,
            provenance_pointer=f"structured_dataset:{structured_dataset_id}:row:{row_index}",
            review_status=ReviewStatus.pending.value,
        )

    if keys & _MESSAGE_KEYS:
        body = (
            lowered.get("message")
            or lowered.get("body")
            or lowered.get("text")
            or lowered.get("content")
            or lowered.get("chat")
            or lowered.get("msg")
        )
        sender = lowered.get("sender") or lowered.get("from") or lowered.get("user")
        return EvidenceEvent(
            case_id=case_id,
            artifact_id=artifact_id,
            transformation_id=transformation_id,
            structured_dataset_id=structured_dataset_id,
            event_type="message_sent",
            event_subtype="structured_row",
            original_timestamp_text=timestamp_text,
            normalized_timestamp=normalized_ts,
            title=(
                f"Message from {sender}" if sender else f"Message row {row_index + 1}"
            ),
            description=str(body) if body is not None else None,
            payload_json=row,
            source_confidence=confidence,
            provenance_pointer=f"structured_dataset:{structured_dataset_id}:row:{row_index}",
            review_status=ReviewStatus.pending.value,
        )

    return EvidenceEvent(
        case_id=case_id,
        artifact_id=artifact_id,
        transformation_id=transformation_id,
        structured_dataset_id=structured_dataset_id,
        event_type="manual_observation",
        event_subtype="structured_row",
        original_timestamp_text=timestamp_text,
        normalized_timestamp=normalized_ts,
        title=f"Observation row {row_index + 1}",
        description=None,
        payload_json=row,
        source_confidence=confidence,
        provenance_pointer=f"structured_dataset:{structured_dataset_id}:row:{row_index}",
        review_status=ReviewStatus.pending.value,
    )


def _json_object_to_event(
    data: object,
    *,
    case_id: uuid.UUID,
    artifact_id: uuid.UUID,
    transformation_id: uuid.UUID | None,
    structured_dataset_id: uuid.UUID,
    base_confidence: float,
) -> EvidenceEvent | None:
    if not isinstance(data, dict):
        return None
    return _row_to_event(
        data,
        case_id=case_id,
        artifact_id=artifact_id,
        transformation_id=transformation_id,
        structured_dataset_id=structured_dataset_id,
        base_confidence=base_confidence,
        row_index=0,
    )


def _parse_timestamp(
    lowered: dict[str, object],
) -> tuple[str | None, datetime | None, float]:
    for key in _TIMESTAMP_KEYS:
        if key not in lowered or lowered[key] in (None, ""):
            continue
        raw_text = str(lowered[key])
        if _ISO_DATE_RE.match(raw_text):
            try:
                normalized = datetime.fromisoformat(raw_text.replace("Z", "+00:00"))
                if normalized.tzinfo is None:
                    normalized = normalized.replace(tzinfo=UTC)
                return raw_text, normalized, 0.85
            except ValueError:
                return raw_text, None, 0.45
        return raw_text, None, 0.45
    return None, None, 0.75
