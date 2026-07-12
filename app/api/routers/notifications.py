"""Router for dispatching Telegram notifications for listings."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_db_session,
    get_notification_service,
)
from app.security.rbac import Permission, require_permissions
from app.api.schemas.response import ErrorResponse, NotificationRequest
from app.models.internship import Internship
from app.notifications.notification_service import NotificationService

router = APIRouter(tags=["Notifications"])


@router.post(
    "/notifications/send",
    response_model=ErrorResponse,
    status_code=status.HTTP_200_OK,
    summary="Send Notifications",
    description=(
        "Retrieve target listings by their database IDs and dispatch "
        "alert notifications using the configured Telegram service."
    ),
    dependencies=[Depends(require_permissions([Permission.NOTIFICATIONS_DISPATCH]))],
)
async def send_notifications(
    request: NotificationRequest,
    session: Session = Depends(get_db_session),
    notification_service: NotificationService = Depends(get_notification_service),
) -> dict[str, str]:
    """Dispatch alerts for the specified list of database IDs.

    Args:
        request: List of IDs in the request body.
        session: Injected database transaction.
        notification_service: Injected NotificationService instance.

    Returns:
        Dictionary mapping detail to success message.

    Raises:
        ValueError: If ID list is empty.
        KeyError: If none of the IDs were matched.
    """
    if not request.internship_ids:
        raise ValueError("List of internship IDs must not be empty.")

    stmt = select(Internship).where(Internship.id.in_(request.internship_ids))
    jobs = list(session.scalars(stmt).all())

    if not jobs:
        raise KeyError("None of the specified internship IDs exist in the database.")

    notification_service.notify_many(jobs)

    return {
        "detail": f"Successfully dispatched notifications for {len(jobs)} listings."
    }
