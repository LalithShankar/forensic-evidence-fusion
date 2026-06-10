"""Evidence-grounded assistant service."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth_deps import check_case_access
from app.models.assistant_log import AssistantLog
from app.models.case_membership import CaseAccessLevel
from app.models.user import User
from app.schemas.assistant import AssistantAskInput, SourceReferencePublic
from app.services.indexing.search_backend import SearchBackend
from app.services.indexing.search_types import SearchHit
from app.services.llm_backend import LLMBackend, format_hits_context

_MIN_RELEVANCE_SCORE = 0.12
_LOW_CONFIDENCE_THRESHOLD = 0.35

_SYSTEM_PROMPT = (
    "You are a forensic evidence assistant. Answer ONLY using the provided "
    "evidence context. Do not speculate or draw legal conclusions. If evidence "
    "is insufficient, say so explicitly."
)


@dataclass(frozen=True)
class AssistantAnswer:
    """Service-layer assistant response."""

    answer_text: str
    confidence: float
    limitation_text: str | None
    insufficient_evidence: bool
    source_references: list[SourceReferencePublic]
    log_id: uuid.UUID


def ask(
    db: Session,
    user: User,
    case_id: uuid.UUID,
    payload: AssistantAskInput,
    search_backend: SearchBackend,
    llm_backend: LLMBackend,
) -> AssistantAnswer | None:
    """Answer a case-scoped question using retrieved chunks only."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.viewer):
        return None

    hits = search_backend.search(case_id, payload.question.strip(), top_k=5)
    relevant = [hit for hit in hits if hit.score >= _MIN_RELEVANCE_SCORE]

    if not relevant:
        log = _write_log(
            db,
            user=user,
            case_id=case_id,
            question=payload.question.strip(),
            answer_text=(
                "Insufficient evidence in this case to answer that question. "
                "Try indexing more artifacts or refining your question."
            ),
            model_name=llm_backend.model_name,
            confidence=0.0,
            limitation_text="No relevant indexed chunks matched the question.",
            insufficient_evidence=True,
            hits=[],
        )
        return AssistantAnswer(
            answer_text=log.answer_text,
            confidence=log.confidence,
            limitation_text=log.limitation_text,
            insufficient_evidence=True,
            source_references=[],
            log_id=log.id,
        )

    context = format_hits_context(relevant)
    answer_text = llm_backend.complete(
        system=_SYSTEM_PROMPT,
        user=payload.question.strip(),
        context=context,
    )
    confidence = sum(hit.score for hit in relevant) / len(relevant)
    limitation_text: str | None = None
    if confidence < _LOW_CONFIDENCE_THRESHOLD:
        limitation_text = (
            "Retrieved evidence partially matches the question. "
            "Review linked sources before relying on this answer."
        )

    sources = [
        SourceReferencePublic(
            chunk_id=hit.chunk_id,
            artifact_id=hit.artifact_id,
            event_id=hit.event_id,
            provenance_pointer=hit.provenance_pointer,
            source_group=hit.source_group,
        )
        for hit in relevant
    ]
    _verify_citations(answer_text, relevant)

    log = _write_log(
        db,
        user=user,
        case_id=case_id,
        question=payload.question.strip(),
        answer_text=answer_text,
        model_name=llm_backend.model_name,
        confidence=confidence,
        limitation_text=limitation_text,
        insufficient_evidence=False,
        hits=relevant,
        source_references=[source.model_dump(mode="json") for source in sources],
    )
    return AssistantAnswer(
        answer_text=answer_text,
        confidence=confidence,
        limitation_text=limitation_text,
        insufficient_evidence=False,
        source_references=sources,
        log_id=log.id,
    )


def list_assistant_logs(
    db: Session,
    user: User,
    case_id: uuid.UUID,
    *,
    limit: int = 20,
) -> list[AssistantLog] | None:
    """Return recent assistant audit entries for a case."""
    if not check_case_access(db, user, case_id, CaseAccessLevel.viewer):
        return None

    stmt = (
        select(AssistantLog)
        .where(AssistantLog.case_id == case_id)
        .order_by(AssistantLog.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def _write_log(
    db: Session,
    *,
    user: User,
    case_id: uuid.UUID,
    question: str,
    answer_text: str,
    model_name: str,
    confidence: float,
    limitation_text: str | None,
    insufficient_evidence: bool,
    hits: list[SearchHit],
    source_references: list[dict] | None = None,
) -> AssistantLog:
    log = AssistantLog(
        case_id=case_id,
        user_id=user.id,
        question=question,
        answer_text=answer_text,
        model_name=model_name,
        confidence=round(confidence, 3),
        limitation_text=limitation_text,
        insufficient_evidence=insufficient_evidence,
        retrieval_chunk_ids=[str(hit.chunk_id) for hit in hits],
        source_references=source_references
        or [
            {
                "chunk_id": str(hit.chunk_id),
                "artifact_id": str(hit.artifact_id),
                "event_id": str(hit.event_id) if hit.event_id else None,
                "provenance_pointer": hit.provenance_pointer,
            }
            for hit in hits
        ],
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def _verify_citations(answer_text: str, hits: list[SearchHit]) -> None:
    """Ensure explicit chunk_id citations in the answer refer to retrieved hits."""
    allowed = {str(hit.chunk_id) for hit in hits}
    for token in answer_text.split():
        if token.startswith("chunk_id="):
            cited = token.split("=", 1)[1].rstrip("]")
            if cited and cited not in allowed:
                msg = f"Citation verifier rejected unknown chunk id: {cited}"
                raise ValueError(msg)
