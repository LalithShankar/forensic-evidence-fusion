"""Report draft generation and listing API routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth_deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.report import GenerateReportRequest, ReportDraftPublic
from app.services.report_service import generate_report_draft, get_report, list_reports

router = APIRouter(tags=["reports"])


@router.post(
    "/cases/{case_id}/reports/generate",
    response_model=ReportDraftPublic,
    status_code=status.HTTP_201_CREATED,
)
def post_generate_report(
    case_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    payload: GenerateReportRequest | None = None,
) -> ReportDraftPublic:
    """Generate or replace a deterministic draft report for contributor+ users."""
    title = payload.title if payload else None
    report = generate_report_draft(db, current_user, case_id, title=title)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or inaccessible",
        )
    return ReportDraftPublic.model_validate(report)


@router.get(
    "/cases/{case_id}/reports",
    response_model=list[ReportDraftPublic],
)
def get_reports(
    case_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ReportDraftPublic]:
    """List report drafts for viewer+ users."""
    reports = list_reports(db, current_user, case_id)
    if reports is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or inaccessible",
        )
    return [ReportDraftPublic.model_validate(report) for report in reports]


@router.get(
    "/cases/{case_id}/reports/{report_id}",
    response_model=ReportDraftPublic,
)
def get_report_detail(
    case_id: uuid.UUID,
    report_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ReportDraftPublic:
    """Return one report draft."""
    report = get_report(db, current_user, case_id, report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found or inaccessible",
        )
    return ReportDraftPublic.model_validate(report)
