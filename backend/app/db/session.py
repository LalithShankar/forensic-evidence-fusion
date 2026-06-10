"""Database engine and session management."""

from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings

SessionLocal: sessionmaker[Session] | None = None


@lru_cache
def get_engine(database_url: str | None = None) -> Engine:
    """Return a cached SQLAlchemy engine for the configured DATABASE_URL."""
    url = database_url or get_settings().database_url
    return create_engine(url, pool_pre_ping=True)


def init_db_connection(settings: Settings | None = None) -> None:
    """Initialize the database engine and verify connectivity."""
    global SessionLocal

    active_settings = settings or get_settings()
    engine = get_engine(active_settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    if SessionLocal is None:
        init_db_connection()

    assert SessionLocal is not None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def dispose_engine() -> None:
    """Dispose the cached engine (used in tests and shutdown)."""
    if get_engine.cache_info().currsize:
        get_engine().dispose()
    get_engine.cache_clear()
    reset_session_factory()


def reset_engine_cache() -> None:
    """Clear engine cache and session factory (used in tests)."""
    dispose_engine()


def reset_session_factory() -> None:
    """Reset the module-level session factory."""
    global SessionLocal
    SessionLocal = None
