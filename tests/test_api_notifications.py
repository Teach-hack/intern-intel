"""Unit and integration tests for the API Notifications endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.app import app
from app.api.dependencies import get_db_session, get_notification_service
from app.core.exceptions import TelegramNotificationError
from app.models.internship import Internship
from app.notifications.notification_service import NotificationService


@pytest.fixture
def client() -> TestClient:
    """Fixture returning a FastAPI test client."""
    return TestClient(app)


def test_send_notifications_success(client: TestClient) -> None:
    """Verify that valid IDs correctly trigger notification dispatches."""
    mock_session = MagicMock(spec=Session)
    mock_job = MagicMock(spec=Internship)
    mock_job.id = 42
    mock_session.scalars.return_value.all.return_value = [mock_job]

    mock_ns = MagicMock(spec=NotificationService)

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_notification_service] = lambda: mock_ns

    try:
        response = client.post(
            "/api/v1/notifications/send", json={"internship_ids": [42]}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "dispatched notifications for 1 listings" in data["detail"]
        mock_ns.notify_many.assert_called_once_with([mock_job])
    finally:
        app.dependency_overrides.clear()


def test_send_notifications_empty_payload(client: TestClient) -> None:
    """Verify empty ID list raises a 400 Bad Request."""
    response = client.post("/api/v1/notifications/send", json={"internship_ids": []})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "must not be empty" in response.json()["detail"]


def test_send_notifications_not_found(client: TestClient) -> None:
    """Verify nonexistent ID lists raise a 404 Not Found."""
    mock_session = MagicMock(spec=Session)
    mock_session.scalars.return_value.all.return_value = []

    app.dependency_overrides[get_db_session] = lambda: mock_session

    try:
        response = client.post(
            "/api/v1/notifications/send", json={"internship_ids": [9999]}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "None of the specified internship IDs exist" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_send_notifications_telegram_error(client: TestClient) -> None:
    """Verify telegram dispatcher error raises a 502 Bad Gateway."""
    mock_session = MagicMock(spec=Session)
    mock_job = MagicMock(spec=Internship)
    mock_job.id = 42
    mock_session.scalars.return_value.all.return_value = [mock_job]

    mock_ns = MagicMock(spec=NotificationService)
    mock_ns.notify_many.side_effect = TelegramNotificationError("Telegram API timeout")

    app.dependency_overrides[get_db_session] = lambda: mock_session
    app.dependency_overrides[get_notification_service] = lambda: mock_ns

    try:
        response = client.post(
            "/api/v1/notifications/send", json={"internship_ids": [42]}
        )
        assert response.status_code == status.HTTP_502_BAD_GATEWAY
        assert "Telegram API timeout" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
