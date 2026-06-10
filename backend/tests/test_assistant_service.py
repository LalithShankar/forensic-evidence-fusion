"""Assistant service tests."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_llm, get_search, get_storage
from app.db.session import get_db
from app.main import app
from app.schemas.assistant import AssistantAskInput
from app.services.assistant_service import ask, list_assistant_logs
from app.services.indexing.indexing_service import index_case
from app.services.indexing.search_backend import InMemorySearchBackend
from app.services.llm_backend import MockLLMBackend
from app.services.storage_service import LocalStorageBackend
from tests.test_auth import create_test_user
from tests.test_indexing import _seed_indexable_case


@pytest.fixture
def backends() -> tuple[InMemorySearchBackend, MockLLMBackend]:
    return InMemorySearchBackend(), MockLLMBackend()


def test_ask_returns_grounded_answer_with_sources(
    db_session: Session,
    tmp_path: Path,
    backends: tuple[InMemorySearchBackend, MockLLMBackend],
) -> None:
    search_backend, llm_backend = backends
    storage = LocalStorageBackend(tmp_path)
    user = create_test_user(db_session)
    case = _seed_indexable_case(db_session, storage, user.id)
    index_case(db_session, user, case.id, storage, search_backend)

    result = ask(
        db_session,
        user,
        case.id,
        AssistantAskInput(question="What did Alice send?"),
        search_backend,
        llm_backend,
    )
    assert result is not None
    assert not result.insufficient_evidence
    assert result.source_references
    assert "Alice" in result.answer_text or "evidence" in result.answer_text.lower()


def test_ask_refuses_when_no_relevant_evidence(
    db_session: Session,
    backends: tuple[InMemorySearchBackend, MockLLMBackend],
) -> None:
    search_backend, llm_backend = backends
    user = create_test_user(db_session, email="empty@local.dev")
    from app.models.case import Case, CaseScenarioType
    from app.models.case_membership import CaseAccessLevel, CaseMembership

    case = Case(
        name="Empty",
        scenario_type=CaseScenarioType.general_investigation,
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

    result = ask(
        db_session,
        user,
        case.id,
        AssistantAskInput(question="What happened?"),
        search_backend,
        llm_backend,
    )
    assert result is not None
    assert result.insufficient_evidence
    assert "Insufficient evidence" in result.answer_text


def test_case_isolation_denies_other_case(
    db_session: Session,
    tmp_path: Path,
    backends: tuple[InMemorySearchBackend, MockLLMBackend],
) -> None:
    search_backend, llm_backend = backends
    storage = LocalStorageBackend(tmp_path)
    owner = create_test_user(db_session, email="owner@local.dev")
    outsider = create_test_user(db_session, email="outsider@local.dev")
    case = _seed_indexable_case(db_session, storage, owner.id)
    index_case(db_session, owner, case.id, storage, search_backend)

    assert (
        ask(
            db_session,
            outsider,
            case.id,
            AssistantAskInput(question="Alice transfer"),
            search_backend,
            llm_backend,
        )
        is None
    )


@pytest.fixture
def client(
    db_session: Session,
    tmp_path: Path,
    backends: tuple[InMemorySearchBackend, MockLLMBackend],
) -> Generator[TestClient, None, None]:
    search_backend, llm_backend = backends
    storage = LocalStorageBackend(tmp_path)

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_storage] = lambda: storage
    app.dependency_overrides[get_search] = lambda: search_backend
    app.dependency_overrides[get_llm] = lambda: llm_backend
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_assistant_logs_record_retrieval_metadata(
    db_session: Session,
    tmp_path: Path,
    backends: tuple[InMemorySearchBackend, MockLLMBackend],
) -> None:
    search_backend, llm_backend = backends
    storage = LocalStorageBackend(tmp_path)
    user = create_test_user(db_session)
    case = _seed_indexable_case(db_session, storage, user.id)
    index_case(db_session, user, case.id, storage, search_backend)
    ask(
        db_session,
        user,
        case.id,
        AssistantAskInput(question="Alice transfer"),
        search_backend,
        llm_backend,
    )

    logs = list_assistant_logs(db_session, user, case.id)
    assert logs is not None
    assert len(logs) == 1
    assert logs[0].retrieval_chunk_ids
