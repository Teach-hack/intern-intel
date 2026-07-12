"""Export all API routers."""

from __future__ import annotations

from app.api.routers.health import router as health_router
from app.api.routers.internships import router as internships_router
from app.api.routers.notifications import router as notifications_router
from app.api.routers.pipeline import router as pipeline_router
from app.api.routers.auth import router as auth_router
from app.api.routers.users import router as users_router
from app.api.routers.dashboard import router as dashboard_router

__all__ = [
    "health_router",
    "internships_router",
    "notifications_router",
    "pipeline_router",
    "auth_router",
    "users_router",
    "dashboard_router",
]
