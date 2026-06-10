"""Report draft generation service tests."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.case import Case, CaseScenarioType
from app.models.case_membership import CaseAccessLevel, CaseMembership
from app.models.claim import Claim
from app.models.user import User
from app.services.report_service import generate_report_draft, get_report, list_reports
from tests.test_auth import create_test_user


def _create_case(db_session: Session, user: User) -> Case:
    case = Case(
        name="Report test case",
        scenario_type=CaseScenarioType.financial_fraud,
        created_by=user.id,
    )
    db_session.add(case)
    db_session.flush()
    db_session.add(
        CaseMembership(
            case_id=case.id,
            user_id=user.id,
            access_level=CaseAccessLevel.manager,
        )
    )
    db_session.commit()
    db_session.refresh(case)
    return case


def test_generate_report_includes_all_sections(
    db_session: Session,
) -> None:
    user = create_test_user(db_session, email="report-sections@local.dev")
    case = _create_case(db_session, user)

    claim = Claim(
        case_id=case.id,
        claim_text="Alice transferred funds on 2024-06-01.",
        created_by=user.id,
    )
    db_session.add(claim)
    db_session.commit()

    report = generate_report_draft(db_session, user, case.id)
    assert report is not None
    assert report.status == "draft"
    assert report.content_json is not None

    section_keys = [section["key"] for section in report.content_json["sections"]]
    assert section_keys == [
        "timeline_summary",
        "claim_matrix",
        "limitations",
        "source_appendix",
    ]

    claim_section = report.content_json["sections"][1]["content"]["claims"]
    assert len(claim_section) == 1
    assert claim_section[0]["claim_text"] == claim.claim_text


def test_regenerate_replaces_existing_draft(
    db_session: Session,
) -> None:
    user = create_test_user(db_session, email="report-regen@local.dev")
    case = _create_case(db_session, user)

    first = generate_report_draft(db_session, user, case.id, title="First draft")
    assert first is not None
    first_id = first.id

    second = generate_report_draft(db_session, user, case.id, title="Second draft")
    assert second is not None
    assert second.id == first_id
    assert second.title == "Second draft"

    reports = list_reports(db_session, user, case.id)
    assert reports is not None
    assert len(reports) == 1


def test_generate_report_denied_for_inaccessible_case(
    db_session: Session,
) -> None:
    owner = create_test_user(db_session, email="report-owner@local.dev")
    outsider = create_test_user(db_session, email="report-outsider@local.dev")
    case = _create_case(db_session, owner)

    report = generate_report_draft(db_session, outsider, case.id)
    assert report is None


def test_empty_case_report_has_zero_counts(
    db_session: Session,
) -> None:
    user = create_test_user(db_session, email="report-empty@local.dev")
    case = _create_case(db_session, user)

    report = generate_report_draft(db_session, user, case.id)
    assert report is not None

    timeline = report.content_json["sections"][0]["content"]
    assert timeline["event_count"] == 0
    assert timeline["date_range"]["start"] is None


def test_get_report_requires_case_access(
    db_session: Session,
) -> None:
    owner = create_test_user(db_session, email="report-get-owner@local.dev")
    outsider = create_test_user(db_session, email="report-get-outsider@local.dev")
    case = _create_case(db_session, owner)
    report = generate_report_draft(db_session, owner, case.id)
    assert report is not None

    denied = get_report(db_session, outsider, case.id, report.id)
    assert denied is None


def test_get_report_wrong_case_returns_none(
    db_session: Session,
) -> None:
    user = create_test_user(db_session, email="report-wrong-case@local.dev")
    case_a = _create_case(db_session, user)
    case_b = _create_case(db_session, user)
    report = generate_report_draft(db_session, user, case_a.id)
    assert report is not None

    wrong = get_report(db_session, user, case_b.id, report.id)
    assert wrong is None
