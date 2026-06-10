# Forensic Evidence Fusion Platform

A secure web platform for collecting, preserving, transforming, and analyzing digital evidence with provenance and human review at every step.

## Repository layout

| Path | Purpose |
|------|---------|
| `backend/` | Python FastAPI API and workers |
| `frontend/` | React + TypeScript + Vite UI |
| `docs/` | Architecture and runbooks |
| `infra/` | Deployment and infrastructure templates |
| `scripts/` | Developer and CI helper scripts |
| `tests/` | Cross-cutting integration tests (future) |

## Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ (local dev; optional for Epic 1 stubs)

## Local setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
export APP_ENV=local
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

Open http://localhost:5173 (frontend) and http://localhost:8000/health (backend).

## Environment contract

- **`APP_ENV=local`**: configuration loads from `.env` files (never committed).
- **`APP_ENV=deployed`**: secrets are loaded from Azure Key Vault via Managed Identity (no `.env` in production).

See `backend/.env.example` and `frontend/.env.example` for variable names only.

## Repo conventions

- Read `PROJECT_PLAN.md` first — it is the single source of truth.
- Agent rules: `AGENTS.md` and `AGENT_WORKFLOW.md`.
- Epic progress: `STATUS.md`.
- Branches: `epic-<n>-<slug>`; one PR per epic; human approval required before merge.
- Never commit secrets or `.env` files.

## CI

Pull requests to `main` run backend lint/format/test, frontend lint/type-check/test, and a secret scan. See `.github/workflows/ci.yml`.

## Branch protection

Configure `main` on GitHub to require pull requests, passing CI checks, and at least one approval before merge (see `docs/branch-protection.md`).
