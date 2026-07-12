"""Router for dashboard endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_active_user, get_dashboard_service
from app.api.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService
from app.models.user import User

router = APIRouter(tags=["Dashboard"])


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Dashboard Overview",
)
async def get_dashboard(
    current_user: User = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> Any:
    """Retrieve comprehensive dashboard overview statistics."""
    return dashboard_service.get_overview()
