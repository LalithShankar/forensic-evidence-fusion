# Epic 8 — Blob Storage Integration

Paste into **Agent mode** on branch `epic-8-blob-storage-integration`.

**Prerequisite:** Epic 7 merged to `main` (artifact upload + local raw preservation). If not merged yet, wait or branch from latest `main` after merge.

```text
Follow @docs/agent-prompts/FAST_TRACK.md

Fast Track — Epic 8 ONLY. One session: build → test → push → PR → enable auto-merge.
Do NOT start Epic 9 (artifact manifest). Do NOT delete local git branches.

---

## Read first

@PROJECT_PLAN.md
@AGENTS.md
@user_story/evidence-fusion-post-edap-full/02_epics/EPIC_08_blob_storage_integration.md

Branch: epic-8-blob-storage-integration (confirm checked out)
Linear: Epic LAL-12, Stories LAL-44, LAL-45
Repo: LalithShankar/forensic-evidence-fusion
Depends on: Epic 7 (merged — artifact upload, `storage_service.preserve_raw`, `artifact_service`)

Reuse Epic 7 patterns (refactor, do not rewrite upload flow):
- backend/app/services/storage_service.py — today: `LocalStorageService.preserve_raw`
- backend/app/services/artifact_service.py — calls storage for raw preservation + hash
- backend/app/api/artifacts.py — `get_storage` dependency
- backend/tests/test_artifacts.py — storage override fixture

Scope: **backend only** for this epic. No frontend changes unless a type import breaks CI.

---

## Goal

One storage abstraction selected by `APP_ENV`; separate path namespaces for raw / readable / structured outputs. Epic 7 upload behavior must keep working unchanged in local mode.

---

## Story 8.1 — Create storage abstraction (LAL-44)

### Acceptance criteria
- [ ] `APP_ENV=local` → file stored via local filesystem (default) or Azurite when blob connection string is configured
- [ ] `APP_ENV=deployed` → Azure Blob Storage backend used
- [ ] API / artifact services call the abstraction only — no direct `LocalStorageService` or Azure SDK in routers

### Backend
1. Refactor `backend/app/services/storage_service.py`:
   - Define `StorageBackend` protocol or ABC with at least:
     - `preserve_raw(case_id, artifact_id, original_filename, content) -> tuple[str, str]`  # path/key + SHA-256 hex
   - `LocalStorageBackend` — move existing Epic 7 atomic write + hash logic here
   - `AzureBlobStorageBackend` — upload blob via `azure-storage-blob` (sync client OK; match existing sync upload flow)
   - `get_storage_service(settings) -> StorageBackend` factory:
     - `APP_ENV=deployed` → Azure backend (require blob config; fail fast with clear error if missing)
     - `APP_ENV=local` → local filesystem by default; if `AZURE_STORAGE_CONNECTION_STRING` is set, allow Azurite/azure emulator via same Azure backend (optional local path — document in `.env.example`)
2. Update `backend/app/core/config.py` + `backend/.env.example`:
   - `AZURE_STORAGE_CONNECTION_STRING` (optional local / required deployed)
   - `AZURE_STORAGE_CONTAINER` (default e.g. `forensic-evidence`)
   - Keep `DATA_ROOT` for local filesystem root
   - Deployed: connection string comes from env/Key Vault contract (name only in `.env.example`; never commit secrets)
3. Update dependents to use `StorageBackend` type (not `LocalStorageService`):
   - `artifact_service.py`, `artifacts.py`, tests
4. Add `azure-storage-blob` to `backend/pyproject.toml` dependencies
5. Tests `backend/tests/test_storage_service.py`:
   - local preserve_raw round-trip (bytes unchanged, hash correct)
   - factory returns local backend when `APP_ENV=local` and no azure connection string
   - factory returns Azure backend when `APP_ENV=deployed` (mock settings)
   - factory returns Azure backend for local + Azurite connection string (optional AC)
   - Azure `preserve_raw` uses mocks — **no real Azure calls in CI**
6. Keep existing `test_artifacts.py` green after refactor

**Out of scope:** provisioning Azure resources, Key Vault wiring (Epic 21), async refactor of upload API

---

## Story 8.2 — Store generated outputs separately from raw files (LAL-45)

### Acceptance criteria
- [ ] Raw artifact path/key lands under a **raw** namespace
- [ ] Readable output path helper lands under a **readable** namespace (no generation yet)
- [ ] Structured output path helper lands under a **structured** namespace (no generation yet)

### Backend
1. Add `backend/app/services/storage_paths.py`:
   - `StorageNamespace` enum: `raw`, `readable`, `structured`
   - `build_object_key(case_id, artifact_id, filename, namespace) -> str`
   - Conventions (local + blob):
     - `raw/{case_id}/{artifact_id}/{safe_filename}`
     - `readable/{case_id}/{artifact_id}/{safe_filename}`
     - `structured/{case_id}/{artifact_id}/{safe_filename}`
   - Sanitize filename (basename only; reject empty)
2. Wire `LocalStorageBackend` and `AzureBlobStorageBackend` to use `build_object_key(..., StorageNamespace.raw)` for `preserve_raw`
3. Expose path builders for readable/structured so Epic 12+ can call them without new path logic
4. Tests `backend/tests/test_storage_paths.py`:
   - each namespace produces distinct prefix
   - same inputs → stable keys
   - raw upload path matches Epic 7 layout (or migration note if prefix changes — prefer keeping `raw/...` as today)

**Out of scope:** readable preview generation, structured dataset storage, DB schema changes beyond existing `storage_path` field

---

## Conventions

- Routers thin; logic in services
- ruff + black + mypy; honor `APP_ENV` local/deployed
- Tests pass in CI without production credentials (SQLite + tmp_path + mocks)
- No secrets in code/commits; `.env.example` lists new var names only
- Do not touch frontend, infra provisioning, or Epic 9 files

---

## Before push

cd backend && .venv/bin/pytest && .venv/bin/ruff check . && .venv/bin/black --check . && .venv/bin/mypy app

(No frontend work expected — skip npm unless you changed frontend.)

---

## Ship

git add …
git commit -m "Epic 8: storage abstraction with APP_ENV local/Azure swap and path namespaces."
git push origin epic-8-blob-storage-integration
gh pr create --base main --head epic-8-blob-storage-integration \
  --title "Epic 8: Blob storage integration" \
  --body "## Summary
- StorageBackend abstraction (local filesystem + Azure Blob by APP_ENV)
- Optional Azurite via connection string in local mode
- raw/readable/structured path namespace helpers

## Linear
LAL-12, LAL-44, LAL-45

## Test plan
- [ ] pytest green (storage + artifacts)
- [ ] local upload still preserves raw file + hash under raw/ namespace"
gh pr merge --auto --merge

Update STATUS.md Epic 8 tracker. Update Linear LAL-12, LAL-44, LAL-45 → In Review.
End with AGENTS.md report.
Do NOT start Epic 9.
```

## Git (start of epic)

```bash
cd /Users/lalithshankar/Documents/projects/forensic_v2
git checkout main && git pull origin main
git checkout -b epic-8-blob-storage-integration
git push -u origin epic-8-blob-storage-integration
```

## Paste pattern

```text
Follow @docs/agent-prompts/FAST_TRACK.md

@docs/agent-prompts/epic_08_blob_storage_integration.md
```
