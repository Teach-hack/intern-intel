"""Pytest conftest configuration."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.app import app
from app.api.dependencies import get_db_session
from app.core.settings import Settings
from app.database.migrations import MigrationService
from app.models.user import UserRole


# Set a secure test secret key for settings loading during the entire test suite run
os.environ["JWT_SECRET_KEY"] = "securetestsecretkeycontainingatleast32chars"


@pytest.fixture(name="db_session", scope="function")
def fixture_db_session(tmp_path: Path) -> Generator[Session, None, None]:
    """Provide an isolated database session with schema migrated."""
    db_path = tmp_path / "test_api_global.db"
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

    app.dependency_overrides[get_db_session] = lambda: session

    from contextlib import contextmanager

    @contextmanager
    def mock_get_session():
        yield session

    with (
        patch("app.database.session.get_session", side_effect=mock_get_session),
        patch("app.services.auth_service.get_session", side_effect=mock_get_session),
        patch("app.services.user_service.get_session", side_effect=mock_get_session),
        patch("app.services.audit_service.get_session", side_effect=mock_get_session),
    ):
        try:
            yield session
        finally:
            session.close()
            engine.dispose()
            app.dependency_overrides.clear()
            # Clear failed login attempts lockout dictionary
            from app.services.auth_service import _default_throttle

            with patch.object(_default_throttle, "_lock"):
                _default_throttle._failed_attempts.clear()


@pytest.fixture(name="client")
def fixture_client(db_session: Session) -> TestClient:
    """TestClient instance fixture."""
    return TestClient(app)


@pytest.fixture
def test_user(client: TestClient) -> dict[str, str]:
    """Create a regular user for tests."""
    user_data = {
        "username": "normal_user",
        "email": "user@example.com",
        "password": "SecurePassword123"
    }
    client.post("/api/v1/auth/register", json=user_data)
    return user_data


@pytest.fixture
def normal_user_token(client: TestClient, test_user: dict[str, str]) -> dict[str, str]:
    """Login and return token for regular user."""
    response = client.post("/api/v1/auth/login", json={"username": test_user["email"], "password": test_user["password"]})
    return response.json()


@pytest.fixture
def admin_token(client: TestClient) -> dict[str, str]:
    """Create an admin user and return token."""
    # Since we don't have a way to register an admin directly, we mock it.
    from app.services.auth_service import AuthenticationService
    from app.core.config import settings
    auth_service = AuthenticationService(settings)
    auth_service.register("admin_user", "admin@example.com", "AdminPassword123", UserRole.ADMIN)
    
    response = client.post("/api/v1/auth/login", json={"username": "admin@example.com", "password": "AdminPassword123"})
    return response.json()
