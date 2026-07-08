"""Unit and integration tests for the API Pipeline endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.api.app import app
from app.api.dependencies import get_pipeline_service
from app.core.exceptions import DatabaseError, ScraperError
from app.models.internship import Internship
from app.services.pipeline_service import PipelineService


@pytest.fixture
def client() -> TestClient:
    """Fixture returning a FastAPI test client."""
    return TestClient(app)


def test_pipeline_run_success(client: TestClient) -> None:
    """Verify that a successful pipeline run returns execution metrics."""
    mock_pipeline = MagicMock(spec=PipelineService)
    mock_pipeline.run.return_value = [
        MagicMock(spec=Internship),
        MagicMock(spec=Internship),
    ]
    mock_pipeline.last_run_discovered = 10

    app.dependency_overrides[get_pipeline_service] = lambda: mock_pipeline

    try:
        response = client.post("/api/v1/pipeline/run")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["jobs_discovered"] == 10
        assert data["jobs_inserted"] == 2
        assert data["execution_status"] == "success"
        assert "execution_time" in data
    finally:
        app.dependency_overrides.clear()


def test_pipeline_run_scraper_error(client: TestClient) -> None:
    """Verify scraper failure maps to 502 Bad Gateway response."""
    mock_pipeline = MagicMock(spec=PipelineService)
    mock_pipeline.run.side_effect = ScraperError("Failed to fetch page")

    app.dependency_overrides[get_pipeline_service] = lambda: mock_pipeline

    try:
        response = client.post("/api/v1/pipeline/run")
        assert response.status_code == status.HTTP_502_BAD_GATEWAY
        data = response.json()
        assert "Failed to fetch page" in data["detail"]
    finally:
        app.dependency_overrides.clear()


def test_pipeline_run_database_error(client: TestClient) -> None:
    """Verify persistence failure maps to 500 Internal Server error."""
    mock_pipeline = MagicMock(spec=PipelineService)
    mock_pipeline.run.side_effect = DatabaseError("Database disk full")

    app.dependency_overrides[get_pipeline_service] = lambda: mock_pipeline

    try:
        response = client.post("/api/v1/pipeline/run")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Database disk full" in data["detail"]
    finally:
        app.dependency_overrides.clear()
