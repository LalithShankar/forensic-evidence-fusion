"""Structured, secret-safe logging for the API."""

from __future__ import annotations

import json
import logging
import re
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)
case_id_var: ContextVar[str | None] = ContextVar("case_id", default=None)
artifact_id_var: ContextVar[str | None] = ContextVar("artifact_id", default=None)

_SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"(?i)(secret[_-]?key|password|token|api[_-]?key)\s*[:=]\s*(\S+)"),
        r"\1=<redacted>",
    ),
    (re.compile(r"(?i)Bearer\s+\S+"), "Bearer <redacted>"),
    (re.compile(r"(?i)authorization\s*[:=]\s*\S+"), "authorization=<redacted>"),
]


def redact_secrets(value: str) -> str:
    """Remove secret-like substrings from log message text."""
    result = value
    for pattern, replacement in _SECRET_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


class StructuredJsonFormatter(logging.Formatter):
    """Emit one JSON object per log line with request and domain context."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "message": redact_secrets(record.getMessage()),
            "logger": record.name,
        }
        if request_id := request_id_var.get():
            payload["request_id"] = request_id
        if user_id := user_id_var.get():
            payload["user_id"] = user_id
        if case_id := case_id_var.get():
            payload["case_id"] = case_id
        if artifact_id := artifact_id_var.get():
            payload["artifact_id"] = artifact_id
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str = "info") -> None:
    """Configure root logger with structured JSON output."""
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJsonFormatter())
    root.setLevel(level.upper())
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger using the structured configuration."""
    return logging.getLogger(name)


def bind_log_context(
    *,
    request_id: str | None = None,
    user_id: str | None = None,
    case_id: str | None = None,
    artifact_id: str | None = None,
) -> None:
    """Attach correlation and domain IDs to subsequent log lines in this context."""
    if request_id is not None:
        request_id_var.set(request_id)
    if user_id is not None:
        user_id_var.set(user_id)
    if case_id is not None:
        case_id_var.set(case_id)
    if artifact_id is not None:
        artifact_id_var.set(artifact_id)


def clear_log_context() -> None:
    """Reset context variables after a request completes."""
    request_id_var.set(None)
    user_id_var.set(None)
    case_id_var.set(None)
    artifact_id_var.set(None)
