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
