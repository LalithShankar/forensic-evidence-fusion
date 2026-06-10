# Agent Rules (apply to every agent in this repo)

## Project conventions
- Stack: React + TypeScript + Vite + Chakra UI (frontend); Python + FastAPI + Pydantic + SQLAlchemy + Alembic (backend); PostgreSQL; Azure Blob Storage; Azure OpenAI + Azure AI Search; Azure Container Apps + Key Vault + Application Insights. Full detail in PROJECT_PLAN.md.
- Style: Python uses ruff + black + mypy (routers thin, logic in services). TypeScript uses ESLint + Prettier, functional components, TanStack Query for server state. Honor APP_ENV (local/deployed).
- Tests: always write/maintain tests; run them before claiming done. Backend = Pytest; frontend = Vitest + React Testing Library.
- Branches: epic-<n>-<slug>. One PR per epic.
- Never commit secrets. Never auto-merge. Human approves all merges. Deployed secrets come only from Azure Key Vault via Managed Identity.

## Source of truth and board updates
- PROJECT_PLAN.md is the canonical plan. If it conflicts with any other doc, PROJECT_PLAN.md wins; report the conflict to the Manager.
- Linear is the product board (single source of truth for backlog/status). GitHub holds code, PRs, and CI.
- When you start/finish work, update the linked Linear issue state (via Linear MCP) and STATUS.md. Do not create duplicate GitHub story issues.

## Scope discipline
- Work ONLY on the assigned epic. Do not touch other epics' files.
- If a change requires touching shared code, STOP and report it instead.

## Mandatory end-of-task report (every agent, every task)
Output this block at the end of each run:

### Report
1. **Done:** what was implemented (bullet list).
2. **Changed:** files touched + one-line reason each.
3. **Conflicts:** conflicts with main and how resolved (or "none").
4. **Requirements:** each acceptance criterion -> met / not met.
5. **Open:** what still needs doing.
6. **Risks/assumptions:** anything you guessed or that may break later.

## Role guardrails
- Builder: implements; opens PR; does NOT review its own work as "approved".
- Reviewer: comments only, no code changes unless Manager says so.
- Integration: fixes ONLY wiring/config/CI/conflicts, no new features.
- QA: runs tests + edge cases; reports pass/fail; does not add features.

## Definition of Done
Nothing is "done" until acceptance criteria pass AND CI is green AND
STATUS.md is updated AND a human approves the merge.

## Cursor Cloud specific instructions

### System prerequisites (one-time on the VM)
- **PostgreSQL 16** via `apt` (no `docker-compose` in this repo). Start with `sudo pg_ctlcluster 16 main start` if `pg_isready` fails. Default dev DB: `forensic_dev`, user `postgres` / password `postgres` (matches `backend/.env.example`).
- **Python 3.11+** with `python3.12-venv` for the backend virtualenv at `backend/.venv`.
- **Node.js 20+** (CI uses 20; Node 22 also works).

### Local config
- Copy `backend/.env.example` → `backend/.env` and `frontend/.env.example` → `frontend/.env` if missing. Never commit `.env`.
- Run migrations before starting the API: `cd backend && source .venv/bin/activate && export APP_ENV=local && alembic upgrade head`.

### Running services (manual per session)
| Service | Command | URL |
|---------|---------|-----|
| PostgreSQL | `sudo pg_ctlcluster 16 main start` | `localhost:5432` |
| Backend API | `cd backend && source .venv/bin/activate && export APP_ENV=local && uvicorn app.main:app --reload --port 8000` | http://localhost:8000/health |
| Frontend | `cd frontend && npm run dev -- --host 0.0.0.0` | http://localhost:5173 |

Use tmux for long-running dev servers. The Dashboard at `/` calls `/health` and should show **Backend status: ok** when everything is wired correctly.

### Lint / test / build (see also `.github/workflows/ci.yml`)
- **Backend:** `cd backend && source .venv/bin/activate && ruff check . && black --check . && mypy app && pytest`
- **Frontend:** `cd frontend && npm run lint && npm run typecheck && npm run test && npm run build`

Backend tests use in-memory SQLite and do **not** require PostgreSQL. Running the live API **does** require PostgreSQL.
