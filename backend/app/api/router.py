"""Top-level API router aggregating feature routers."""

from fastapi import APIRouter, Depends

from app.api.artifacts import router as artifacts_router
from app.api.auth import router as auth_router
from app.api.cases import router as cases_router
from app.api.review_queue import router as review_queue_router
from app.api.readable_views import router as readable_views_router
from app.api.structured_datasets import router as structured_datasets_router
from app.api.transformations import router as transformations_router
from app.core.config import Settings, get_settings

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(cases_router)
api_router.include_router(artifacts_router)
api_router.include_router(review_queue_router)
api_router.include_router(transformations_router)
api_router.include_router(readable_views_router)
api_router.include_router(structured_datasets_router)


@api_router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    """Health check endpoint for local dev, load balancers, and CI smoke tests."""
    return {
        "status": "ok",
        "app_env": settings.app_env,
        "secrets_source": settings.secrets_source,
    }
