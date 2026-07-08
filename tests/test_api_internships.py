"""Unit and integration tests for the API Internships endpoints."""

from __future__ import annotations

from collections.abc import Generator
from datetime import date
from pathlib import Path

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.app import app
from app.api.dependencies import get_db_session
from app.core.settings import Settings
from app.database.migrations import MigrationService
from app.models.internship import Internship


@pytest.fixture(name="db_session")
def fixture_db_session(tmp_path: Path) -> Generator[Session, None, None]:
    """Provide an isolated database session with schema migrated."""
    db_path = tmp_path / "test_api.db"
    settings = Settings(
        {"database": {"path": str(db_path), "url": f"sqlite:///{db_path}"}}
    )

    ms = MigrationService(settings=settings)
    ms.upgrade("head")

    engine = create_engine(settings.database_url, future=True)
    session_factory = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )
    session = session_factory()

    # Override get_db_session dependency globally
    app.dependency_overrides[get_db_session] = lambda: session

    from contextlib import contextmanager
    from unittest.mock import patch

    @contextmanager
    def mock_get_session():
        yield session

    with (
        patch("app.database.session.get_session", side_effect=mock_get_session),
        patch(
            "app.services.database_service.get_session", side_effect=mock_get_session
        ),
    ):
        try:
            yield session
        finally:
            session.close()
            engine.dispose()
            app.dependency_overrides.clear()


@pytest.fixture(name="client")
def fixture_client(db_session: Session) -> TestClient:
    """Fixture returning a FastAPI test client configured with overridden DB."""
    return TestClient(app)


def seed_data(session: Session) -> list[Internship]:
    """Helper to populate mock internships."""
    jobs = [
        Internship(
            company="Google",
            title="Software Engineering Intern",
            location="Mountain View, CA",
            employment_type="internship",
            work_mode="hybrid",
            url="https://careers.google.com/jobs/1",
            posted_date=date(2026, 7, 7),
            skills="Python, SQL, Algorithms",
            source="greenhouse",
            status="new",
        ),
        Internship(
            company="Meta",
            title="Production Engineering Intern",
            location="Remote, US",
            employment_type="internship",
            work_mode="remote",
            url="https://careers.meta.com/jobs/2",
            posted_date=date(2026, 7, 8),
            skills="Systems, Python, Networking",
            source="lever",
            status="new",
        ),
        Internship(
            company="Apple",
            title="Hardware Engineer",
            location="Cupertino, CA",
            employment_type="full-time",
            work_mode="on-site",
            url="https://careers.apple.com/jobs/3",
            posted_date=date(2026, 7, 5),
            skills="Verilog, C++",
            source="workday",
            status="active",
        ),
    ]
    session.add_all(jobs)
    session.commit()
    return jobs


def test_list_internships_all(client: TestClient, db_session: Session) -> None:
    """Verify that listing returning all stored records runs correctly."""
    seed_data(db_session)
    response = client.get("/api/v1/internships")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 3
    assert data[0]["company"] == "Google"
    assert data[1]["company"] == "Meta"
    assert data[2]["company"] == "Apple"


def test_list_internships_filter_company(
    client: TestClient, db_session: Session
) -> None:
    """Verify that listing filtering by company name runs correctly."""
    seed_data(db_session)
    response = client.get("/api/v1/internships?company=Google")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["company"] == "Google"


def test_list_internships_filter_location(
    client: TestClient, db_session: Session
) -> None:
    """Verify location search substring match works."""
    seed_data(db_session)
    response = client.get("/api/v1/internships?location=remote")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["company"] == "Meta"


def test_list_internships_search(client: TestClient, db_session: Session) -> None:
    """Verify search matching skills/title queries correctly."""
    seed_data(db_session)
    # Search term 'verilog' matches Apple hardware engineer skills
    response = client.get("/api/v1/internships?search=verilog")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["company"] == "Apple"


def test_list_internships_date_filters(client: TestClient, db_session: Session) -> None:
    """Verify listing filter by posted date range boundaries."""
    seed_data(db_session)
    response = client.get("/api/v1/internships?date_from=2026-07-06")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # Google (7/7) and Meta (7/8) should match. Apple (7/5) is excluded.
    assert len(data) == 2


def test_list_internships_pagination(client: TestClient, db_session: Session) -> None:
    """Verify listing handles page limit bounds and offsets."""
    seed_data(db_session)
    response = client.get("/api/v1/internships?page=2&page_size=1")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    # Page 2 size 1 -> yields the second job (Meta)
    assert data[0]["company"] == "Meta"


def test_list_internships_pagination_invalid(client: TestClient) -> None:
    """Verify negative page inputs raise 422 validations."""
    response = client.get("/api/v1/internships?page=0")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_list_internships_sorting(client: TestClient, db_session: Session) -> None:
    """Verify sorting order directions and fields."""
    seed_data(db_session)
    response = client.get("/api/v1/internships?sort_by=posted_date&order=desc")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # Meta (7/8) -> Google (7/7) -> Apple (7/5)
    assert data[0]["company"] == "Meta"
    assert data[1]["company"] == "Google"
    assert data[2]["company"] == "Apple"


def test_list_internships_sorting_invalid(client: TestClient) -> None:
    """Verify invalid sort field raises 400 validations."""
    response = client.get("/api/v1/internships?sort_by=invalid_field")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_get_internship_detail_success(client: TestClient, db_session: Session) -> None:
    """Verify retrieving detailed view of a single listing."""
    jobs = seed_data(db_session)
    target_id = jobs[0].id
    response = client.get(f"/api/v1/internships/{target_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["company"] == "Google"


def test_get_internship_detail_not_found(client: TestClient) -> None:
    """Verify detail response returns 404 for missing IDs."""
    response = client.get("/api/v1/internships/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "detail" in response.json()


def test_get_stats_empty(client: TestClient) -> None:
    """Verify statistics aggregates on empty database."""
    response = client.get("/api/v1/stats")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 0
    assert data["companies"] == 0
    assert data["sources"] == {}


def test_get_stats_populated(client: TestClient, db_session: Session) -> None:
    """Verify statistics aggregates group elements accurately."""
    seed_data(db_session)
    response = client.get("/api/v1/stats")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 3
    assert data["companies"] == 3
    assert data["sources"] == {"greenhouse": 1, "lever": 1, "workday": 1}
