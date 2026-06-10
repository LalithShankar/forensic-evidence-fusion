# Scripts

Developer and CI helper scripts.

## `smoke_pipeline.sh`

Full API + UI smoke test for Epics 10–12 (bulk upload → review queue →
transformation). Uses in-memory DB and mocked frontend fetch — no running server
required.

```bash
./scripts/smoke_pipeline.sh
```

Or backend only:

```bash
cd backend && .venv/bin/pytest -m smoke -v
```

## `smoke_pipeline_live.sh`

Same pipeline against a **running** backend (real DB + storage). No frontend
browser — HTTP only.

**One-time setup:**

```bash
cd backend
alembic upgrade head
cd ..
LOCAL_DEV_PASSWORD='DevPassword123!' python scripts/seed_local_users.py
cd backend && APP_ENV=local uvicorn app.main:app --port 8000
```

**Run (separate terminal):**

```bash
SMOKE_EMAIL=analyst@local.dev \
SMOKE_PASSWORD='DevPassword123!' \
./scripts/smoke_pipeline_live.sh
```

Override `BASE_URL` if the API is not on `http://localhost:8000`.
