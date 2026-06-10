"""Tests for environment configuration contract."""

from pathlib import Path

import pytest

from app.core.config import (
    DeployedSettings,
    LocalSettings,
    get_settings,
    reset_settings_cache,
)


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    reset_settings_cache()
    yield
    reset_settings_cache()


def test_local_settings_load_from_dotenv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "APP_ENV=local\n" "APP_NAME=test-local-app\n" "SECRET_KEY=local-test-secret\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("APP_ENV", "local")

    settings = LocalSettings()

    assert settings.app_env == "local"
    assert settings.app_name == "test-local-app"
    assert settings.secret_key == "local-test-secret"
    assert settings.secrets_source == "dotenv"


def test_deployed_settings_require_key_vault_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "deployed")
    monkeypatch.delenv("AZURE_KEY_VAULT_URL", raising=False)

    with pytest.raises(ValueError, match="AZURE_KEY_VAULT_URL"):
        DeployedSettings()


def test_deployed_settings_use_key_vault_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "deployed")
    monkeypatch.setenv("AZURE_KEY_VAULT_URL", "https://example.vault.azure.net/")

    settings = DeployedSettings()

    assert settings.is_deployed
    assert settings.secrets_source == "azure_key_vault_managed_identity"
    assert settings.azure_key_vault_url == "https://example.vault.azure.net/"


def test_cors_allowed_origins_default_to_local_frontend() -> None:
    settings = LocalSettings()

    assert settings.cors_origins_list == ["http://localhost:5173"]


def test_cors_allowed_origins_parse_comma_separated_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,https://app.example.com",
    )

    settings = LocalSettings()

    assert settings.cors_origins_list == [
        "http://localhost:5173",
        "https://app.example.com",
    ]


def test_applicationinsights_configured_when_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "APPLICATIONINSIGHTS_CONNECTION_STRING",
        "InstrumentationKey=test-key",
    )
    settings = LocalSettings()
    assert settings.applicationinsights_configured is True


def test_get_settings_respects_app_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "deployed")
    monkeypatch.setenv("AZURE_KEY_VAULT_URL", "https://example.vault.azure.net/")

    settings = get_settings()

    assert settings.app_env == "deployed"
    assert settings.secrets_source == "azure_key_vault_managed_identity"
