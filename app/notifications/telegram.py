"""Telegram notification dispatcher."""

from __future__ import annotations

import httpx

from app.core.exceptions import TelegramNotificationError
from app.core.logger import logger

__all__ = ["TelegramNotifier"]


class TelegramNotifier:
    """Dispatches notifications to a Telegram chat using a bot."""

    def __init__(self, bot_token: str, chat_id: str, timeout: float = 30.0) -> None:
        """Initialize the TelegramNotifier.

        Args:
            bot_token: Secret Telegram bot token.
            chat_id: Telegram chat ID to send messages to.
            timeout: Request timeout in seconds.

        Raises:
            ValueError: If bot_token or chat_id is empty or whitespace-only.
        """
        if not bot_token or not bot_token.strip():
            raise ValueError("Telegram bot_token must not be empty.")
        if not chat_id or not chat_id.strip():
            raise ValueError("Telegram chat_id must not be empty.")

        self._bot_token = bot_token.strip()
        self._chat_id = chat_id.strip()
        self._timeout = timeout

    def send(
        self,
        text: str,
        parse_mode: str = "Markdown",
        disable_web_page_preview: bool = True,
    ) -> None:
        """Send a message to the configured Telegram chat.

        Args:
            text: The message text to send.
            parse_mode: Parse mode for formatting (e.g. Markdown, HTML).
            disable_web_page_preview: Disable link preview in the chat.

        Raises:
            ValueError: If text is empty or whitespace-only.
            TelegramNotificationError: If the dispatch fails due to HTTP error,
                timeout, or an unsuccessful response from Telegram.
        """
        if not text or not text.strip():
            raise ValueError("Message text must not be empty.")

        url = f"https://api.telegram.org/bot{self._bot_token}/sendMessage"
        payload = {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }

        try:
            logger.info("Sending Telegram notification to chat: {}", self._chat_id)
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

            if not isinstance(data, dict) or not data.get("ok"):
                error_msg = data.get("description", "Unknown Telegram error response")
                raise TelegramNotificationError(
                    f"Telegram API returned error: {error_msg}"
                )

            logger.info("Telegram notification sent successfully.")

        except httpx.TimeoutException as exc:
            msg = f"Timeout sending Telegram notification: {exc}"
            logger.error(msg)
            raise TelegramNotificationError(msg) from exc

        except httpx.HTTPStatusError as exc:
            msg = f"HTTP status error sending Telegram notification: {exc}"
            logger.error(msg)
            raise TelegramNotificationError(msg) from exc

        except httpx.RequestError as exc:
            msg = f"Network request error sending Telegram notification: {exc}"
            logger.error(msg)
            raise TelegramNotificationError(msg) from exc

        except Exception as exc:
            if isinstance(exc, TelegramNotificationError):
                raise
            msg = f"Unexpected error sending Telegram notification: {exc}"
            logger.error(msg)
            raise TelegramNotificationError(msg) from exc
