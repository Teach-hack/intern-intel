"""Pydantic schemas for authentication and user management endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.user import UserRole


class RegisterRequest(BaseModel):
    """Payload to register a new user account."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Unique username containing only alphanumeric characters, underscores, or hyphens.",
    )
    email: str = Field(
        ...,
        pattern=r"^[^@]+@[^@]+\.[^@]+$",
        description="Unique and valid email address.",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Account security password (minimum 8 characters).",
    )

    @field_validator("username", mode="before")
    @classmethod
    def trim_username(cls, v: str) -> str:
        """Trim leading and trailing whitespaces from username candidate."""
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("email", mode="before")
    @classmethod
    def trim_email(cls, v: str) -> str:
        """Trim leading and trailing whitespaces from email candidate."""
        if isinstance(v, str):
            return v.strip()
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "alice",
                "email": "alice@example.com",
                "password": "securepassword123",
            }
        }
    }


class LoginRequest(BaseModel):
    """Payload to authenticate credentials and issue tokens."""

    username: str = Field(
        ...,
        description="Registered username or email address.",
    )
    password: str = Field(
        ...,
        description="Secret account password.",
    )
    device_name: str | None = Field(
        None,
        max_length=100,
        description="Optional label for identifying the login device.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "alice",
                "password": "securepassword123",
                "device_name": "Chrome / MacOS",
            }
        }
    }


class RefreshRequest(BaseModel):
    """Payload to refresh an expired access token."""

    refresh_token: str = Field(
        ...,
        description="Active refresh token string.",
    )
    device_name: str | None = Field(
        None,
        max_length=100,
        description="Optional label for identifying the refresh device.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "device_name": "Chrome / MacOS",
            }
        }
    }


class LogoutRequest(BaseModel):
    """Payload to revoke active session tokens."""

    refresh_token: str = Field(
        ...,
        description="Refresh token to invalidate.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            }
        }
    }


class ChangePasswordRequest(BaseModel):
    """Payload to modify current user credentials."""

    old_password: str = Field(
        ...,
        description="Current account password confirmation.",
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New replacement password (minimum 8 characters).",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "old_password": "securepassword123",
                "new_password": "newsecurepassword456",
            }
        }
    }


class UserResponse(BaseModel):
    """Serialized representation of a user profile."""

    id: int = Field(description="Unique database user primary key ID.")
    username: str = Field(description="User account unique name identifier.")
    email: str = Field(description="User registered email contact address.")
    role: UserRole = Field(description="User account privilege role (ADMIN/USER).")
    is_active: bool = Field(description="Indicates whether the account is active.")
    is_verified: bool = Field(
        description="Indicates whether the email address is verified."
    )
    created_at: datetime = Field(description="UTC timestamp of account registration.")
    updated_at: datetime = Field(description="UTC timestamp of last profile update.")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 42,
                "username": "alice",
                "email": "alice@example.com",
                "role": "USER",
                "is_active": True,
                "is_verified": False,
                "created_at": "2026-07-08T11:00:00Z",
                "updated_at": "2026-07-08T11:00:00Z",
            }
        },
    }


class TokenResponse(BaseModel):
    """Response containing access and refresh token data."""

    access_token: str = Field(description="Encoded access JWT token.")
    refresh_token: str = Field(description="Active session refresh token string.")
    token_type: str = Field(default="bearer", description="Token schema prefix type.")
    expires_in: int = Field(description="Access token lifespan in seconds.")
    auth_state: str = Field(
        default="AUTHENTICATED", description="Current authentication state."
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "secrets_token_urlsafe...",
                "token_type": "bearer",
                "expires_in": 1800,
                "auth_state": "AUTHENTICATED",
            }
        }
    }


class UserUpdateRequest(BaseModel):
    """Payload to update current user details."""

    email: str | None = Field(
        None,
        pattern=r"^[^@]+@[^@]+\.[^@]+$",
        description="Optional new email address.",
    )
    username: str | None = Field(
        None,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Optional new username.",
    )

    @field_validator("username", mode="before")
    @classmethod
    def trim_username(cls, v: str | None) -> str | None:
        """Trim whitespaces if value is provided."""
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("email", mode="before")
    @classmethod
    def trim_email(cls, v: str | None) -> str | None:
        """Trim whitespaces if value is provided."""
        if isinstance(v, str):
            return v.strip()
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "alice_updated",
                "email": "alice.new@example.com",
            }
        }
    }


class AdminUserUpdateRequest(BaseModel):
    """Payload for admin-only user profile alterations."""

    email: str | None = Field(None, pattern=r"^[^@]+@[^@]+\.[^@]+$")
    username: str | None = Field(
        None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$"
    )
    role: UserRole | None = Field(None, description="Privilege role level override.")
    is_active: bool | None = Field(None, description="Toggle user active status.")
    is_verified: bool | None = Field(
        None, description="Toggle user email verification."
    )

    @field_validator("username", mode="before")
    @classmethod
    def trim_username(cls, v: str | None) -> str | None:
        """Trim whitespaces if value is provided."""
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("email", mode="before")
    @classmethod
    def trim_email(cls, v: str | None) -> str | None:
        """Trim whitespaces if value is provided."""
        if isinstance(v, str):
            return v.strip()
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "role": "ADMIN",
                "is_active": False,
            }
        }
    }
