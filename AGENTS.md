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

### Services (local dev)
| Service | Port | Start command |
|---------|------|---------------|
| PostgreSQL 16 | 5432 | `sudo service postgresql start` |
| Backend (FastAPI) | 8000 | `cd backend && source .venv/bin/activate && export APP_ENV=local && uvicorn app.main:app --reload --port 8000` |
| Frontend (Vite) | 5173 | `cd frontend && npm run dev` |

### First-time / cold-start checklist
1. Ensure PostgreSQL is running: `pg_isready -h localhost -p 5432` (install via `apt` if missing: `postgresql`, `python3.12-venv`).
2. Create DB once if absent: `sudo -u postgres createdb forensic_dev` and set password: `sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"`.
3. Copy env templates if `.env` files are missing: `cp backend/.env.example backend/.env` and `cp frontend/.env.example frontend/.env`.
4. Run migrations: `cd backend && source .venv/bin/activate && export APP_ENV=local && alembic upgrade head`.
5. Backend **requires** a reachable PostgreSQL instance at startup (`init_db_connection` in `app/main.py` lifespan); pytest uses SQLite in-memory and does not need Postgres.

### Lint / test (matches CI)
- **Backend** (`cd backend`, venv active): `ruff check .`, `black --check .`, `mypy app`, `pytest`
- **Frontend** (`cd frontend`): `npm run lint`, `npm run typecheck`, `npm run test`

### Gotchas
- Use the backend virtualenv at `backend/.venv` for all Python commands; do not install backend deps globally.
- `APP_ENV=local` must be set when running the backend so settings load from `backend/.env`.
- The Dashboard at `http://localhost:5173` calls `GET /health` on the backend — use it as a quick E2E smoke test (`Backend status: ok`).
