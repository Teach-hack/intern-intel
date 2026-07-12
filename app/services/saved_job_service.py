"""Service layer for Saved Jobs business logic."""

from typing import Sequence
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.database.saved_job_repository import SavedJobRepository
from app.database.repository import InternshipRepository
from app.models.saved_job import SavedJob


class SavedJobService:
    """Business logic for saved internships."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._saved_job_repo = SavedJobRepository(session)
        self._internship_repo = InternshipRepository(session)

    def get_user_saved_jobs(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[SavedJob]:
        """Get paginated saved jobs for a user."""
        return self._saved_job_repo.get_user_saved_jobs(user_id, skip, limit)

    def save_job(self, user_id: int, internship_id: int) -> SavedJob:
        """Save an internship for a user.

        Raises HTTP 404 if internship doesn't exist.
        Raises HTTP 409 if already saved.
        """
        # Validate internship exists
        internship = self._internship_repo.get(internship_id)
        if not internship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Internship not found."
            )

        # Check if already saved
        existing = self._saved_job_repo.get_by_user_and_internship(
            user_id, internship_id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Internship already saved."
            )

        saved_job = SavedJob(user_id=user_id, internship_id=internship_id)
        return self._saved_job_repo.add(saved_job)

    def remove_saved_job(self, user_id: int, internship_id: int) -> None:
        """Remove a saved internship for a user.

        Raises HTTP 404 if not found or doesn't belong to user.
        """
        saved_job = self._saved_job_repo.get_by_user_and_internship(
            user_id, internship_id
        )
        if not saved_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved internship not found.",
            )

        self._saved_job_repo.delete(saved_job.id)
