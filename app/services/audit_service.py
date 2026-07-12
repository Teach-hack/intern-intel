"""Audit log service for persisting security events."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.database.session import get_session
from app.models.audit_log import AuditLog

if TYPE_CHECKING:
    from fastapi import Request


class AuditService:
    """Service for appending immutable audit records."""

    @classmethod
    def log_event(
        cls,
        action: str,
        actor_id: int | None = None,
        target_id: int | None = None,
        status: str = "SUCCESS",
        details: str | None = None,
        request: Request | None = None,
        session: Session | None = None,
    ) -> None:
        """Create and persist an audit record.

        Args:
            action: Descriptive action name (e.g. 'USER_LOGIN').
            actor_id: The ID of the user performing the action.
            target_id: The ID of the resource or user being modified.
            status: Status of the action (e.g. 'SUCCESS', 'FAILED').
            details: Optional extra contextual details.
            request: Optional FastAPI request to extract IP/Agent.
            session: Optional existing DB session.
        """
        ip_address = None
        user_agent = None

        if request:
            if request.client:
                ip_address = request.client.host
            user_agent = request.headers.get("User-Agent")

        audit_log = AuditLog(
            action=action,
            actor_id=actor_id,
            target_id=target_id,
            status=status,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if session:
            session.add(audit_log)
            # Do not commit if session was passed in, rely on caller transaction
        else:
            with get_session() as new_session:
                new_session.add(audit_log)
                new_session.commit()
