"""Pagination query parameters mapping and validation helper."""

from __future__ import annotations

from fastapi import Query

__all__ = ["PaginationParams"]


class PaginationParams:
    """Stateless pagination container validating offset inputs."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page index offset (must be >= 1)."),
        page_size: int = Query(
            20,
            ge=1,
            le=100,
            description="Number of listings per page (must be 1-100).",
        ),
    ) -> None:
        """Validate pagination inputs and initialize bounds.

        Args:
            page: Requested page count.
            page_size: Number of items per page.

        Raises:
            ValueError: If bounds are exceeded.
        """
        if page < 1:
            raise ValueError("Page index must be greater than or equal to 1.")
        if page_size < 1:
            raise ValueError("Page size must be greater than or equal to 1.")
        if page_size > 100:
            raise ValueError("Page size must not exceed the limit of 100.")

        self.page = page
        self.page_size = page_size

    @property
    def skip(self) -> int:
        """Database skip record offset."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Database limit size constraint."""
        return self.page_size
