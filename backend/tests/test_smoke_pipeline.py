"""Full-stack API smoke test for Epics 10–12 (bulk → review → transform).

Runs against TestClient with in-memory DB and local storage — no live server
required. Marked ``smoke`` so it can be invoked via ``pytest -m smoke``.
"""

from __future__ import annotations

import json
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.artifacts import get_storage
from app.db.session import get_db
from app.main import app
from app.models.artifact import ArtifactStatus
from app.models.transformation import TransformationStage, TransformationStatus
from app.services.storage_service import LocalStorageBackend
from tests.test_auth import auth_header, create_test_user
from tests.test_cases import login_token

pytestmark = pytest.mark.smoke


@pytest.fixture
def smoke_client(
    db_session: Session,
    tmp_path: Path,
) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    storage = LocalStorageBackend(tmp_path)

    def override_get_storage() -> LocalStorageBackend:
        return storage

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_storage] = override_get_storage
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_full_pipeline_bulk_review_transform_smoke(
    smoke_client: TestClient,
    db_session: Session,
    tmp_path: Path,
) -> None:
    """Smoke: health → auth → case → bulk upload → review → transform → manifest."""
    client = smoke_client

    # --- Platform health ---
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    # --- Auth ---
    user = create_test_user(db_session, email="smoke@local.dev")
    password = "DevPassword123!"
    login = client.post(
        "/auth/login",
        json={"email": user.email, "password": password},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/auth/me", headers=auth_header(token))
    assert me.status_code == 200
    assert me.json()["email"] == user.email

    ping = client.get("/auth/protected/ping", headers=auth_header(token))
    assert ping.status_code == 200

    # --- Case ---
    case_resp = client.post(
        "/cases",
        headers=auth_header(token),
        json={
            "name": "Smoke pipeline case",
            "scenario_type": "general_investigation",
        },
    )
    assert case_resp.status_code == 201
    case_id = case_resp.json()["id"]

    # --- Epic 10: bulk upload + classification ---
    bulk = client.post(
        f"/cases/{case_id}/artifacts/bulk-upload",
        headers=auth_header(token),
        files=[
            ("files", ("ledger.csv", b"name,amount\nAlice,10", "text/csv")),
            ("files", ("WhatsApp Chat with Bob.txt", b"messages", "text/plain")),
            ("files", ("mystery.bin", b"\x00\x01", "application/octet-stream")),
            ("files", ("empty.txt", b"", "text/plain")),
        ],
    )
    assert bulk.status_code == 201
    bulk_body = bulk.json()
    assert bulk_body["succeeded_count"] == 3
    assert bulk_body["failed_count"] == 1
    assert bulk_body["upload_batch_id"]
    batch_id = bulk_body["upload_batch_id"]

    results_by_name = {item["filename"]: item for item in bulk_body["results"]}
    assert results_by_name["ledger.csv"]["artifact"]["status"] == "preserved"
    assert results_by_name["WhatsApp Chat with Bob.txt"]["artifact"][
        "suggested_source_family"
    ] == "WhatsApp"
    assert results_by_name["mystery.bin"]["artifact"]["status"] == "needs_review"
    assert results_by_name["empty.txt"]["error"] is not None

    csv_id = results_by_name["ledger.csv"]["artifact"]["id"]
    mystery_id = results_by_name["mystery.bin"]["artifact"]["id"]

    artifacts = client.get(
        f"/cases/{case_id}/artifacts",
        headers=auth_header(token),
    )
    assert artifacts.status_code == 200
    listed = artifacts.json()
    assert len(listed) == 3
    assert all(item["upload_batch_id"] == batch_id for item in listed)

    # --- Epic 11: review queue ---
    queue = client.get(
        f"/cases/{case_id}/review-queue",
        headers=auth_header(token),
    )
    assert queue.status_code == 200
    queue_body = queue.json()
    assert queue_body["total"] >= 1
    queue_ids = {item["artifact"]["id"] for item in queue_body["items"]}
    assert mystery_id in queue_ids

    preserve = client.patch(
        f"/cases/{case_id}/review-queue/{mystery_id}",
        headers=auth_header(token),
        json={"action": "preserve_only"},
    )
    assert preserve.status_code == 200
    assert preserve.json()["artifact"]["status"] == ArtifactStatus.preserve_only.value

    approve = client.patch(
        f"/cases/{case_id}/review-queue/{csv_id}",
        headers=auth_header(token),
        json={"action": "approve"},
    )
    assert approve.status_code == 200
    assert (
        approve.json()["artifact"]["status"]
        == ArtifactStatus.ready_for_transformation.value
    )

    empty_queue = client.get(
        f"/cases/{case_id}/review-queue",
        headers=auth_header(token),
    )
    assert empty_queue.json()["total"] == 0

    # --- Epic 12: transformation ---
    transform = client.post(
        f"/cases/{case_id}/artifacts/{csv_id}/transformations/start",
        headers=auth_header(token),
    )
    assert transform.status_code == 201
    transform_body = transform.json()
    record = transform_body["record"]
    assert record["status"] == TransformationStatus.completed.value
    stage_values = {stage for stage in transform_body["stages_completed"]}
    assert TransformationStage.structured_generated.value in stage_values
    assert record["readable_path"]
    assert record["structured_path"]
    assert (tmp_path / record["readable_path"]).exists()
    structured_bytes = (tmp_path / record["structured_path"]).read_bytes()
    structured = json.loads(structured_bytes.decode())
    assert structured["format"] == "csv"
    assert structured["row_count"] == 1

    latest = client.get(
        f"/cases/{case_id}/artifacts/{csv_id}/transformations/latest",
        headers=auth_header(token),
    )
    assert latest.status_code == 200
    assert latest.json()["id"] == record["id"]

    # Idempotent re-run returns same record.
    again = client.post(
        f"/cases/{case_id}/artifacts/{csv_id}/transformations/start",
        headers=auth_header(token),
    )
    assert again.status_code == 201
    assert again.json()["record"]["id"] == record["id"]

    # --- Epic 9 manifest: classification visible ---
    manifest = client.get(
        f"/cases/{case_id}/artifacts/manifest",
        headers=auth_header(token),
    )
    assert manifest.status_code == 200
    manifest_entries = {
        entry["original_filename"]: entry for entry in manifest.json()["artifacts"]
    }
    assert manifest_entries["ledger.csv"]["source_group"] == "Generic"
    assert manifest_entries["WhatsApp Chat with Bob.txt"]["source_family"] == "WhatsApp"


@pytest.mark.smoke
def test_smoke_json_transform_path(
    smoke_client: TestClient,
    db_session: Session,
    tmp_path: Path,
) -> None:
    """Smoke: JSON upload → approve → transform produces readable + structured."""
    client = smoke_client
    user = create_test_user(db_session, email="smoke-json@local.dev")
    token = login_token(client, user)

    case = client.post(
        "/cases",
        headers=auth_header(token),
        json={"name": "JSON smoke", "scenario_type": "general_investigation"},
    )
    assert case.status_code == 201
    case_id = case.json()["id"]

    upload = client.post(
        f"/cases/{case_id}/artifacts/bulk-upload",
        headers=auth_header(token),
        files=[
            (
                "files",
                (
                    "events.json",
                    b'{"event":"login","user":"alice"}',
                    "application/json",
                ),
            ),
        ],
    )
    assert upload.status_code == 201
    artifact_id = upload.json()["results"][0]["artifact"]["id"]

    client.patch(
        f"/cases/{case_id}/review-queue/{artifact_id}",
        headers=auth_header(token),
        json={"action": "approve"},
    )

    result = client.post(
        f"/cases/{case_id}/artifacts/{artifact_id}/transformations/start",
        headers=auth_header(token),
    )
    assert result.status_code == 201
    record = result.json()["record"]
    assert record["status"] == TransformationStatus.completed.value
    assert (tmp_path / record["readable_path"]).exists()
    assert (tmp_path / record["structured_path"]).exists()
