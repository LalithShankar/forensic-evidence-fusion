"""Authentication API tests."""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Generator
from io import StringIO

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import StructuredJsonFormatter, clear_log_context
from app.core.security import hash_password
from app.db.session import get_db
from app.main import app
from app.models.user import User, UserRole, UserStatus
from app.services.audit_service import write_audit_log


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """API client with database session override."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def create_test_user(
    db_session: Session,
    *,
    email: str = "analyst@local.dev",
    password: str = "DevPassword123!",
    role: UserRole = UserRole.analyst,
    status: UserStatus = UserStatus.active,
) -> User:
    user = User(
        email=email,
        display_name="Test Analyst",
        password_hash=hash_password(password),
        role=role,
        status=status,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_login_success_returns_jwt(client: TestClient, db_session: Session) -> None:
    user = create_test_user(db_session)

    response = client.post(
        "/auth/login",
        json={"email": user.email, "password": "DevPassword123!"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["expires_in"] == get_settings().access_token_expire_minutes * 60
    decoded = jwt.decode(
        payload["access_token"],
        get_settings().secret_key,
        algorithms=["HS256"],
    )
    assert decoded["sub"] == str(user.id)
    assert decoded["role"] == user.role.value
    assert "password_hash" not in payload


def test_login_invalid_credentials_are_generic(
    client: TestClient,
    db_session: Session,
) -> None:
    create_test_user(db_session)

    wrong_password = client.post(
        "/auth/login",
        json={"email": "analyst@local.dev", "password": "wrong-password"},
    )
    unknown_email = client.post(
        "/auth/login",
        json={"email": "missing@local.dev", "password": "DevPassword123!"},
    )

    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401
    assert wrong_password.json()["detail"] == "Invalid email or password"
    assert unknown_email.json()["detail"] == "Invalid email or password"


def test_unauthenticated_routes_return_401(client: TestClient) -> None:
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/protected/ping").status_code == 401


def test_auth_me_returns_role_and_status(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session, role=UserRole.admin, status=UserStatus.active)
    login = client.post(
        "/auth/login",
        json={"email": user.email, "password": "DevPassword123!"},
    )
    token = login.json()["access_token"]

    response = client.get("/auth/me", headers=auth_header(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(user.id)
    assert payload["email"] == user.email
    assert payload["role"] == "admin"
    assert payload["status"] == "active"
    assert "password_hash" not in payload


def test_protected_ping_returns_current_user_id(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    login = client.post(
        "/auth/login",
        json={"email": user.email, "password": "DevPassword123!"},
    )
    token = login.json()["access_token"]

    response = client.get("/auth/protected/ping", headers=auth_header(token))

    assert response.status_code == 200
    assert response.json()["user_id"] == str(user.id)


def test_disabled_user_blocked_on_login_and_token_use(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session, status=UserStatus.disabled)

    login = client.post(
        "/auth/login",
        json={"email": user.email, "password": "DevPassword123!"},
    )
    assert login.status_code == 403
    assert login.json()["detail"] == "Account disabled"

    active_user = create_test_user(
        db_session,
        email="active@local.dev",
        status=UserStatus.active,
    )
    token = client.post(
        "/auth/login",
        json={"email": active_user.email, "password": "DevPassword123!"},
    ).json()["access_token"]

    active_user.status = UserStatus.disabled
    db_session.commit()

    me = client.get("/auth/me", headers=auth_header(token))
    assert me.status_code == 403
    assert me.json()["detail"] == "Account disabled"


def test_authenticated_request_logs_user_id(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    login = client.post(
        "/auth/login",
        json={"email": user.email, "password": "DevPassword123!"},
    )
    token = login.json()["access_token"]

    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(StructuredJsonFormatter())
    logger = logging.getLogger("app.request")
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False

    clear_log_context()
    response = client.get("/auth/me", headers=auth_header(token))
    assert response.status_code == 200

    logged = False
    for line in stream.getvalue().splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if payload.get("user_id") == str(user.id):
            logged = True
            break
    assert logged


def test_audit_service_accepts_authenticated_user_id(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    object_id = uuid.uuid4()

    entry = write_audit_log(
        db_session,
        user_id=user.id,
        action="login",
        object_type="user",
        object_id=object_id,
    )

    assert entry.user_id == user.id


def test_logout_returns_204(client: TestClient, db_session: Session) -> None:
    user = create_test_user(db_session)
    login = client.post(
        "/auth/login",
        json={"email": user.email, "password": "DevPassword123!"},
    )
    token = login.json()["access_token"]

    response = client.post("/auth/logout", headers=auth_header(token))

    assert response.status_code == 204
