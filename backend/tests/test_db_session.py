"""Tests for database connection initialization and Alembic migrations."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import reset_settings_cache
from app.db.session import (
    dispose_engine,
    get_engine,
    init_db_connection,
    reset_engine_cache,
)
from app.main import app


def test_init_db_connection_uses_configured_database_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite:///:memory:",
    )
    reset_settings_cache()
    reset_engine_cache()

    init_db_connection()

    engine = get_engine()
    assert engine.url.drivername == "sqlite"


def test_app_startup_initializes_database_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    reset_settings_cache()
    reset_engine_cache()

    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        engine = get_engine()
        assert engine.url.drivername == "sqlite"

    dispose_engine()


def test_alembic_upgrade_creates_schema(sqlite_database_url: str) -> None:
    backend_root = Path(__file__).resolve().parents[1]
    alembic_cfg = Config(str(backend_root / "alembic.ini"))
    os.environ["ALEMBIC_DATABASE_URL"] = sqlite_database_url

    command.upgrade(alembic_cfg, "head")

    engine = get_engine(sqlite_database_url)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    assert {"users", "cases", "artifacts", "audit_log"}.issubset(tables)
    dispose_engine()


def test_test_session_does_not_require_production_credentials(
    monkeypatch: pytest.MonkeyPatch,
    db_session: Session,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    reset_settings_cache()

    assert db_session.bind is not None
    assert db_session.bind.url.drivername == "sqlite"
