"""Azure Key Vault secret loading for deployed environments."""

from __future__ import annotations

import os
from typing import Any

from app.core.config import Settings

_SECRET_ENV_MAP: dict[str, str] = {
    "database-url": "DATABASE_URL",
    "secret-key": "SECRET_KEY",
    "azure-storage-connection-string": "AZURE_STORAGE_CONNECTION_STRING",
    "azure-search-api-key": "AZURE_SEARCH_API_KEY",
    "azure-openai-api-key": "AZURE_OPENAI_API_KEY",
    "applicationinsights-connection-string": "APPLICATIONINSIGHTS_CONNECTION_STRING",
}


def load_keyvault_secrets(settings: Settings) -> dict[str, str]:
    """Load configured secrets from Key Vault by standard secret names."""
    if not settings.is_deployed or not settings.azure_key_vault_url:
        return {}

    credential = _build_credential()
    client = _build_secret_client(settings.azure_key_vault_url, credential)

    loaded: dict[str, str] = {}
    for secret_name, env_key in _SECRET_ENV_MAP.items():
        try:
            secret = client.get_secret(secret_name)
        except Exception:
            continue
        if secret.value:
            loaded[env_key] = secret.value
    return loaded


def apply_keyvault_secrets(settings: Settings) -> Settings:
    """Merge Key Vault secrets into process env and return refreshed settings."""
    secrets = load_keyvault_secrets(settings)
    for env_key, value in secrets.items():
        os.environ[env_key] = value
    return settings


def _build_credential() -> Any:
    from azure.identity import DefaultAzureCredential

    return DefaultAzureCredential()


def _build_secret_client(vault_url: str, credential: Any) -> Any:
    from azure.keyvault.secrets import SecretClient

    return SecretClient(vault_url=vault_url, credential=credential)
