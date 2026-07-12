"""Comprehensive unit and integration tests for authentication and authorization."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.models.user import User, UserRole
from app.security.pwd_context import hash_password, verify_password


def test_password_hashing() -> None:
    """Verify password hashing context functions correctly."""
    pwd = "mysecretpassword"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed)
    assert not verify_password("wrongpassword", hashed)


def test_registration_success(client: TestClient, db_session: Session) -> None:
    """Verify signing up a new user account."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "SecurePassword123",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == "bob"
    assert data["email"] == "bob@example.com"
    assert data["role"] == "USER"


def test_registration_weak_password_length(client: TestClient) -> None:
    """Verify weak password lengths are rejected by schema validator."""
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "bob", "email": "bob@example.com", "password": "short"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_registration_weak_password_uppercase(client: TestClient) -> None:
    """Verify passwords missing uppercase letter are rejected."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "securepassword123",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "uppercase" in response.json()["detail"]


def test_registration_weak_password_lowercase(client: TestClient) -> None:
    """Verify passwords missing lowercase letter are rejected."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "SECUREPASSWORD123",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "lowercase" in response.json()["detail"]


def test_registration_weak_password_digit(client: TestClient) -> None:
    """Verify passwords missing digit are rejected."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "SecurePassword",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "digit" in response.json()["detail"]


def test_registration_duplicate_user(client: TestClient, db_session: Session) -> None:
    """Verify signing up duplicate username or email fails with 400."""
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "SecurePassword123",
        },
    )
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "SecurePassword123",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already registered" in response.json()["detail"]


def test_email_normalization(client: TestClient, db_session: Session) -> None:
    """Verify email casing normalization handles duplicate prevention."""
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "bob",
            "email": "Bob@EXAMPLE.com ",
            "password": "SecurePassword123",
        },
    )
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "bob2",
            "email": "bob@example.com",
            "password": "SecurePassword123",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_username_normalization(client: TestClient, db_session: Session) -> None:
    """Verify username casing and space normalization handles duplicate prevention."""
    res1 = client.post(
        "/api/v1/auth/register",
        json={
            "username": " bob ",
            "email": "bob@example.com",
            "password": "SecurePassword123",
        },
    )
    assert res1.status_code == status.HTTP_201_CREATED
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "bob",
            "email": "bob2@example.com",
            "password": "SecurePassword123",
        },
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_login_success(client: TestClient, db_session: Session) -> None:
    """Verify credential verification and token creation."""
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "SecurePassword123",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "bob", "password": "SecurePassword123"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_failure(client: TestClient, db_session: Session) -> None:
    """Verify incorrect credentials fail."""
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "SecurePassword123",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "bob", "password": "wrongpassword"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid username or password" in response.json()["detail"]


def test_login_lockout_throttling(client: TestClient, db_session: Session) -> None:
    """Verify lockout throttling triggers after 5 failures."""
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "SecurePassword123",
        },
    )
    for _ in range(5):
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "bob", "password": "wrongpassword"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "bob", "password": "wrongpassword"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "locked out" in response.json()["detail"]


def test_inactive_user_login(client: TestClient, db_session: Session) -> None:
    """Verify inactive users are rejected during authentication check."""
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "inactive_bob",
            "email": "inactive@example.com",
            "password": "SecurePassword123",
        },
    )
    # Deactivate in database
    from app.database.user_repository import UserRepository

    user_repo = UserRepository(db_session)
    user = user_repo.get_by_username("inactive_bob")
    assert user is not None
    user.is_active = False
    user_repo.update(user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "inactive_bob", "password": "SecurePassword123"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "deactivated" in response.json()["detail"]


def test_refresh_token_rotation(client: TestClient, db_session: Session) -> None:
    """Verify refresh token rotation handles rotating and reuse breach."""
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "SecurePassword123",
        },
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": "bob", "password": "SecurePassword123"},
    )
    tokens = login_res.json()
    ref_token = tokens["refresh_token"]

    ref_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": ref_token},
    )
    assert ref_res.status_code == status.HTTP_200_OK
    new_tokens = ref_res.json()
    assert new_tokens["refresh_token"] != ref_token

    breach_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": ref_token},
    )
    assert breach_res.status_code == status.HTTP_401_UNAUTHORIZED
    assert "revoked" in breach_res.json()["detail"]


def test_logout_revocation(client: TestClient, db_session: Session) -> None:
    """Verify logging out revokes the refresh token."""
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "SecurePassword123",
        },
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": "bob", "password": "SecurePassword123"},
    )
    tokens = login_res.json()
    ref_token = tokens["refresh_token"]

    logout_res = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": ref_token},
    )
    assert logout_res.status_code == status.HTTP_200_OK

    ref_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": ref_token},
    )
    assert ref_res.status_code == status.HTTP_401_UNAUTHORIZED


def test_auth_me_protected_endpoints(client: TestClient, db_session: Session) -> None:
    """Verify route protections and profile updates."""
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "bob",
            "email": "bob@example.com",
            "password": "SecurePassword123",
        },
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": "bob", "password": "SecurePassword123"},
    )
    access_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == status.HTTP_200_OK
    assert me_res.json()["username"] == "bob"

    update_res = client.patch(
        "/api/v1/users/me",
        json={"email": "bob_new@example.com"},
        headers=headers,
    )
    assert update_res.status_code == status.HTTP_200_OK
    assert update_res.json()["email"] == "bob_new@example.com"

    pwd_res = client.patch(
        "/api/v1/auth/change-password",
        json={
            "old_password": "SecurePassword123",
            "new_password": "NewSecurePassword123",
        },
        headers=headers,
    )
    assert pwd_res.status_code == status.HTTP_200_OK

    login_new = client.post(
        "/api/v1/auth/login",
        json={"username": "bob", "password": "NewSecurePassword123"},
    )
    assert login_new.status_code == status.HTTP_200_OK


def test_admin_routes_privilege(client: TestClient, db_session: Session) -> None:
    """Verify admin role validations and user lists."""
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "user1",
            "email": "u1@example.com",
            "password": "SecurePassword123",
        },
    )
    admin = User(
        username="admin1",
        email="admin1@example.com",
        password_hash=hash_password("AdminPassword123"),
        role=UserRole.ADMIN,
    )
    db_session.add(admin)
    db_session.commit()

    u_login = client.post(
        "/api/v1/auth/login",
        json={"username": "user1", "password": "SecurePassword123"},
    )
    u_headers = {"Authorization": f"Bearer {u_login.json()['access_token']}"}

    a_login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin1", "password": "AdminPassword123"},
    )
    a_headers = {"Authorization": f"Bearer {a_login.json()['access_token']}"}

    list_u = client.get("/api/v1/admin/users", headers=u_headers)
    assert list_u.status_code == status.HTTP_403_FORBIDDEN

    list_a = client.get("/api/v1/admin/users", headers=a_headers)
    assert list_a.status_code == status.HTTP_200_OK
    assert len(list_a.json()) == 2

    target_user_id = list_a.json()[0]["id"]
    get_res = client.get(f"/api/v1/admin/users/{target_user_id}", headers=a_headers)
    assert get_res.status_code == status.HTTP_200_OK

    update_res = client.patch(
        f"/api/v1/admin/users/{target_user_id}",
        json={"role": "ADMIN"},
        headers=a_headers,
    )
    assert update_res.status_code == status.HTTP_200_OK
    assert update_res.json()["role"] == "ADMIN"

    del_res = client.delete(f"/api/v1/admin/users/{target_user_id}", headers=a_headers)
    assert del_res.status_code == status.HTTP_200_OK


def test_user_service_direct_methods(db_session: Session) -> None:
    """Verify all public methods of UserService directly."""
    from app.services.user_service import UserService

    settings = Settings({})
    user_service = UserService(settings)

    # 1. Register users for testing
    from app.services.auth_service import AuthenticationService

    auth_service = AuthenticationService(settings)
    u1 = auth_service.register("testuser1", "u1@example.com", "Password123")
    u2 = auth_service.register("testuser2", "u2@example.com", "Password123")

    # profile lookup
    retrieved = user_service.profile(u1.id)
    assert retrieved.username == "testuser1"

    with pytest.raises(ValueError, match="User not found"):
        user_service.profile(99999)

    # update_profile
    # success
    updated = user_service.update_profile(
        u1.id, username="testuser1_new", email="u1_new@example.com"
    )
    assert updated.username == "testuser1_new"
    assert updated.email == "u1_new@example.com"

    # User not found
    with pytest.raises(ValueError, match="User not found"):
        user_service.update_profile(99999, username="fail")

    # Username already taken
    with pytest.raises(ValueError, match="Username already taken"):
        user_service.update_profile(u2.id, username="testuser1_new")

    # Email already taken
    with pytest.raises(ValueError, match="Email already taken"):
        user_service.update_profile(u2.id, email="u1_new@example.com")

    # deactivate/activate account
    # success deactivation
    deactivated = user_service.deactivate_account(u1.id)
    assert not deactivated.is_active

    with pytest.raises(ValueError, match="User not found"):
        user_service.deactivate_account(99999)

    # success activation
    activated = user_service.activate_account(u1.id)
    assert activated.is_active

    with pytest.raises(ValueError, match="User not found"):
        user_service.activate_account(99999)

    # list_users
    users = user_service.list_users(skip=0, limit=10)
    assert len(users) >= 2

    # admin_update_user
    # success with role / is_active / is_verified
    admin_updated = user_service.admin_update_user(
        u1.id,
        username="admin_chosen_username",
        email="admin_chosen_email@example.com",
        role=UserRole.ADMIN,
        is_active=False,
        is_verified=True,
    )
    assert admin_updated.username == "admin_chosen_username"
    assert admin_updated.email == "admin_chosen_email@example.com"
    assert admin_updated.role == UserRole.ADMIN
    assert not admin_updated.is_active
    assert admin_updated.is_verified

    # User not found
    with pytest.raises(ValueError, match="User not found"):
        user_service.admin_update_user(99999, username="fail")

    # Username already taken
    with pytest.raises(ValueError, match="Username already taken"):
        user_service.admin_update_user(u2.id, username="admin_chosen_username")

    # Email already taken
    with pytest.raises(ValueError, match="Email already taken"):
        user_service.admin_update_user(u2.id, email="admin_chosen_email@example.com")

    # delete_user
    user_service.admin_update_user(u2.id, role=UserRole.ADMIN)
    user_service.delete_user(u1.id)
    with pytest.raises(ValueError, match="User not found"):
        user_service.profile(u1.id)

    # delete non-existing user shouldn't raise
    user_service.delete_user(99999)


def test_login_throttle_interface_raises() -> None:
    """Verify that LoginThrottleInterface methods raise NotImplementedError."""
    from app.security.throttle import LoginThrottleInterface

    throttle = LoginThrottleInterface()
    with pytest.raises(NotImplementedError):
        throttle.is_locked("bob")
    with pytest.raises(NotImplementedError):
        throttle.get_remaining_lockout("bob")
    with pytest.raises(NotImplementedError):
        throttle.record_failure("bob")
    with pytest.raises(NotImplementedError):
        throttle.reset("bob")


def test_in_memory_throttle_lockout_expiry() -> None:
    """Verify that expired lockout records are cleaned up."""
    from datetime import datetime, timedelta, timezone

    from app.security.throttle import InMemoryLoginThrottle

    throttle = InMemoryLoginThrottle(max_attempts=3)
    throttle.record_failure("bob")
    throttle.record_failure("bob")
    throttle.record_failure("bob")
    assert throttle.is_locked("bob")

    # Manually backdate the lockout expiration to be in the past
    with throttle._lock:
        count, _ = throttle._failed_attempts["bob"]
        past_expiry = datetime.now(timezone.utc) - timedelta(minutes=1)
        throttle._failed_attempts["bob"] = (count, past_expiry)

    # Calling is_locked should now clean up and return False
    assert not throttle.is_locked("bob")
    assert throttle.get_remaining_lockout("bob") == 0


def test_verify_password_exception() -> None:
    """Verify verify_password returns False when an exception is raised."""
    from app.security.pwd_context import verify_password

    # Passing a malformed hash should raise an error inside bcrypt, which we catch and return False
    assert not verify_password("secret", "invalid-bcrypt-hash-format")
    assert not verify_password("secret", "")


def test_token_helpers_direct() -> None:
    """Verify create_refresh_token, create_access_token, and verify_token behavior."""
    from datetime import timedelta

    from app.security.tokens import (
        create_access_token,
        create_refresh_token,
        verify_token,
    )

    # Access Token Creation & Validation
    mock_user = MagicMock()
    mock_user.username = "alice"
    mock_user.id = 1
    mock_user.role = "USER"
    tok = create_access_token(mock_user)
    claims = verify_token(tok)
    assert claims is not None
    assert claims["sub"] == "alice"
    assert claims["type"] == "access"

    # Refresh Token Creation & Validation
    ref_tok = create_refresh_token("alice")
    claims_ref = verify_token(ref_tok)
    assert claims_ref is not None
    assert claims_ref["sub"] == "alice"
    assert claims_ref["type"] == "refresh"

    # Invalid token verification
    assert verify_token("invalid.token.payload") is None
    assert verify_token("") is None

    # Expired token verification
    expired_tok = create_access_token(mock_user, expires_delta=timedelta(seconds=-10))
    assert verify_token(expired_tok) is None
