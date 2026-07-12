"""Repository for saved internship entities."""

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from sqlalchemy import delete

from app.models.saved_job import SavedJob


class SavedJobRepository:
    """Handles database operations for saved internships."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository.

        Args:
            session: SQLAlchemy database session.
        """
        self._session = session

    def add(self, job: SavedJob) -> SavedJob:
        self._session.add(job)
        self._session.flush()
        return job

    def delete(self, job_id: int) -> None:
        stmt = delete(SavedJob).where(SavedJob.id == job_id)
        self._session.execute(stmt)
        self._session.flush()

    def get_by_user_and_internship(
        self, user_id: int, internship_id: int
    ) -> SavedJob | None:
        """Retrieve a specific saved job mapping by user and internship ID."""
        stmt = select(SavedJob).where(
            SavedJob.user_id == user_id, SavedJob.internship_id == internship_id
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def get_user_saved_jobs(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> Sequence[SavedJob]:
        """Get all saved jobs for a user, eagerly loading the internship details.

        Args:
            user_id: ID of the user.
            skip: Pagination offset.
            limit: Pagination limit.

        Returns:
            Sequence of SavedJob instances.
        """
        stmt = (
            select(SavedJob)
            .where(SavedJob.user_id == user_id)
            .options(joinedload(SavedJob.internship))
            .order_by(SavedJob.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return self._session.execute(stmt).scalars().all()
