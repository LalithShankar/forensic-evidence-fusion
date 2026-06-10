"""Evidence-grounded assistant API routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_llm, get_search
from app.core.auth_deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.assistant import (
    AssistantAnswerPublic,
    AssistantAskInput,
    AssistantLogPublic,
    SourceReferencePublic,
)
from app.services.assistant_service import ask, list_assistant_logs
from app.services.indexing.search_backend import SearchBackend
from app.services.llm_backend import LLMBackend

router = APIRouter(tags=["assistant"])


@router.post(
    "/cases/{case_id}/assistant/ask",
    response_model=AssistantAnswerPublic,
)
def post_assistant_ask(
    case_id: uuid.UUID,
    payload: AssistantAskInput,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    search_backend: Annotated[SearchBackend, Depends(get_search)],
    llm_backend: Annotated[LLMBackend, Depends(get_llm)],
) -> AssistantAnswerPublic:
    """Ask a grounded question over indexed case evidence."""
    try:
        result = ask(
            db,
            current_user,
            case_id,
            payload,
            search_backend,
            llm_backend,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or inaccessible",
        )

    return AssistantAnswerPublic(
        answer_text=result.answer_text,
        confidence=result.confidence,
        limitation_text=result.limitation_text,
        insufficient_evidence=result.insufficient_evidence,
        source_references=[
            SourceReferencePublic.model_validate(source)
            for source in result.source_references
        ],
        log_id=result.log_id,
    )


@router.get(
    "/cases/{case_id}/assistant/logs",
    response_model=list[AssistantLogPublic],
)
def get_assistant_logs(
    case_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[AssistantLogPublic]:
    """Return recent assistant Q&A audit entries."""
    logs = list_assistant_logs(db, current_user, case_id)
    if logs is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or inaccessible",
        )
    return [AssistantLogPublic.model_validate(entry) for entry in logs]
