"""FastAPI application entrypoint."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import (
    bind_log_context,
    clear_log_context,
    configure_logging,
    get_logger,
)
from app.db.session import dispose_engine, init_db_connection

settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize shared resources on startup and release them on shutdown."""
    init_db_connection(settings)
    yield
    dispose_engine()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
request_logger = get_logger("app.request")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.middleware("http")
async def structured_request_logging(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Attach a correlation ID and emit structured request lifecycle logs."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    bind_log_context(request_id=request_id)
    request_logger.info(
        "request_started method=%s path=%s",
        request.method,
        request.url.path,
    )

    try:
        response = await call_next(request)
    except Exception:
        request_logger.exception(
            "request_failed method=%s path=%s",
            request.method,
            request.url.path,
        )
        clear_log_context()
        raise

    response.headers["X-Request-ID"] = request_id
    request_logger.info(
        "request_completed method=%s path=%s status=%s",
        request.method,
        request.url.path,
        response.status_code,
    )
    clear_log_context()
    return response
