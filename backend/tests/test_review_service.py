"""Unit tests for review_service (no HTTP layer)."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.orm import Session

from app.models.artifact import Artifact, ArtifactStatus
from app.models.case import Case, CaseScenarioType
from app.models.case_membership import CaseAccessLevel, CaseMembership
from app.schemas.review import ReviewActionInput
from app.services import review_service
from tests.test_auth import create_test_user


def _case_with_manager(db: Session, user_id: uuid.UUID) -> Case:
    case = Case(
        name="Review Svc Case",
        scenario_type=CaseScenarioType.general_investigation,
        created_by=user_id,
    )
    db.add(case)
    db.flush()
    db.add(
        CaseMembership(
            case_id=case.id,
            user_id=user_id,
            access_level=CaseAccessLevel.manager,
        )
    )
    db.commit()
    db.refresh(case)
    return case


def _artifact(db: Session, case_id: uuid.UUID, status: ArtifactStatus) -> Artifact:
    artifact = Artifact(
        case_id=case_id,
        original_filename="item.bin",
        file_size_bytes=4,
        file_extension="bin",
        mime_type="application/octet-stream",
        storage_path="raw/x/y/item.bin",
        content_hash="deadbeef",
        status=status,
        suggested_source_group="Generic",
        suggested_source_family="Binary",
        suggested_artifact_type="unknown",
        classification_confidence=0.25,
        classification_reason="No matching classification rule",
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact


def test_list_review_queue_includes_needs_review_and_blocked(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = _case_with_manager(db_session, user.id)
    _artifact(db_session, case.id, ArtifactStatus.needs_review)
    blocked = _artifact(db_session, case.id, ArtifactStatus.blocked)
    blocked.blocker_notes = "Hash mismatch"
    db_session.commit()
    _artifact(db_session, case.id, ArtifactStatus.preserved)  # excluded

    items = review_service.list_review_queue(db_session, user, case.id)

    assert items is not None
    assert len(items) == 2
    reasons = {item.review_reason for item in items}
    assert any("Hash mismatch" in reason for reason in reasons)


def test_list_review_queue_denied_without_access_returns_none(
    db_session: Session,
) -> None:
    owner = create_test_user(db_session, email="owner@local.dev")
    outsider = create_test_user(db_session, email="outsider@local.dev")
    case = _case_with_manager(db_session, owner.id)

    assert review_service.list_review_queue(db_session, outsider, case.id) is None


def test_approve_promotes_to_ready_and_fills_suggestion(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    case = _case_with_manager(db_session, user.id)
    artifact = _artifact(db_session, case.id, ArtifactStatus.needs_review)

    updated = review_service.apply_review_action(
        db_session,
        user,
        case.id,
        artifact.id,
        ReviewActionInput(action="approve"),
    )

    assert updated is not None
    assert updated.status == ArtifactStatus.ready_for_transformation
    assert updated.source_group == "Generic"


def test_preserve_only_excludes_from_transformation(db_session: Session) -> None:
    user = create_test_user(db_session)
    case = _case_with_manager(db_session, user.id)
    artifact = _artifact(db_session, case.id, ArtifactStatus.needs_review)

    updated = review_service.apply_review_action(
        db_session,
        user,
        case.id,
        artifact.id,
        ReviewActionInput(action="preserve_only"),
    )

    assert updated is not None
    assert updated.status == ArtifactStatus.preserve_only


def test_correct_keeps_in_review_and_updates_metadata(db_session: Session) -> None:
    user = create_test_user(db_session)
    case = _case_with_manager(db_session, user.id)
    artifact = _artifact(db_session, case.id, ArtifactStatus.needs_review)

    updated = review_service.apply_review_action(
        db_session,
        user,
        case.id,
        artifact.id,
        ReviewActionInput(
            action="correct",
            source_group="ThirdParty",
            source_family="WhatsApp",
            artifact_type="chat_export",
        ),
    )

    assert updated is not None
    assert updated.status == ArtifactStatus.needs_review
    assert updated.source_group == "ThirdParty"
    assert updated.source_family == "WhatsApp"


def test_invalid_action_raises_value_error(db_session: Session) -> None:
    user = create_test_user(db_session)
    case = _case_with_manager(db_session, user.id)
    artifact = _artifact(db_session, case.id, ArtifactStatus.needs_review)

    with pytest.raises(ValueError):
        review_service.apply_review_action(
            db_session,
            user,
            case.id,
            artifact.id,
            ReviewActionInput(action="explode"),
        )


def test_action_on_missing_artifact_returns_none(db_session: Session) -> None:
    user = create_test_user(db_session)
    case = _case_with_manager(db_session, user.id)

    result = review_service.apply_review_action(
        db_session,
        user,
        case.id,
        uuid.uuid4(),
        ReviewActionInput(action="approve"),
    )
    assert result is None
