"""Integration tests for RBAC endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user import User, UserRole


def test_user_cannot_access_admin_route(
    client: TestClient, db_session: Session, normal_user_token: dict[str, str]
) -> None:
    """Test that a USER role cannot access admin health endpoints."""
    headers = {"Authorization": f"Bearer {normal_user_token['access_token']}"}
    response = client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 403
    assert "Not enough permissions to perform this action." in response.json()["detail"]


def test_admin_can_access_admin_route(
    client: TestClient, db_session: Session, admin_token: dict[str, str]
) -> None:
    """Test that an ADMIN role can access admin health endpoints."""
    headers = {"Authorization": f"Bearer {admin_token['access_token']}"}
    response = client.get("/api/v1/admin/users", headers=headers)
    assert response.status_code == 200


def test_admin_cannot_delete_last_admin(
    client: TestClient, db_session: Session, admin_token: dict[str, str]
) -> None:
    """Test that the last admin cannot be deleted."""
    headers = {"Authorization": f"Bearer {admin_token['access_token']}"}

    # Ensure there's only 1 admin
    admins = (
        db_session.execute(select(User).where(User.role == UserRole.ADMIN))
        .scalars()
        .all()
    )
    assert len(admins) == 1

    admin_id = admins[0].id

    response = client.delete(f"/api/v1/admin/users/{admin_id}", headers=headers)
    assert response.status_code == 400
    assert "You cannot delete your own admin account" in response.json()["detail"]


def test_admin_cannot_demote_last_admin(
    client: TestClient, db_session: Session, admin_token: dict[str, str]
) -> None:
    """Test that the last admin cannot be demoted."""
    headers = {"Authorization": f"Bearer {admin_token['access_token']}"}

    admins = (
        db_session.execute(select(User).where(User.role == UserRole.ADMIN))
        .scalars()
        .all()
    )
    assert len(admins) == 1

    admin_id = admins[0].id

    payload = {"role": "USER"}
    response = client.patch(
        f"/api/v1/admin/users/{admin_id}", json=payload, headers=headers
    )

    assert response.status_code == 400
    assert "You cannot demote your own admin account" in response.json()["detail"]
