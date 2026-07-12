"""Integration tests for AuditLog."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.audit_log import AuditLog


def test_login_creates_audit_log(client: TestClient, db_session: Session, test_user: dict[str, str]) -> None:
    """Test that a successful login creates an audit log."""
    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": test_user["email"],
            "password": test_user["password"],
            "device_name": "Test Device"
        }
    )
    assert response.status_code == 200
    
    # Check audit log
    logs = db_session.execute(
        select(AuditLog).where(AuditLog.action == "USER_LOGIN").order_by(AuditLog.timestamp.desc())
    ).scalars().all()
    
    assert len(logs) >= 1
    latest_log = logs[0]
    assert latest_log.status == "SUCCESS"
    assert "Test Device" in latest_log.details


def test_failed_login_creates_audit_log(client: TestClient, db_session: Session) -> None:
    """Test that a failed login creates an audit log."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "nonexistent@example.com",
            "password": "wrongpassword",
            "device_name": "Test Device"
        }
    )
    assert response.status_code == 400
    
    # Check audit log
    logs = db_session.execute(
        select(AuditLog).where(AuditLog.action == "LOGIN_FAILED").order_by(AuditLog.timestamp.desc())
    ).scalars().all()
    
    assert len(logs) >= 1
    latest_log = logs[0]
    assert latest_log.status == "FAILED"
    assert "nonexistent@example.com" in latest_log.details
