"""API router for authentication and user profile management."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    get_admin_user,
    get_current_active_user,
    get_settings,
)
from app.api.schemas.auth import (
    AdminUserUpdateRequest,
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    UserUpdateRequest,
)
from app.core.logger import logger
from app.core.settings import Settings
from app.models.user import User
from app.services.auth_service import AuthenticationService
from app.services.user_service import UserService

router = APIRouter(tags=["Authentication & Users"])


@router.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    payload: RegisterRequest,
    settings: Settings = Depends(get_settings),
) -> User:
    """Register a new user in the platform.

    Args:
        payload: RegisterRequest validation fields.
        settings: Injected system settings.

    Returns:
        The created User response.
    """
    auth_service = AuthenticationService(settings)
    try:
        user = auth_service.register(
            username=payload.username,
            email=payload.email,
            password=payload.password,
        )
        logger.info(
            "User registered | username={} | email={}",
            payload.username,
            payload.email,
        )
        return user
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate credentials and retrieve session tokens",
)
async def login(
    payload: LoginRequest,
    settings: Settings = Depends(get_settings),
) -> dict:
    """Verify login parameters and issue access & refresh tokens.

    Args:
        payload: LoginRequest credentials.
        settings: Injected system settings.

    Returns:
        TokenResponse payload.
    """
    auth_service = AuthenticationService(settings)
    try:
        tokens = auth_service.login(
            username_or_email=payload.username,
            password=payload.password,
            device_name=payload.device_name,
        )
        logger.info(
            "User login success | username_or_email={} | device={}",
            payload.username,
            payload.device_name,
        )
        return tokens
    except ValueError as exc:
        logger.warning(
            "User login failure | username_or_email={} | reason={}",
            payload.username,
            str(exc),
        )
        # Check if error indicates lockout to throw 403, otherwise 400
        if "lockout" in str(exc) or "locked" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(exc),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/auth/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate refresh token for new access token",
)
async def refresh(
    payload: RefreshRequest,
    settings: Settings = Depends(get_settings),
) -> dict:
    """Perform refresh token rotation check.

    Args:
        payload: RefreshRequest containing current token.
        settings: Injected system settings.

    Returns:
        TokenResponse payload.
    """
    auth_service = AuthenticationService(settings)
    try:
        tokens = auth_service.refresh_session(
            refresh_token=payload.refresh_token,
            device_name=payload.device_name,
        )
        logger.info("Session token refreshed | device={}", payload.device_name)
        return tokens
    except ValueError as exc:
        logger.warning("Session token refresh failure | reason={}", str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )


@router.post(
    "/auth/logout",
    status_code=status.HTTP_200_OK,
    summary="Revoke target session refresh token",
)
async def logout(
    payload: LogoutRequest,
    settings: Settings = Depends(get_settings),
) -> dict:
    """Invalidate active refresh token session.

    Args:
        payload: LogoutRequest containing target token.
        settings: Injected system settings.

    Returns:
        Detail dict status success.
    """
    auth_service = AuthenticationService(settings)
    auth_service.logout(payload.refresh_token)
    logger.info("User logout success")
    return {"detail": "Successfully logged out."}


@router.get(
    "/auth/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user details",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Retrieve session details for the authenticated user.

    Args:
        current_user: Active authenticated user.

    Returns:
        The matched user model.
    """
    return current_user


@router.patch(
    "/auth/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change user account credentials",
)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Modify credentials and revoke all active login sessions.

    Args:
        payload: ChangePasswordRequest payload validation bounds.
        current_user: Active authenticated user.
        settings: Injected system settings.

    Returns:
        Detail dict status success.
    """
    auth_service = AuthenticationService(settings)
    try:
        auth_service.change_password(
            user_id=current_user.id,
            old_password=payload.old_password,
            new_password=payload.new_password,
        )
        logger.info("User changed password | user_id={}", current_user.id)
        return {"detail": "Password changed successfully."}
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/users/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get active user profile",
)
async def get_user_me(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Retrieve active authenticated profile details.

    Args:
        current_user: Active authenticated user.

    Returns:
        The matched user profile.
    """
    return current_user


@router.patch(
    "/users/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update active user profile",
)
async def update_user_me(
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    settings: Settings = Depends(get_settings),
) -> User:
    """Allow active users to modify their profile attributes.

    Args:
        payload: UserUpdateRequest containing updates.
        current_user: Active authenticated user.
        settings: Injected system settings.

    Returns:
        The updated User profile.
    """
    user_service = UserService(settings)
    try:
        updated = user_service.update_profile(
            user_id=current_user.id,
            email=payload.email,
            username=payload.username,
        )
        logger.info("User profile updated | user_id={}", current_user.id)
        return updated
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# =============================================================================
# Admin User Management Routes
# =============================================================================


@router.get(
    "/admin/users",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="List all platform users",
)
async def admin_list_users(
    skip: int = 0,
    limit: int = 100,
    current_admin: User = Depends(get_admin_user),
    settings: Settings = Depends(get_settings),
) -> list[User]:
    """Retrieve lists of stored user accounts.

    Args:
        skip: Count skip offset.
        limit: Max pagination bounds.
        current_admin: Active administrator.
        settings: Injected system settings.

    Returns:
        List of user accounts.
    """
    user_service = UserService(settings)
    logger.info("Admin listing users | admin_id={}", current_admin.id)
    return user_service.list_users(skip=skip, limit=limit)


@router.get(
    "/admin/users/{id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get target user profile details",
)
async def admin_get_user(
    id: int,
    current_admin: User = Depends(get_admin_user),
    settings: Settings = Depends(get_settings),
) -> User:
    """Retrieve details for any user account.

    Args:
        id: Target user ID.
        current_admin: Active administrator.
        settings: Injected system settings.

    Returns:
        The target user account profile.
    """
    user_service = UserService(settings)
    try:
        return user_service.profile(id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.patch(
    "/admin/users/{id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Modify target user profile",
)
async def admin_update_user(
    id: int,
    payload: AdminUserUpdateRequest,
    current_admin: User = Depends(get_admin_user),
    settings: Settings = Depends(get_settings),
) -> User:
    """Allow administrators to override any parameter for a user.

    Args:
        id: Target user ID.
        payload: AdminUserUpdateRequest specifications.
        current_admin: Active administrator.
        settings: Injected system settings.

    Returns:
        The updated User profile.
    """
    user_service = UserService(settings)
    try:
        updated = user_service.admin_update_user(
            user_id=id,
            username=payload.username,
            email=payload.email,
            role=payload.role,
            is_active=payload.is_active,
            is_verified=payload.is_verified,
        )
        logger.info(
            "Admin updated user | admin_id={} | target_user_id={}",
            current_admin.id,
            id,
        )
        return updated
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.delete(
    "/admin/users/{id}",
    status_code=status.HTTP_200_OK,
    summary="Delete target user profile",
)
async def admin_delete_user(
    id: int,
    current_admin: User = Depends(get_admin_user),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Permanently delete a user account from database.

    Args:
        id: Target user ID.
        current_admin: Active administrator.
        settings: Injected system settings.

    Returns:
        Detail dict status success.
    """
    user_service = UserService(settings)
    user_service.delete_user(id)
    logger.info(
        "Admin deleted user | admin_id={} | target_user_id={}",
        current_admin.id,
        id,
    )
    return {"detail": "User deleted successfully."}
