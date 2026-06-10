"""Search chunk builder tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.models.artifact import PROVENANCE_UNKNOWN, Artifact, ArtifactStatus
from app.models.case import Case, CaseScenarioType
from app.models.case_membership import CaseAccessLevel, CaseMembership
from app.models.event import EvidenceEvent, ReviewStatus
from app.models.readable_view import ReadableView, ReadableViewStatus, ReadableViewType
from app.models.search_chunk import IndexStatus
from app.services.indexing.chunk_service import build_chunks_for_artifact
from app.services.storage_paths import StorageNamespace
from app.services.storage_service import LocalStorageBackend
from tests.test_auth import create_test_user


@pytest.fixture
def storage(tmp_path: Path) -> LocalStorageBackend:
    return LocalStorageBackend(tmp_path)


def _seed_case(db_session: Session) -> tuple[Case, Artifact]:
    user = create_test_user(db_session, email="chunk-test@local.dev")

    case = Case(
        name="Chunk Case",
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

    artifact = Artifact(
        case_id=case.id,
        original_filename="notes.txt",
        file_size_bytes=100,
        file_extension="txt",
        mime_type="text/plain",
        status=ArtifactStatus.ready_for_transformation,
        source_group="ThirdParty",
        source_family=PROVENANCE_UNKNOWN,
        artifact_type=PROVENANCE_UNKNOWN,
        collection_method=PROVENANCE_UNKNOWN,
        parser_class=PROVENANCE_UNKNOWN,
    )
    db_session.add(artifact)
    db_session.commit()
    db_session.refresh(case)
    db_session.refresh(artifact)
    return case, artifact


def test_readable_chunks_include_source_linkage(
    db_session: Session,
    storage: LocalStorageBackend,
) -> None:
    case, artifact = _seed_case(db_session)
    storage_path = storage.write_output(
        case.id,
        artifact.id,
        "notes_readable.txt",
        b"Alice confirmed transfer on 2024-06-01. " * 30,
        StorageNamespace.readable,
    )
    view = ReadableView(
        artifact_id=artifact.id,
        view_type=ReadableViewType.extracted_text.value,
        storage_path=storage_path,
        status=ReadableViewStatus.generated.value,
    )
    db_session.add(view)
    db_session.commit()

    chunks = build_chunks_for_artifact(db_session, case.id, artifact.id, storage)
    assert len(chunks) >= 2
    assert all(chunk.case_id == case.id for chunk in chunks)
    assert all(chunk.artifact_id == artifact.id for chunk in chunks)
    assert all(chunk.source_group == "ThirdParty" for chunk in chunks)
    assert all(chunk.provenance_pointer for chunk in chunks)
    assert all(chunk.index_status == IndexStatus.pending.value for chunk in chunks)


def test_event_summary_chunks_include_filter_metadata(
    db_session: Session,
    storage: LocalStorageBackend,
) -> None:
    case, artifact = _seed_case(db_session)
    event = EvidenceEvent(
        case_id=case.id,
        artifact_id=artifact.id,
        event_type="message_sent",
        title="Message from Alice",
        description="Transfer confirmed",
        provenance_pointer="row:0",
        source_confidence=0.8,
        review_status=ReviewStatus.pending.value,
    )
    db_session.add(event)
    db_session.commit()

    chunks = build_chunks_for_artifact(db_session, case.id, artifact.id, storage)
    event_chunks = [chunk for chunk in chunks if chunk.event_id == event.id]
    assert len(event_chunks) == 1
    metadata = event_chunks[0].filter_metadata or {}
    assert metadata.get("event_type") == "message_sent"
    assert metadata.get("event_id") == str(event.id)
