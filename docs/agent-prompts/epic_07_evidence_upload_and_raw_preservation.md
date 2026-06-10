# Epic 7 — Evidence Upload and Raw Preservation

Paste into **Agent mode** on branch `epic-7-evidence-upload-and-raw-preservation`.

```text
Follow @docs/agent-prompts/FAST_TRACK.md

Fast Track — Epic 7 ONLY. One session: build → test → push → PR → enable auto-merge.
Do NOT start Epic 8 (Azure blob swap). Do NOT delete local git branches.

---

## Read first

@PROJECT_PLAN.md
@AGENTS.md
@user_story/evidence-fusion-post-edap-full/02_epics/EPIC_07_evidence_upload_and_raw_preservation.md

Branch: epic-7-evidence-upload-and-raw-preservation (confirm checked out)
Linear: Epic LAL-11, Stories LAL-42, LAL-43
Repo: LalithShankar/forensic-evidence-fusion
Depends on: Epic 6 (merged — cases API, membership access, CaseDetail UI)

Also reuse patterns from Epic 6:
- backend/app/api/cases.py, case_service.py, auth_deps.check_case_access
- frontend CaseDetail route: /cases/:caseId

---

## Goal

Upload one evidence file to a case; preserve raw bytes unchanged locally; store artifact metadata + hash.

---

## Story 7.1 — Upload a single evidence file (LAL-42)

### Acceptance criteria
- [ ] In a case, upload supported file → Artifact record created
- [ ] Metadata stored: filename, size, extension, MIME type, uploader, upload time
- [ ] Upload failure → no fake completed artifact in UI or API

### Backend
1. Alembic migration `004_artifact_upload_fields` — expand `artifacts` table:
   - original_filename, file_size_bytes, file_extension, mime_type
   - uploaded_by (FK users.id), uploaded_at (timestamptz)
   - storage_path (relative path under local data root)
   - content_hash (SHA-256 hex, nullable until preserved)
   - status enum: pending | preserved | failed | blocked (default pending)
2. Update `backend/app/models/artifact.py` + `backend/app/schemas/artifact.py`
3. `backend/app/services/artifact_service.py` — create artifact row, orchestrate preservation
4. `backend/app/services/storage_service.py` — local raw write to configured data dir (APP_ENV=local uses e.g. `./data/raw` or setting from config; no Azure yet — Epic 8)
5. `backend/app/api/artifacts.py`:
   - POST `/cases/{case_id}/artifacts/upload` — multipart file upload, auth + case access (contributor+)
   - GET `/cases/{case_id}/artifacts` — list artifacts for case (viewer+)
   - GET `/cases/{case_id}/artifacts/{artifact_id}` — single artifact metadata
6. Register router in `backend/app/api/router.py`
7. Audit: `artifact.uploaded` via audit_service
8. Tests `backend/tests/test_artifacts.py`: create, metadata fields, access control, failed upload

### Frontend
1. Extend `apiClient` — uploadArtifact (multipart), listArtifacts, getArtifact
2. `frontend/src/pages/CaseUpload.tsx` — file picker, progress/error states, list recent uploads
3. Route `/cases/:caseId/upload` in App.tsx; link from CaseDetailPage
4. Tests: upload success shows artifact; validation/error states

**Out of scope:** ZIP extraction, categorization, transformation

---

## Story 7.2 — Preserve raw artifact before processing (LAL-43)

### Acceptance criteria
- [ ] After upload, original file stored unchanged on disk
- [ ] SHA-256 hash stored on artifact when preservation completes
- [ ] Preservation failure → status failed/blocked, not completed

### Backend
1. storage_service: write bytes atomically (temp file + rename); verify size matches
2. artifact_service: after write, compute hash, set status=preserved; on error status=failed
3. Extend tests: hash present, file bytes match upload, failure path

**Out of scope:** parsing, AI, Azure Blob (Epic 8)

---

## Conventions

- Routers thin; logic in services
- ruff + black + mypy; ESLint + Prettier
- Tests pass in CI without production credentials (SQLite fixtures OK)
- No secrets in code/commits; update `.env.example` if new vars (e.g. DATA_ROOT)
- Honor APP_ENV local/deployed

---

## Before push

cd backend && .venv/bin/pytest && .venv/bin/ruff check . && .venv/bin/black --check .
cd frontend && npm run lint && npm run test && npm run build

---

## Ship

git add …
git commit -m "Epic 7: evidence upload with local raw preservation and artifact metadata."
git push origin epic-7-evidence-upload-and-raw-preservation
gh pr create --base main --head epic-7-evidence-upload-and-raw-preservation \
  --title "Epic 7: Evidence upload and raw preservation" \
  --body "## Summary
- Multipart upload to case with membership access control
- Local raw file preservation + SHA-256 hash
- Case upload UI

## Linear
LAL-11, LAL-42, LAL-43

## Test plan
- [ ] pytest + frontend tests green
- [ ] login → case → upload file → artifact listed with metadata"
gh pr merge --auto --merge

Update STATUS.md Epic 7 tracker. End with AGENTS.md report.
Do NOT start Epic 8.
```

## Git (start of epic — already done if on branch)

```bash
cd /Users/lalithshankar/Documents/projects/forensic_v2
git checkout main && git pull origin main
git checkout epic-7-evidence-upload-and-raw-preservation
git pull origin epic-7-evidence-upload-and-raw-preservation
```
