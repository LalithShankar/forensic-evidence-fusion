"""Smoke tests for the health endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["app_env"] in {"local", "deployed"}
    assert payload["secrets_source"] in {"dotenv", "azure_key_vault_managed_identity"}
    assert "secret_key" not in payload
    assert "database_url" not in payload


def test_health_exposes_app_env_without_secrets() -> None:
    response = client.get("/health")
    payload = response.json()

    assert "app_env" in payload
    assert set(payload.keys()) <= {"status", "app_env", "secrets_source"}


def test_cors_allows_configured_local_origin() -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
