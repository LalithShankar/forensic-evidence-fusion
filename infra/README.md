# Infrastructure

Azure deployment templates and documentation for Epic 21+.

## Contents

| Path | Purpose |
|------|---------|
| [main.bicep](./main.bicep) | Subscription-scoped deployment — resource group + core module |
| [modules/core.bicep](./modules/core.bicep) | Postgres, Storage, Key Vault, Container Apps, Static Web App, App Insights |
| [../docs/deployment.md](../docs/deployment.md) | Step-by-step deploy guide, secret names, env mapping |
| [../docs/infra/AZURE_RESOURCES_PLAN.md](../docs/infra/AZURE_RESOURCES_PLAN.md) | SKU choices and procurement timing |

## Validate locally / CI

```bash
./scripts/validate_infra.sh
```

Uses `az bicep build` when Azure CLI is installed; otherwise checks required files only.

## Backend container

```bash
docker build -t forensic-api backend/
```

See `docs/deployment.md` for Managed Identity, Key Vault secret names, and frontend `VITE_API_BASE_URL` build contract.
