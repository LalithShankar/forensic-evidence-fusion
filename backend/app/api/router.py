"""Top-level API router aggregating feature routers."""

from fastapi import APIRouter, Depends

from app.api.auth import router as auth_router
from app.api.cases import router as cases_router
from app.core.config import Settings, get_settings

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(cases_router)


@api_router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    """Health check endpoint for local dev, load balancers, and CI smoke tests."""
    return {
        "status": "ok",
        "app_env": settings.app_env,
        "secrets_source": settings.secrets_source,
    }
