"""Storage backends for raw artifact preservation (local filesystem or Azure Blob)."""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Protocol, runtime_checkable

from azure.storage.blob import BlobServiceClient

from app.core.config import Settings, get_settings
from app.services.storage_paths import StorageNamespace, build_object_key


class StorageError(Exception):
    """Raised when raw preservation fails."""


@runtime_checkable
class StorageBackend(Protocol):
    """Interface for swapping local and cloud storage without API changes."""

    def preserve_raw(
        self,
        case_id: uuid.UUID,
        artifact_id: uuid.UUID,
        original_filename: str,
        content: bytes,
    ) -> tuple[str, str]:
        """Store bytes unchanged and return storage path/key + SHA-256 hex digest."""
        ...


class LocalStorageBackend:
    """Write raw artifact bytes to a configured local data directory."""

    def __init__(self, data_root: Path) -> None:
        self._data_root = data_root

    @property
    def data_root(self) -> Path:
        return self._data_root

    def preserve_raw(
        self,
        case_id: uuid.UUID,
        artifact_id: uuid.UUID,
        original_filename: str,
        content: bytes,
    ) -> tuple[str, str]:
        """Store bytes unchanged and return relative path + SHA-256 hex digest."""
        if not content:
            raise StorageError("Cannot preserve empty file content")

        object_key = build_object_key(
            case_id,
            artifact_id,
            original_filename,
            StorageNamespace.raw,
        )

        destination_file = self._data_root / object_key
        destination_file.parent.mkdir(parents=True, exist_ok=True)
        temp_file = destination_file.with_suffix(destination_file.suffix + ".tmp")

        try:
            temp_file.write_bytes(content)
            if temp_file.stat().st_size != len(content):
                raise StorageError("Stored file size does not match upload size")
            temp_file.replace(destination_file)
        except OSError as exc:
            temp_file.unlink(missing_ok=True)
            raise StorageError("Failed to write raw artifact") from exc

        digest = hashlib.sha256(content).hexdigest()
        return object_key, digest


class AzureBlobStorageBackend:
    """Upload raw artifact bytes to Azure Blob Storage (or Azurite locally)."""

    def __init__(
        self,
        connection_string: str,
        container_name: str,
        *,
        blob_service_client: BlobServiceClient | None = None,
    ) -> None:
        self._container_name = container_name
        self._client = blob_service_client or BlobServiceClient.from_connection_string(
            connection_string
        )

    def preserve_raw(
        self,
        case_id: uuid.UUID,
        artifact_id: uuid.UUID,
        original_filename: str,
        content: bytes,
    ) -> tuple[str, str]:
        """Upload bytes unchanged and return blob key + SHA-256 hex digest."""
        if not content:
            raise StorageError("Cannot preserve empty file content")

        object_key = build_object_key(
            case_id,
            artifact_id,
            original_filename,
            StorageNamespace.raw,
        )
        digest = hashlib.sha256(content).hexdigest()

        try:
            blob_client = self._client.get_blob_client(
                container=self._container_name,
                blob=object_key,
            )
            blob_client.upload_blob(content, overwrite=True)
        except Exception as exc:
            raise StorageError("Failed to upload raw artifact to blob storage") from exc

        return object_key, digest


def get_storage_service(settings: Settings | None = None) -> StorageBackend:
    """Build the active storage backend from application settings."""
    active_settings = settings or get_settings()

    if active_settings.is_deployed:
        if not active_settings.azure_storage_connection_string:
            msg = (
                "AZURE_STORAGE_CONNECTION_STRING must be set when APP_ENV=deployed; "
                "blob storage is required in deployed environments."
            )
            raise ValueError(msg)
        return AzureBlobStorageBackend(
            active_settings.azure_storage_connection_string,
            active_settings.azure_storage_container,
        )

    if active_settings.azure_storage_connection_string:
        return AzureBlobStorageBackend(
            active_settings.azure_storage_connection_string,
            active_settings.azure_storage_container,
        )

    return LocalStorageBackend(Path(active_settings.data_root))
