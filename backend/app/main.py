"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint for local dev and CI smoke tests."""
    return {
        "status": "ok",
        "app_env": settings.app_env,
        "secrets_source": settings.secrets_source,
    }
