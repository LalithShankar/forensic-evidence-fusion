# Epic 20–22 R4 MVP Design Notes

## Epic 20 — Reporting & Audit

- **Report regenerate:** idempotent replace — one `draft` row per case; regenerate updates `content_json`, `title`, and `updated_at` in place.
- **Report sections (stable order):** `timeline_summary`, `claim_matrix`, `limitations`, `source_appendix`.
- **Audit read:** case-scoped; redact `password`, `secret`, `token`, `api_key`, `connection_string` keys from JSON blobs.
- **Audit coverage:** `case.created`, `case.updated`, `artifact.uploaded`, `claim.resolved`, `report.generated`.

## Epic 21 — Deployment

- **Secrets:** `APP_ENV=deployed` loads `DATABASE_URL`, `SECRET_KEY`, storage/search/openai keys from Key Vault by name matching `.env.example`.
- **CI:** Bicep syntax validated when `az` CLI present; structural fallback when absent.
- **No live deploy in CI** — templates + Dockerfile + mocked Key Vault tests only.

## Epic 22 — Observability & Ops

- **Ops summary:** `GET /operations/summary` restricted to `admin` and `case_manager` roles (global platform view).
- **Telemetry:** Application Insights via `azure-monitor-opentelemetry` only when `APP_ENV=deployed` and `APPLICATIONINSIGHTS_CONNECTION_STRING` is set; local/CI no-op.
- **Pipeline logs:** structured JSON at stage transitions with `stage`, `artifact_id`, `case_id`, `duration_ms`, `outcome`.
