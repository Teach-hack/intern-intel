"""Router for querying, retrieving, and displaying statistics for internships."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.auth.dependencies import verify_api_key
from app.api.dependencies import get_database_service, get_db_session
from app.api.pagination import PaginationParams
from app.api.schemas.internship import InternshipResponse
from app.api.schemas.response import StatsResponse
from app.models.internship import Internship
from app.services.database_service import DatabaseService

router = APIRouter(tags=["Internships"])


@router.get(
    "/internships",
    response_model=list[InternshipResponse],
    status_code=status.HTTP_200_OK,
    summary="List Internship Listings",
    description=(
        "Retrieve stored internship listings with support for filtering, "
        "search, sorting, and pagination boundaries."
    ),
    dependencies=[Depends(verify_api_key)],
)
async def list_internships(
    pagination: PaginationParams = Depends(),
    sort_by: str | None = Query(
        None, description="Field name on the Internship model to sort by."
    ),
    order: str = Query("asc", description="Sort direction: 'asc' or 'desc'."),
    company: str | None = Query(None, description="Filter by hiring company name."),
    location: str | None = Query(
        None, description="Filter by location (substring match)."
    ),
    employment_type: str | None = Query(
        None, description="Filter by employment classification."
    ),
    source: str | None = Query(None, description="Filter by scraper source."),
    search: str | None = Query(
        None, description="Search term matching title, company, or skills."
    ),
    date_from: date | None = Query(
        None, description="Only return listings posted on or after this date."
    ),
    date_to: date | None = Query(
        None, description="Only return listings posted on or before this date."
    ),
    db_service: DatabaseService = Depends(get_database_service),
) -> list[Internship]:
    """Retrieve filtered and paginated list of internship entities.

    Args:
        pagination: Paginated skip/limit boundaries.
        sort_by: Target model field to order results by.
        order: Sorting direction.
        company: Company exact filter.
        location: Location substring match.
        employment_type: Type filter.
        source: Source scraper filter.
        search: Broad search query match.
        date_from: Minimum posting date.
        date_to: Maximum posting date.
        db_service: Database service handler.

    Returns:
        List of matching SQLAlchemy Internship listings.
    """
    if order.lower() not in ("asc", "desc"):
        raise ValueError("Sort order must be 'asc' or 'desc'.")

    if sort_by and not hasattr(Internship, sort_by):
        raise ValueError(f"Invalid sort_by field: '{sort_by}'")

    return db_service.query_internships(
        skip=pagination.skip,
        limit=pagination.limit,
        sort_by=sort_by,
        order=order,
        company=company,
        location=location,
        employment_type=employment_type,
        source=source,
        search=search,
        date_from=date_from,
        date_to=date_to,
    )


@router.get(
    "/internships/{id}",
    response_model=InternshipResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Internship by ID",
    description="Retrieve details of a single internship listing by database ID.",
    dependencies=[Depends(verify_api_key)],
)
async def get_internship(
    id: int,
    session: Session = Depends(get_db_session),
) -> Internship:
    """Retrieve details of a single listing.

    Args:
        id: Target database primary key.
        session: Active database transaction.

    Returns:
        The matched SQLAlchemy model.

    Raises:
        KeyError: If no record is matched.
    """
    job = session.get(Internship, id)
    if not job:
        raise KeyError(f"Internship with ID {id} not found.")
    return job


@router.get(
    "/stats",
    response_model=StatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Database Statistics",
    description="Retrieve aggregated metrics and scraping breakdowns from database.",
    dependencies=[Depends(verify_api_key)],
)
async def get_stats(
    db_service: DatabaseService = Depends(get_database_service),
) -> StatsResponse:
    """Retrieve metrics indicating database coverage.

    Args:
        db_service: Database service handler.

    Returns:
        StatsResponse metrics.
    """
    stats = db_service.get_statistics()
    return StatsResponse(
        total=stats["total"],
        new_today=stats["new_today"],
        companies=stats["companies"],
        sources=stats["sources"],
    )
