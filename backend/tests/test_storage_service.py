"""Tests for storage backend abstraction and factory."""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.core.config import DeployedSettings, LocalSettings
from app.services.storage_paths import StorageNamespace
from app.services.storage_service import (
    AzureBlobStorageBackend,
    LocalStorageBackend,
    StorageError,
    get_storage_service,
)


def test_local_write_output_to_readable_namespace(tmp_path: Path) -> None:
    backend = LocalStorageBackend(tmp_path)
    case_id = uuid.uuid4()
    artifact_id = uuid.uuid4()

    key = backend.write_output(
        case_id,
        artifact_id,
        "report_readable.txt",
        b"human readable preview",
        StorageNamespace.readable,
    )

    assert key.startswith("readable/")
    assert (tmp_path / key).read_bytes() == b"human readable preview"


def test_local_write_output_rejects_empty_content(tmp_path: Path) -> None:
    backend = LocalStorageBackend(tmp_path)
    with pytest.raises(StorageError):
        backend.write_output(
            uuid.uuid4(),
            uuid.uuid4(),
            "empty.json",
            b"",
            StorageNamespace.structured,
        )


def test_local_read_raw_round_trip(tmp_path: Path) -> None:
    backend = LocalStorageBackend(tmp_path)
    case_id = uuid.uuid4()
    artifact_id = uuid.uuid4()
    storage_path, _ = backend.preserve_raw(
        case_id,
        artifact_id,
        "data.csv",
        b"a,b\n1,2",
    )

    assert backend.read_raw(storage_path) == b"a,b\n1,2"


def test_local_read_raw_missing_file_raises(tmp_path: Path) -> None:
    backend = LocalStorageBackend(tmp_path)
    with pytest.raises(StorageError):
        backend.read_raw("raw/missing/object/file.bin")


def test_local_preserve_raw_round_trip(tmp_path: Path) -> None:
    backend = LocalStorageBackend(tmp_path)
    case_id = uuid.uuid4()
    artifact_id = uuid.uuid4()
    content = b"%PDF-1.4 preserved bytes"

    storage_path, digest = backend.preserve_raw(
        case_id,
        artifact_id,
        "report.pdf",
        content,
    )

    expected_digest = hashlib.sha256(content).hexdigest()
    assert digest == expected_digest
    assert storage_path == f"raw/{case_id}/{artifact_id}/report.pdf"
    assert (tmp_path / storage_path).read_bytes() == content


def test_factory_returns_local_backend_when_local_without_azure() -> None:
    settings = LocalSettings(
        azure_storage_connection_string=None,
    )

    backend = get_storage_service(settings)

    assert isinstance(backend, LocalStorageBackend)


def test_factory_returns_azure_backend_when_deployed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "deployed")
    monkeypatch.setenv("AZURE_KEY_VAULT_URL", "https://example.vault.azure.net/")
    monkeypatch.setenv(
        "AZURE_STORAGE_CONNECTION_STRING",
        "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=key;EndpointSuffix=core.windows.net",
    )

    settings = DeployedSettings()
    backend = get_storage_service(settings)

    assert isinstance(backend, AzureBlobStorageBackend)


def test_factory_requires_azure_connection_string_when_deployed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "deployed")
    monkeypatch.setenv("AZURE_KEY_VAULT_URL", "https://example.vault.azure.net/")
    monkeypatch.delenv("AZURE_STORAGE_CONNECTION_STRING", raising=False)

    settings = DeployedSettings()

    with pytest.raises(ValueError, match="AZURE_STORAGE_CONNECTION_STRING"):
        get_storage_service(settings)


def test_factory_returns_azure_backend_for_local_with_azurite_string(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "AZURE_STORAGE_CONNECTION_STRING",
        "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
        "AccountKey=key;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;",
    )

    settings = LocalSettings()
    backend = get_storage_service(settings)

    assert isinstance(backend, AzureBlobStorageBackend)


def test_azure_preserve_raw_uploads_blob_with_mock_client() -> None:
    mock_client = MagicMock()
    mock_blob_client = MagicMock()
    mock_client.get_blob_client.return_value = mock_blob_client

    backend = AzureBlobStorageBackend(
        "UseDevelopmentStorage=true",
        "forensic-evidence",
        blob_service_client=mock_client,
    )
    case_id = uuid.uuid4()
    artifact_id = uuid.uuid4()
    content = b"blob payload"

    storage_key, digest = backend.preserve_raw(
        case_id,
        artifact_id,
        "artifact.bin",
        content,
    )

    expected_key = f"raw/{case_id}/{artifact_id}/artifact.bin"
    assert storage_key == expected_key
    assert digest == hashlib.sha256(content).hexdigest()
    mock_client.get_blob_client.assert_called_once_with(
        container="forensic-evidence",
        blob=expected_key,
    )
    mock_blob_client.upload_blob.assert_called_once_with(content, overwrite=True)


def test_preserve_raw_rejects_empty_content(tmp_path: Path) -> None:
    backend = LocalStorageBackend(tmp_path)

    with pytest.raises(StorageError, match="empty"):
        backend.preserve_raw(uuid.uuid4(), uuid.uuid4(), "empty.bin", b"")
