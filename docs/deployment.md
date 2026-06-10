# Azure Deployment Guide

Deploy the Forensic Evidence Fusion MVP to Azure using Bicep templates in `infra/`.

## Prerequisites

- Azure CLI (`az`) logged in with subscription access
- Docker (to build the backend image)
- Node.js 20+ (frontend static build)
- PostgreSQL client optional (smoke checks)

## Resources provisioned

| Resource | Template | Notes |
|----------|----------|-------|
| Resource Group | `infra/main.bicep` | `rg-forensic-mvp-<env>` |
| PostgreSQL Flexible Server (B1ms) | `infra/modules/core.bicep` | Burstable SKU |
| Storage Account + `forensic-evidence` container | core module | Standard LRS |
| Key Vault | core module | RBAC-enabled |
| Container Apps environment + API app | core module | Scale 0–2 |
| Static Web Apps (Free) | core module | Frontend static hosting |
| Application Insights | core module | Epic 22 telemetry |

## Step 1 — Deploy infrastructure

```bash
cd infra
az deployment sub create \
  --location eastus \
  --template-file main.bicep \
  --parameters environmentName=dev \
               postgresAdminLogin=forensicadmin \
               postgresAdminPassword='<strong-password>'
```

Record outputs: `keyVaultName`, `postgresFqdn`, `containerAppFqdn`, `staticWebAppHostname`.

## Step 2 — Store secrets in Key Vault

Secret names must match `backend/app/core/keyvault.py`:

| Key Vault secret name | Maps to env var |
|-----------------------|-----------------|
| `database-url` | `DATABASE_URL` |
| `secret-key` | `SECRET_KEY` |
| `azure-storage-connection-string` | `AZURE_STORAGE_CONNECTION_STRING` |
| `azure-search-api-key` | `AZURE_SEARCH_API_KEY` |
| `azure-openai-api-key` | `AZURE_OPENAI_API_KEY` |
| `applicationinsights-connection-string` | `APPLICATIONINSIGHTS_CONNECTION_STRING` |

```bash
VAULT_NAME=<keyVaultName from output>
az keyvault secret set --vault-name $VAULT_NAME --name database-url --value "postgresql+psycopg://..."
az keyvault secret set --vault-name $VAULT_NAME --name secret-key --value "<random-32+-chars>"
```

## Step 3 — Managed Identity access

Grant the Container App system-assigned identity:

- **Key Vault Secrets User** on the vault
- **Storage Blob Data Contributor** on the storage account (if using MI for blob later)

```bash
# Example — replace IDs from Azure portal / az resource show
az role assignment create --role "Key Vault Secrets User" \
  --assignee <container-app-principal-id> --scope <key-vault-resource-id>
```

Non-secret env vars set on the Container App (see Bicep):

- `APP_ENV=deployed`
- `AZURE_KEY_VAULT_URL=https://<vault>.vault.azure.net/`
- `AZURE_STORAGE_CONTAINER=forensic-evidence`
- `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_INDEX`
- `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_CHAT_DEPLOYMENT`, `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`
- `CORS_ALLOWED_ORIGINS=https://<static-web-app-hostname>`

## Step 4 — Build and deploy backend

```bash
cd backend
docker build -t forensic-api:latest .
# Push to ACR and update Container App image (follow-up — not wired in CI)
```

Run migrations against deployed Postgres before serving traffic:

```bash
APP_ENV=deployed DATABASE_URL=... alembic upgrade head
```

Health check: `GET https://<containerAppFqdn>/health` — must not expose secrets.

## Step 5 — Build and deploy frontend

```bash
cd frontend
VITE_APP_ENV=deployed \
VITE_API_BASE_URL=https://<containerAppFqdn> \
npm run build
```

Deploy `frontend/dist` to Static Web Apps (GitHub Actions or `az staticwebapp` — **follow-up**, not in CI).

## Local vs deployed

| Concern | Local (`APP_ENV=local`) | Deployed |
|---------|-------------------------|----------|
| Secrets | `.env` | Key Vault + Managed Identity |
| Storage | `./data` filesystem | Azure Blob |
| AI Search / OpenAI | Mocks when unset | Real Azure services |
| App Insights | No-op | Enabled when connection string set |

## CI note

GitHub Actions validates Bicep syntax when `az` is available; no live Azure deploy in CI.

## Post-MVP follow-ups

- GitHub Actions workflow for image push + Container App revision
- Static Web Apps CI deploy on `main`
- Production SKU hardening (see `docs/infra/AZURE_RESOURCES_PLAN.md`)
