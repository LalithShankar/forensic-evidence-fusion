"""Application settings with local vs deployed environment contract."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Base settings shared across environments."""

    model_config = SettingsConfigDict(
        env_file=None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["local", "deployed"] = Field(default="local", alias="APP_ENV")
    app_name: str = Field(default="forensic-evidence-fusion", alias="APP_NAME")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    log_level: str = Field(default="info", alias="LOG_LEVEL")
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/forensic_dev",
        alias="DATABASE_URL",
    )
    secret_key: str = Field(default="change-me-in-local-env-only", alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(
        default=30,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    azure_key_vault_url: str | None = Field(default=None, alias="AZURE_KEY_VAULT_URL")
    cors_allowed_origins: str = Field(
        default="http://localhost:5173",
        alias="CORS_ALLOWED_ORIGINS",
    )
    data_root: str = Field(default="./data", alias="DATA_ROOT")
    azure_storage_connection_string: str | None = Field(
        default=None,
        alias="AZURE_STORAGE_CONNECTION_STRING",
    )
    azure_storage_container: str = Field(
        default="forensic-evidence",
        alias="AZURE_STORAGE_CONTAINER",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]

    @property
    def is_local(self) -> bool:
        return self.app_env == "local"

    @property
    def is_deployed(self) -> bool:
        return self.app_env == "deployed"

    @property
    def secrets_source(self) -> str:
        if self.is_local:
            return "dotenv"
        return "azure_key_vault_managed_identity"


class LocalSettings(Settings):
    """Local development: load configuration from .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class DeployedSettings(Settings):
    """Deployed: secrets from Azure Key Vault via Managed Identity."""

    model_config = SettingsConfigDict(
        env_file=None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def model_post_init(self, __context: object) -> None:
        if not self.azure_key_vault_url:
            msg = (
                "AZURE_KEY_VAULT_URL must be set when APP_ENV=deployed; "
                "secrets are loaded from Azure Key Vault using Managed Identity."
            )
            raise ValueError(msg)


def _resolve_settings_class() -> type[Settings]:
    app_env = os.getenv("APP_ENV", "local").lower()
    if app_env == "deployed":
        return DeployedSettings
    return LocalSettings


@lru_cache
def get_settings() -> Settings:
    """Return cached settings for the active APP_ENV."""
    settings_cls = _resolve_settings_class()
    return settings_cls()


def reset_settings_cache() -> None:
    """Clear cached settings (used in tests)."""
    get_settings.cache_clear()
