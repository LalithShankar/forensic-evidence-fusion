"""Key Vault secret loading tests (mocked — no network)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.config import DeployedSettings, reset_settings_cache
from app.core.keyvault import apply_keyvault_secrets, load_keyvault_secrets


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    reset_settings_cache()
    yield
    reset_settings_cache()


class _FakeSecret:
    def __init__(self, value: str) -> None:
        self.value = value


class _FakeSecretClient:
    def __init__(self, secrets: dict[str, str]) -> None:
        self._secrets = secrets

    def get_secret(self, name: str) -> _FakeSecret:
        if name not in self._secrets:
            raise KeyError(name)
        return _FakeSecret(self._secrets[name])


def _deployed_settings(monkeypatch: pytest.MonkeyPatch) -> DeployedSettings:
    monkeypatch.setenv("APP_ENV", "deployed")
    monkeypatch.setenv("AZURE_KEY_VAULT_URL", "https://test-vault.vault.azure.net/")
    return DeployedSettings()


def test_load_keyvault_secrets_maps_standard_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _deployed_settings(monkeypatch)
    fake_client = _FakeSecretClient(
        {
            "database-url": "postgresql+psycopg://user:pass@host/db",
            "secret-key": "vault-secret-key",
        }
    )

    with (
        patch("app.core.keyvault._build_credential", return_value=MagicMock()),
        patch("app.core.keyvault._build_secret_client", return_value=fake_client),
    ):
        loaded = load_keyvault_secrets(settings)

    assert loaded["DATABASE_URL"] == "postgresql+psycopg://user:pass@host/db"
    assert loaded["SECRET_KEY"] == "vault-secret-key"


def test_load_keyvault_skips_missing_secrets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _deployed_settings(monkeypatch)
    fake_client = _FakeSecretClient({"secret-key": "only-one"})

    with (
        patch("app.core.keyvault._build_credential", return_value=MagicMock()),
        patch("app.core.keyvault._build_secret_client", return_value=fake_client),
    ):
        loaded = load_keyvault_secrets(settings)

    assert "SECRET_KEY" in loaded
    assert "DATABASE_URL" not in loaded


def test_apply_keyvault_secrets_writes_to_environ(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _deployed_settings(monkeypatch)

    with patch(
        "app.core.keyvault.load_keyvault_secrets",
        return_value={"SECRET_KEY": "from-vault"},
    ):
        apply_keyvault_secrets(settings)

    assert settings is not None
    import os

    assert os.environ.get("SECRET_KEY") == "from-vault"


def test_local_settings_skip_keyvault() -> None:
    from app.core.config import LocalSettings

    settings = LocalSettings()
    assert load_keyvault_secrets(settings) == {}
