"""Unit and integration tests for the API Health endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.api.app import app


@pytest.fixture
def client() -> TestClient:
    """Fixture returning a FastAPI test client."""
    return TestClient(app)


def test_api_root(client: TestClient) -> None:
    """Verify GET / returns application description metadata."""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["application"] == "InternIntel"
    assert "version" in data
    assert "description" in data


def test_api_health_success(client: TestClient) -> None:
    """Verify GET /api/v1/health reports system metrics correctly."""
    response = client.get("/api/v1/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["scheduler"] in ("running", "stopped")
    assert "uptime_seconds" in data
    assert "version" in data


def test_api_health_database_disconnected(client: TestClient) -> None:
    """Verify health endpoint database failure reports disconnected status."""
    # Mock database session execution to raise an error
    mock_session = MagicMock()
    mock_session.execute.side_effect = Exception("DB error")

    from app.api.dependencies import get_db_session

    app.dependency_overrides[get_db_session] = lambda: mock_session

    try:
        response = client.get("/api/v1/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["database"] == "disconnected"
    finally:
        app.dependency_overrides.clear()


def test_openapi_generation(client: TestClient) -> None:
    """Verify that the OpenAPI JSON schema loads successfully."""
    response = client.get("/openapi.json")
    assert response.status_code == status.HTTP_200_OK
    schema = response.json()
    assert schema["info"]["title"] == "InternIntel API"
    assert "paths" in schema
