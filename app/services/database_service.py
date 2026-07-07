"""Database service layer for coordinating Internship persistence."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING

from app.core.logger import logger
from app.database.repository import InternshipRepository
from app.database.session import get_session

if TYPE_CHECKING:
    from app.models.internship import Internship

__all__ = ["DatabaseService"]


class DatabaseService:
    """Service responsible for Internship database operations.

    This service manages database sessions and delegates persistence
    operations to InternshipRepository.
    """

    @contextmanager
    def _repository(self) -> Generator[InternshipRepository, None, None]:
        """Provide a repository with a managed database session."""
        with get_session() as session:
            yield InternshipRepository(session)

    def save(self, job: Internship) -> Internship:
        """Persist a single internship.

        Args:
            job: Internship instance to persist.

        Returns:
            The persisted Internship instance.

        Raises:
            ValueError: If the provided job is None.
        """
        if job is None:
            raise ValueError("job must not be None")

        with self._repository() as repo:
            saved = repo.add(job)

        logger.info(
            "Saved internship | company={} | title={} | url={}",
            saved.company,
            saved.title,
            saved.url,
        )

        return saved

    def save_many(
        self,
        jobs: list[Internship],
    ) -> list[Internship]:
        """Persist multiple internships.

        Args:
            jobs: Internship instances to persist.

        Returns:
            Persisted Internship instances.
        """
        if not jobs:
            logger.debug("No internship listings supplied for bulk save.")
            return []

        with self._repository() as repo:
            saved = repo.add_many(jobs)

        logger.info("Saved {} internship listings.", len(saved))

        return saved

    def exists(self, url: str) -> bool:
        """Check whether a listing exists.

        Args:
            url: Canonical internship URL.

        Returns:
            True if the listing exists.

        Raises:
            ValueError: If URL is empty.
        """
        url = url.strip()

        if not url:
            raise ValueError("url must not be empty")

        with self._repository() as repo:
            exists = repo.exists(url)

        logger.debug("Checked existence for '{}': {}", url, exists)

        return exists

    def get_all(self) -> list[Internship]:
        """Retrieve every stored internship.

        Returns:
            All stored Internship objects.
        """
        with self._repository() as repo:
            jobs = repo.get_all()

        logger.info("Retrieved {} internship listings.", len(jobs))

        return jobs

    def count(self) -> int:
        """Return the total number of internships.

        Returns:
            Total Internship count.
        """
        with self._repository() as repo:
            total = repo.count()

        logger.debug("Current internship count: {}", total)

        return total

    def delete(self, job: Internship) -> None:
        """Delete a single internship.

        Args:
            job: Internship instance to delete.

        Raises:
            ValueError: If job is None.
        """
        if job is None:
            raise ValueError("job must not be None")

        with self._repository() as repo:
            repo.delete(job)

        logger.info(
            "Deleted internship | company={} | title={} | url={}",
            job.company,
            job.title,
            job.url,
        )

    def delete_all(self) -> int:
        """Delete every internship from the database.

        Returns:
            Number of deleted records.
        """
        with self._repository() as repo:
            deleted = repo.delete_all()

        logger.info("Deleted {} internship listings.", deleted)

        return deleted
