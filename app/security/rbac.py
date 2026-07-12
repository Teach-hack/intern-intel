"""Role-Based Access Control (RBAC) permissions and dependencies."""

from __future__ import annotations

import enum
from typing import Callable

from fastapi import Depends, HTTPException, status

from app.models.user import User, UserRole
from app.api.dependencies import get_current_active_user


class Permission(str, enum.Enum):
    """Granular system permissions."""

    # User management
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"
    USERS_DELETE = "users:delete"

    # Pipeline/Scraper management
    PIPELINE_READ = "pipeline:read"
    PIPELINE_EXECUTE = "pipeline:execute"

    # Notifications
    NOTIFICATIONS_READ = "notifications:read"
    NOTIFICATIONS_DISPATCH = "notifications:dispatch"

    # System Health & Audit
    SYSTEM_HEALTH_READ = "system_health:read"
    AUDIT_LOG_READ = "audit_log:read"


# Mapping of roles to their granted permissions
ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.USER: set(),  # Users have no admin permissions by default
    UserRole.ADMIN: {
        Permission.USERS_READ,
        Permission.USERS_WRITE,
        Permission.USERS_DELETE,
        Permission.PIPELINE_READ,
        Permission.PIPELINE_EXECUTE,
        Permission.NOTIFICATIONS_READ,
        Permission.NOTIFICATIONS_DISPATCH,
        Permission.SYSTEM_HEALTH_READ,
        Permission.AUDIT_LOG_READ,
    },
}


def has_permission(user: User, required_permissions: list[Permission]) -> bool:
    """Check if the user's role grants the required permissions.

    Args:
        user: The authenticated User.
        required_permissions: List of permissions needed to perform an action.

    Returns:
        True if all required permissions are met, False otherwise.
    """
    granted = ROLE_PERMISSIONS.get(user.role, set())
    return all(perm in granted for perm in required_permissions)


def require_permissions(permissions: list[Permission]) -> Callable:
    """Dependency generator to enforce RBAC permissions on endpoints.

    Args:
        permissions: List of Permission enums required.

    Returns:
        A FastAPI dependency function.
    """

    def dependency(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if not has_permission(current_user, permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to perform this action.",
            )
        return current_user

    return dependency
