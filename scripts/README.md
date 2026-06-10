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
