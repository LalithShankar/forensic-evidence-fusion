"""Application Insights telemetry bootstrap for deployed environments."""

from __future__ import annotations

import logging

from app.core.config import Settings

_telemetry_configured = False
logger = logging.getLogger("app.telemetry")


def init_telemetry(settings: Settings) -> None:
    """Configure Azure Monitor OpenTelemetry when deployed with a connection string."""
    global _telemetry_configured
    if _telemetry_configured:
        return

    if not settings.is_deployed or not settings.applicationinsights_configured:
        logger.info("telemetry_skipped app_env=%s", settings.app_env)
        return

    try:
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(
            connection_string=settings.applicationinsights_connection_string,
        )
        _telemetry_configured = True
        logger.info("telemetry_initialized exporter=azure_monitor")
    except Exception:
        logger.exception("telemetry_init_failed")
        raise
