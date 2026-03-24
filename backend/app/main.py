from __future__ import annotations

from fastapi import APIRouter, FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.projects import router as projects_router
from app.api.routes.workspace import router as workspace_router
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.state.settings = settings

    api_router = APIRouter(prefix="/api")
    api_router.include_router(auth_router)
    api_router.include_router(health_router)
    api_router.include_router(projects_router)
    api_router.include_router(workspace_router)
    app.include_router(api_router)

    return app


app = create_app()
