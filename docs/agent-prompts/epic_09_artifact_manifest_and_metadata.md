# Epic 9 — Artifact Manifest and Metadata

Paste into **Agent mode** on branch `epic-9-artifact-manifest-and-metadata`.

**Prerequisite:** Epics 7 and 8 merged to `main` (upload + `StorageBackend` + path namespaces). Confirm `main` is current before branching.

```text
Follow @docs/agent-prompts/FAST_TRACK.md

Fast Track — Epic 9 ONLY. One session: build → test → push → PR → enable auto-merge.
Do NOT start Epic 10 (bulk upload / categorization). Do NOT delete local git branches.

---

## Read first

@PROJECT_PLAN.md
@AGENTS.md
@user_story/evidence-fusion-post-edap-full/02_epics/EPIC_09_artifact_manifest_and_metadata.md

Optional field reference (names + intent — do not expand scope beyond Epic 9 ACs):
@user_story/evidence-fusion-pre-edap-full/05_schema/artifact_schema.md
@user_story/evidence-fusion-pre-edap-full/04_transformation/source_format_and_parser_matrix.md

Branch: epic-9-artifact-manifest-and-metadata (confirm checked out)
Linear: Epic LAL-13, Stories LAL-46, LAL-47
Repo: LalithShankar/forensic-evidence-fusion
Depends on: Epic 7 (artifact upload), Epic 8 (`StorageBackend`, `storage_paths`)

Reuse existing patterns:
- backend/app/models/artifact.py — Epic 7 fields + `ArtifactStatus` (keep lifecycle enum; do not replace with pre-edap status list)
- backend/app/schemas/artifact.py — `ArtifactPublic`
- backend/app/services/artifact_service.py — upload + list + get
- backend/app/api/artifacts.py — upload/list/get routes + case access
- frontend/src/pages/CaseUpload.tsx — artifact list (extend, do not rewrite upload flow)
- frontend/src/lib/apiClient.ts — artifact types + API methods

---

## Goal

Store source/provenance metadata on each artifact; expose artifact details in the UI; provide a case-level manifest API for downstream processors.

---

## Story 9.1 — Add source and artifact metadata fields (LAL-46)

### Acceptance criteria
- [ ] On upload, metadata can be stored: `source_group`, `source_family`, `artifact_type`, `collection_method`, `parser_class`
- [ ] When optional metadata is omitted, safe defaults apply (e.g. `"unknown"` — never null/empty where a value is required for manifest)
- [ ] Artifact detail view shows provenance metadata including `provenance_notes`

### Backend
1. Alembic migration `005_artifact_provenance_metadata` — add columns to `artifacts`:
   - `source_group` (String, not null, default `unknown`)
   - `source_family` (String, not null, default `unknown`)
   - `artifact_type` (String, not null, default `unknown`)
   - `collection_method` (String, not null, default `unknown`)
   - `parser_class` (String, not null, default `unknown`) — align with parser matrix classes 1–6 as string values (e.g. `direct_structured`, `readable_then_structured`, `archive_extraction`, `screenshot_ocr`, `backup_viewer`, `manual_escalation`, or `unknown`)
   - `provenance_notes` (Text, nullable)
2. Update `backend/app/models/artifact.py` + schemas:
   - Extend `ArtifactPublic` with new fields
   - Add `ArtifactMetadataInput` (optional fields for upload / future PATCH)
3. Extend upload API `POST /cases/{case_id}/artifacts/upload`:
   - Accept optional multipart form fields for metadata (alongside file)
   - Apply defaults when omitted
   - Do not break existing upload tests (file-only upload still works)
4. Optional: `PATCH /cases/{case_id}/artifacts/{artifact_id}` for contributor+ to update metadata + provenance_notes (only if needed for AC — prefer upload + detail read if sufficient)
5. Tests in `backend/tests/test_artifact_metadata.py` (or extend `test_artifacts.py`):
   - upload with metadata persisted
   - upload without metadata → defaults
   - GET single artifact returns provenance fields

### Frontend
1. Extend upload form (`CaseUpload.tsx`) with optional metadata fields (source group, family, type, collection method, parser class, provenance notes) — keep UX simple; defaults OK if user skips
2. Add artifact detail UI — prefer `frontend/src/pages/ArtifactDetail.tsx` route `/cases/:caseId/artifacts/:artifactId` OR dedicated component under `frontend/src/components/artifacts/`
3. Link artifact rows on CaseUpload → detail page
4. Extend `apiClient` types + `getArtifact`; detail page shows all provenance fields including notes
5. Tests: detail renders metadata; upload-with-metadata round-trip (mock API OK)

**Out of scope:** AI classification, auto-detect source from file content, bulk categorization (Epic 10)

---

## Story 9.2 — Generate artifact manifest records (LAL-47)

### Acceptance criteria
- [ ] Case manifest lists every artifact with: id, case_id, storage_path, status, content_hash, and metadata fields from 9.1
- [ ] When artifact status/metadata changes, manifest reflects current values
- [ ] Tests assert required provenance fields are never null where manifest contract requires them

### Backend
1. Add `backend/app/services/manifest_service.py`:
   - `build_case_manifest(artifacts: list[Artifact]) -> list[ArtifactManifestEntry]` (or similar pydantic model)
   - Include: id, case_id, storage_path, status, content_hash, source_group, source_family, artifact_type, collection_method, parser_class, provenance_notes, uploaded_at, uploaded_by, original_filename, file_extension, mime_type, file_size_bytes
   - Stable field names for downstream processors
2. Add schema `backend/app/schemas/manifest.py` — `ArtifactManifestEntry`, `CaseArtifactManifest`
3. Add API route (viewer+ case access):
   - `GET /cases/{case_id}/artifacts/manifest` → `CaseArtifactManifest`
   - Reuse `artifact_service.list_artifacts_for_case`; 404 when case inaccessible (same pattern as list artifacts)
4. Register route in `backend/app/api/artifacts.py` (or thin `manifest.py` router if cleaner)
5. Tests `backend/tests/test_manifest_service.py`:
   - manifest includes all artifacts for case
   - required fields populated (defaults when not set)
   - status change reflected (update artifact in test, rebuild manifest)
   - access control: no manifest for inaccessible case

**Out of scope:** manifest download/export UI, CSV/JSON file export, transformation pipeline (Epic 12)

---

## Conventions

- Routers thin; logic in services
- ruff + black + mypy; ESLint + Prettier on frontend
- Tests pass in CI without production credentials (SQLite fixtures OK)
- No secrets in code/commits; no new secrets expected — skip `.env.example` unless you add config
- Honor APP_ENV local/deployed; do not change storage abstraction from Epic 8
- One PR per epic; end with AGENTS.md mandatory report block

---

## Before push

cd backend && .venv/bin/pytest && .venv/bin/ruff check . && .venv/bin/black --check . && .venv/bin/mypy app
cd frontend && npm run lint && npm run test && npm run build

---

## Ship

git add …
git commit -m "Epic 9: artifact provenance metadata and case manifest API."
git push origin epic-9-artifact-manifest-and-metadata
gh pr create --base main --head epic-9-artifact-manifest-and-metadata \
  --title "Epic 9: Artifact manifest and metadata" \
  --body "## Summary
- Provenance metadata fields on artifacts (upload + detail UI)
- Case artifact manifest API for downstream processors

## Linear
LAL-13, LAL-46, LAL-47

## Test plan
- [ ] pytest + frontend tests green
- [ ] upload with/without metadata → detail + manifest correct"
gh pr merge --auto --merge

Update STATUS.md Epic 9 tracker. Update Linear LAL-13, LAL-46, LAL-47 → In Review.
End with AGENTS.md report.
Do NOT start Epic 10.
```

## Git (start of epic)

```bash
cd /Users/lalithshankar/Documents/projects/forensic_v2
git checkout main && git pull origin main
git checkout -b epic-9-artifact-manifest-and-metadata
git push -u origin epic-9-artifact-manifest-and-metadata
```

## Paste pattern

```text
Follow @docs/agent-prompts/FAST_TRACK.md

@docs/agent-prompts/epic_09_artifact_manifest_and_metadata.md
```
