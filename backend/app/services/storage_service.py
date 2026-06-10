"""Local raw file preservation (Epic 7 — Azure swap in Epic 8)."""

from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

from app.core.config import Settings, get_settings


class StorageError(Exception):
    """Raised when raw preservation fails."""


class LocalStorageService:
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

        safe_name = Path(original_filename).name
        if not safe_name:
            raise StorageError("Invalid filename")

        relative_dir = Path("raw") / str(case_id) / str(artifact_id)
        destination_dir = self._data_root / relative_dir
        destination_dir.mkdir(parents=True, exist_ok=True)

        relative_path = relative_dir / safe_name
        destination_file = self._data_root / relative_path
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
        return str(relative_path), digest


def get_storage_service(settings: Settings | None = None) -> LocalStorageService:
    """Build a storage service from application settings."""
    active_settings = settings or get_settings()
    return LocalStorageService(Path(active_settings.data_root))
