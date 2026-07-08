"""Export all API routers."""

from __future__ import annotations

from app.api.routers.health import router as health_router
from app.api.routers.internships import router as internships_router
from app.api.routers.notifications import router as notifications_router
from app.api.routers.pipeline import router as pipeline_router

__all__ = [
    "health_router",
    "internships_router",
    "notifications_router",
    "pipeline_router",
]
