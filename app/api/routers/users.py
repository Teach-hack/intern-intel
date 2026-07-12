"""Router for user-specific operations (e.g. saved jobs, profile management)."""

from typing import List, Any

from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_active_user, get_saved_job_service
from app.api.pagination import PaginationParams
from app.api.schemas.saved_job import SavedJobResponse
from app.models.user import User
from app.services.saved_job_service import SavedJobService

router = APIRouter(tags=["Users"])


@router.get(
    "/users/me/saved-jobs",
    response_model=List[SavedJobResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Saved Internships",
)
async def get_saved_jobs(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    saved_job_service: SavedJobService = Depends(get_saved_job_service),
) -> Any:
    """Retrieve paginated saved internships for the current user."""
    return list(
        saved_job_service.get_user_saved_jobs(
            user_id=current_user.id,
            skip=pagination.skip,
            limit=pagination.limit,
        )
    )


@router.post(
    "/users/me/saved-jobs/{internship_id}",
    response_model=SavedJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save Internship",
)
async def save_job(
    internship_id: int,
    current_user: User = Depends(get_current_active_user),
    saved_job_service: SavedJobService = Depends(get_saved_job_service),
) -> Any:
    """Save an internship to the current user's saved list."""
    return saved_job_service.save_job(
        user_id=current_user.id,
        internship_id=internship_id,
    )


@router.delete(
    "/users/me/saved-jobs/{internship_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove Saved Internship",
)
async def remove_saved_job(
    internship_id: int,
    current_user: User = Depends(get_current_active_user),
    saved_job_service: SavedJobService = Depends(get_saved_job_service),
) -> None:
    """Remove an internship from the current user's saved list."""
    saved_job_service.remove_saved_job(
        user_id=current_user.id,
        internship_id=internship_id,
    )
