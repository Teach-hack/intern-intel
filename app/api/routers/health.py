"""Router for retrieving service and system health status."""

from __future__ import annotations

import threading
import time

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.auth.dependencies import verify_api_key
from app.api.dependencies import get_db_session, get_settings
from app.api.schemas.response import HealthResponse
from app.core.settings import Settings
from app.registry import SCRAPER_FACTORIES

router = APIRouter(tags=["Health"])

_START_TIME = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get System Health Metrics",
    description=(
        "Returns the connectivity status of the database, the state of the "
        "scheduler thread, application version, scrapers count, and uptime."
    ),
    dependencies=[Depends(verify_api_key)],
)
async def get_health(
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    """Retrieve detailed health metrics for database, scheduler, and notifications.

    Args:
        session: Injected SQLAlchemy database session.
        settings: Injected settings configuration container.

    Returns:
        HealthResponse containing connectivity and uptime statistics.
    """
    database_status = "disconnected"
    try:
        session.execute(text("SELECT 1"))
        database_status = "connected"
    except Exception:
        pass

    scheduler_status = "stopped"
    for t in threading.enumerate():
        if t.name and "scheduler" in t.name.lower():
            scheduler_status = "running"
            break

    notifications_status = "enabled" if settings.telegram_enabled else "disabled"
    uptime = int(time.time() - _START_TIME)

    return HealthResponse(
        status="healthy",
        database=database_status,
        scheduler=scheduler_status,
        notifications=notifications_status,
        registered_scrapers=len(SCRAPER_FACTORIES),
        version=settings.API_VERSION,
        uptime_seconds=uptime,
    )
