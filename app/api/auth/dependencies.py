"""Authentication dependencies placeholder layer."""

from __future__ import annotations

from typing import Annotated

from fastapi import Header

__all__ = ["verify_api_key"]


async def verify_api_key(
    x_api_key: Annotated[
        str | None,
        Header(
            alias="X-API-Key",
            description="API key placeholder authentication header. Currently accepts any value.",
        ),
    ] = None,
) -> str | None:
    """Verify the API key or authentication token.

    Currently permits all requests. Designed to be easily updated with actual
    verification logic without modifications to individual router layers.

    Args:
        x_api_key: Optional X-API-Key header value.

    Returns:
        The provided key (if any) indicating a successful placeholder pass.
    """
    return x_api_key
