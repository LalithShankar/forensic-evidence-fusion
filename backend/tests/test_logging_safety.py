"""Tests for structured logging safety and context attachment."""

from __future__ import annotations

import json
import logging
from io import StringIO

import pytest
from fastapi.testclient import TestClient

from app.core.logging import (
    StructuredJsonFormatter,
    bind_log_context,
    clear_log_context,
    configure_logging,
    get_logger,
    redact_secrets,
)
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_log_context() -> None:
    clear_log_context()
    yield
    clear_log_context()


def test_redact_secrets_masks_common_patterns() -> None:
    raw = (
        "secret_key=super-secret-value password=abc123 "
        "Bearer eyJhbGciOiJIUzI1NiJ9 token=deadbeef"
    )
    redacted = redact_secrets(raw)

    assert "super-secret-value" not in redacted
    assert "abc123" not in redacted
    assert "eyJhbGciOiJIUzI1NiJ9" not in redacted
    assert "deadbeef" not in redacted
    assert "<redacted>" in redacted


def test_structured_formatter_includes_request_id() -> None:
    bind_log_context(request_id="req-123")
    formatter = StructuredJsonFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )

    payload = json.loads(formatter.format(record))

    assert payload["message"] == "hello"
    assert payload["request_id"] == "req-123"
    assert "timestamp" in payload
    assert payload["level"] == "INFO"


def test_structured_formatter_attaches_domain_context() -> None:
    bind_log_context(
        request_id="req-456",
        user_id="user-1",
        case_id="case-9",
        artifact_id="artifact-42",
    )
    formatter = StructuredJsonFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="artifact processed",
        args=(),
        exc_info=None,
    )

    payload = json.loads(formatter.format(record))

    assert payload["user_id"] == "user-1"
    assert payload["case_id"] == "case-9"
    assert payload["artifact_id"] == "artifact-42"


def test_logger_redacts_secrets_in_emitted_lines() -> None:
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(StructuredJsonFormatter())
    logger = get_logger("test.secret_redaction")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    secret_value = "local-only-secret-token-xyz"
    logger.info("loaded credentials secret_key=%s", secret_value)

    output = stream.getvalue().strip()
    payload = json.loads(output)

    assert secret_value not in output
    assert secret_value not in payload["message"]
    assert "<redacted>" in payload["message"]


def test_request_emits_correlation_id_header() -> None:
    response = client.get("/health", headers={"X-Request-ID": "corr-test-id"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "corr-test-id"


def test_request_generates_correlation_id_when_missing() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")


def test_pipeline_stage_log_includes_required_fields() -> None:
    import uuid
    from unittest.mock import patch

    import app.services.transformation_pipeline as pipeline_module

    with patch.object(pipeline_module._pipeline_logger, "info") as mock_info:
        pipeline_module._log_stage_transition(
            stage="classified",
            artifact_id=uuid.uuid4(),
            case_id=uuid.uuid4(),
            duration_ms=5,
            outcome="running",
        )

    message = mock_info.call_args[0][0]
    assert "pipeline_stage" in message
    assert "outcome=running" in message


def test_pipeline_stage_log_warning_on_blocked() -> None:
    import uuid
    from unittest.mock import patch

    import app.services.transformation_pipeline as pipeline_module

    with patch.object(pipeline_module._pipeline_logger, "warning") as mock_warning:
        pipeline_module._log_stage_transition(
            stage="blocked",
            artifact_id=uuid.uuid4(),
            case_id=uuid.uuid4(),
            duration_ms=50,
            outcome="blocked",
            limitation_notes="Unsupported format",
        )

    message = mock_warning.call_args[0][0]
    assert "limitation_notes=Unsupported format" in message


def test_configure_logging_uses_json_formatter() -> None:
    stream = StringIO()
    configure_logging("info")
    logger = get_logger("test.configure")
    handler = logging.StreamHandler(stream)
    handler.setFormatter(StructuredJsonFormatter())
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False

    bind_log_context(request_id="json-shape-test")
    logger.info("structured line")

    payload = json.loads(stream.getvalue().strip())
    assert isinstance(payload, dict)
    assert payload["request_id"] == "json-shape-test"
