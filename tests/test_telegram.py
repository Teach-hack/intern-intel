"""Unit tests for the TelegramNotifier class."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.core.exceptions import TelegramNotificationError
from app.notifications.telegram import TelegramNotifier


def test_initialization() -> None:
    """Verify that TelegramNotifier initializes correctly with valid inputs."""
    notifier = TelegramNotifier("token123", "chat456", timeout=15.0)
    assert notifier._bot_token == "token123"
    assert notifier._chat_id == "chat456"
    assert notifier._timeout == 15.0


@pytest.mark.parametrize(
    ("token", "chat_id"),
    [
        ("", "chat456"),
        ("token123", ""),
        ("   ", "chat456"),
        ("token123", "   "),
        (None, "chat456"),
        ("token123", None),
    ],
)
def test_initialization_invalid_inputs(token: str | None, chat_id: str | None) -> None:
    """Verify that invalid initialization inputs raise ValueError."""
    with pytest.raises(ValueError):
        TelegramNotifier(token, chat_id)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "text",
    [
        "",
        "   ",
        None,
    ],
)
def test_send_invalid_text(text: str | None) -> None:
    """Verify that send() raises ValueError for empty or null text."""
    notifier = TelegramNotifier("token123", "chat456")
    with pytest.raises(ValueError, match="Message text must not be empty"):
        notifier.send(text)  # type: ignore[arg-type]


@patch("app.notifications.telegram.httpx.Client")
def test_send_success_defaults(mock_client_class: MagicMock) -> None:
    """Verify successful send with default parse_mode and disable_web_page_preview."""
    mock_client = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_client

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {"ok": True, "result": {"message_id": 1}}
    mock_client.post.return_value = mock_response

    notifier = TelegramNotifier("token123", "chat456", timeout=25.0)
    with patch("app.notifications.telegram.logger") as mock_logger:
        notifier.send("Hello world")

    mock_client_class.assert_called_once_with(timeout=25.0)
    mock_client.post.assert_called_once_with(
        "https://api.telegram.org/bottoken123/sendMessage",
        json={
            "chat_id": "chat456",
            "text": "Hello world",
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        },
    )
    mock_logger.info.assert_any_call(
        "Sending Telegram notification to chat: {}",
        "chat456",
    )
    mock_logger.info.assert_any_call("Telegram notification sent successfully.")


@patch("app.notifications.telegram.httpx.Client")
def test_send_success_custom(mock_client_class: MagicMock) -> None:
    """Verify successful send with custom parse_mode and web page preview options."""
    mock_client = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_client

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {"ok": True, "result": {"message_id": 1}}
    mock_client.post.return_value = mock_response

    notifier = TelegramNotifier("token123", "chat456")
    notifier.send("HTML message", parse_mode="HTML", disable_web_page_preview=False)

    mock_client.post.assert_called_once_with(
        "https://api.telegram.org/bottoken123/sendMessage",
        json={
            "chat_id": "chat456",
            "text": "HTML message",
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        },
    )


@patch("app.notifications.telegram.httpx.Client")
def test_send_api_ok_false(mock_client_class: MagicMock) -> None:
    """Verify that send() raises TelegramNotificationError if ok is False in response."""
    mock_client = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_client

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {
        "ok": False,
        "description": "Chat not found",
    }
    mock_client.post.return_value = mock_response

    notifier = TelegramNotifier("token123", "chat456")
    with patch("app.notifications.telegram.logger") as mock_logger:
        with pytest.raises(
            TelegramNotificationError,
            match="Telegram API returned error: Chat not found",
        ):
            notifier.send("Hello world")

    mock_logger.info.assert_any_call(
        "Sending Telegram notification to chat: {}",
        "chat456",
    )


@patch("app.notifications.telegram.httpx.Client")
def test_send_api_ok_false_no_description(mock_client_class: MagicMock) -> None:
    """Verify that send() defaults the error description if it is missing from Telegram."""
    mock_client = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_client

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.return_value = {
        "ok": False,
    }
    mock_client.post.return_value = mock_response

    notifier = TelegramNotifier("token123", "chat456")
    with pytest.raises(
        TelegramNotificationError,
        match="Telegram API returned error: Unknown Telegram error response",
    ):
        notifier.send("Hello world")


@patch("app.notifications.telegram.httpx.Client")
def test_send_http_status_error(mock_client_class: MagicMock) -> None:
    """Verify that HTTP status errors are converted to TelegramNotificationError."""
    mock_client = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_client

    request = httpx.Request("POST", "https://api.telegram.org")
    response = httpx.Response(400, request=request)
    mock_exc = httpx.HTTPStatusError("Bad Request", request=request, response=response)
    mock_client.post.side_effect = mock_exc

    notifier = TelegramNotifier("token123", "chat456")
    with patch("app.notifications.telegram.logger") as mock_logger:
        with pytest.raises(TelegramNotificationError, match="HTTP status error"):
            notifier.send("Hello world")

    mock_logger.error.assert_called_once()


@patch("app.notifications.telegram.httpx.Client")
def test_send_timeout_error(mock_client_class: MagicMock) -> None:
    """Verify that timeout exceptions are converted to TelegramNotificationError."""
    mock_client = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_client

    mock_exc = httpx.TimeoutException("Connection timed out")
    mock_client.post.side_effect = mock_exc

    notifier = TelegramNotifier("token123", "chat456")
    with patch("app.notifications.telegram.logger") as mock_logger:
        with pytest.raises(TelegramNotificationError, match="Timeout"):
            notifier.send("Hello world")

    mock_logger.error.assert_called_once()


@patch("app.notifications.telegram.httpx.Client")
def test_send_request_error(mock_client_class: MagicMock) -> None:
    """Verify that general request errors are converted to TelegramNotificationError."""
    mock_client = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_client

    request = httpx.Request("POST", "https://api.telegram.org")
    mock_exc = httpx.RequestError("Network error", request=request)
    mock_client.post.side_effect = mock_exc

    notifier = TelegramNotifier("token123", "chat456")
    with patch("app.notifications.telegram.logger") as mock_logger:
        with pytest.raises(
            TelegramNotificationError,
            match="Network request error",
        ):
            notifier.send("Hello world")

    mock_logger.error.assert_called_once()


@patch("app.notifications.telegram.httpx.Client")
def test_send_invalid_json(mock_client_class: MagicMock) -> None:
    """Verify that JSON decode failures are handled gracefully."""
    mock_client = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_client

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.json.side_effect = ValueError("Invalid JSON syntax")
    mock_client.post.return_value = mock_response

    notifier = TelegramNotifier("token123", "chat456")
    with patch("app.notifications.telegram.logger") as mock_logger:
        with pytest.raises(
            TelegramNotificationError,
            match="Unexpected error sending Telegram notification: Invalid JSON syntax",
        ):
            notifier.send("Hello world")

    mock_logger.error.assert_called_once()


@patch("app.notifications.telegram.httpx.Client")
def test_send_generic_exception(mock_client_class: MagicMock) -> None:
    """Verify that unexpected exceptions are converted to TelegramNotificationError."""
    mock_client = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_client

    mock_exc = RuntimeError("Fatal local system failure")
    mock_client.post.side_effect = mock_exc

    notifier = TelegramNotifier("token123", "chat456")
    with patch("app.notifications.telegram.logger") as mock_logger:
        with pytest.raises(TelegramNotificationError, match="Unexpected error"):
            notifier.send("Hello world")

    mock_logger.error.assert_called_once()
