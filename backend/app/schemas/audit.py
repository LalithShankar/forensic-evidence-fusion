"""Audit log read API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_SENSITIVE_KEYS = frozenset(
    {
        "password",
        "secret",
        "secret_key",
        "token",
        "api_key",
        "connection_string",
        "authorization",
    }
)


def redact_audit_json(value: dict[str, Any] | None) -> dict[str, Any] | None:
    """Remove sensitive keys from audit JSON blobs before API exposure."""
    if value is None:
        return None
    return {
        key: "<redacted>" if key.lower() in _SENSITIVE_KEYS else nested
        for key, nested in value.items()
    }


class AuditLogPublic(BaseModel):
    """Case audit entry safe for viewer consumption."""

    model_config = ConfigDict(from_attributes=True)

    audit_id: uuid.UUID
    case_id: uuid.UUID | None
    user_id: uuid.UUID
    action: str
    object_type: str
    object_id: uuid.UUID
    before_json: dict[str, Any] | None = None
    after_json: dict[str, Any] | None = None
    timestamp: datetime
    reason: str | None = None

    @classmethod
    def from_audit_row(cls, row: object) -> AuditLogPublic:
        """Build a redacted public payload from an ORM audit row."""
        payload = cls.model_validate(row)
        return payload.model_copy(
            update={
                "before_json": redact_audit_json(payload.before_json),
                "after_json": redact_audit_json(payload.after_json),
            }
        )


class AuditLogListResponse(BaseModel):
    """Paginated audit log list."""

    items: list[AuditLogPublic]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
