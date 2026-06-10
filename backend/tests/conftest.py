"""Shared pytest fixtures for database-backed tests."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import reset_settings_cache
from app.db.base import Base
from app.db.session import reset_engine_cache
from app.models import (  # noqa: F401
    Artifact,
    AuditLog,
    Case,
    CaseMembership,
    ReadableView,
    StructuredDataset,
    TransformationRecord,
    User,
)

# Ensure tests never require a production Postgres instance at import time.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("APP_ENV", "local")


@pytest.fixture(autouse=True)
def reset_cached_db_state() -> Generator[None, None, None]:
    """Ensure each test starts with a clean settings/engine cache."""
    reset_settings_cache()
    reset_engine_cache()
    yield
    reset_settings_cache()
    reset_engine_cache()


@pytest.fixture
def sqlite_database_url(tmp_path: Path) -> str:
    """Return a file-backed SQLite URL for isolated migration tests."""
    db_path = tmp_path / "test.db"
    return f"sqlite:///{db_path}"


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a SQLAlchemy session backed by an in-memory SQLite database."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
