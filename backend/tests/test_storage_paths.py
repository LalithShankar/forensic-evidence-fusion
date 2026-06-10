"""Tests for storage object key conventions."""

from __future__ import annotations

import uuid

import pytest

from app.services.storage_paths import (
    InvalidFilenameError,
    StorageNamespace,
    build_object_key,
    sanitize_filename,
)


def test_each_namespace_produces_distinct_prefix() -> None:
    case_id = uuid.uuid4()
    artifact_id = uuid.uuid4()

    raw_key = build_object_key(case_id, artifact_id, "file.bin", StorageNamespace.raw)
    readable_key = build_object_key(
        case_id, artifact_id, "file.bin", StorageNamespace.readable
    )
    structured_key = build_object_key(
        case_id, artifact_id, "file.bin", StorageNamespace.structured
    )

    assert raw_key.startswith("raw/")
    assert readable_key.startswith("readable/")
    assert structured_key.startswith("structured/")
    assert raw_key != readable_key != structured_key


def test_same_inputs_produce_stable_keys() -> None:
    case_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    artifact_id = uuid.UUID("22222222-2222-2222-2222-222222222222")

    first = build_object_key(case_id, artifact_id, "report.pdf", StorageNamespace.raw)
    second = build_object_key(case_id, artifact_id, "report.pdf", StorageNamespace.raw)

    assert first == second
    assert (
        first == "raw/11111111-1111-1111-1111-111111111111/"
        "22222222-2222-2222-2222-222222222222/report.pdf"
    )


def test_raw_key_matches_epic_7_layout() -> None:
    case_id = uuid.uuid4()
    artifact_id = uuid.uuid4()

    key = build_object_key(case_id, artifact_id, "evidence.txt", StorageNamespace.raw)

    assert key == f"raw/{case_id}/{artifact_id}/evidence.txt"


def test_sanitize_filename_uses_basename_only() -> None:
    assert sanitize_filename("/tmp/nested/evidence.pdf") == "evidence.pdf"
    assert sanitize_filename("evidence.pdf") == "evidence.pdf"


def test_sanitize_filename_rejects_empty() -> None:
    with pytest.raises(InvalidFilenameError, match="Invalid filename"):
        sanitize_filename("")
    with pytest.raises(InvalidFilenameError, match="Invalid filename"):
        sanitize_filename("/")
