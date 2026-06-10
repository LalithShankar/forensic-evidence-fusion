# Batch pipeline — Epics 10, 11, 12 (one paste, minimal Manager)

**Manager involvement:** paste once → walk away → merge happens via auto-merge when CI green (merge PRs **in order**: #10 → #11 → #12).

Paste into **Agent mode** on `main` (Epic 9 must already be merged).

```text
Follow @docs/agent-prompts/FAST_TRACK.md

BATCH PIPELINE — Epics 10, 11, 12 ONLY. One session. Three PRs. Minimal Manager.
Do NOT stop between epics to ask the Manager unless blocked (CI failure, ambiguous spec, shared-code conflict).
Do NOT start Epic 13. Do NOT delete local git branches.

Manager has delegated full build authority — implement all ACs, fix CI, open PRs, enable auto-merge. No per-epic approval gates.

---

## Read first (all phases)

@PROJECT_PLAN.md
@AGENTS.md
@user_story/evidence-fusion-post-edap-full/02_epics/EPIC_10_bulk_upload_and_categorization.md
@user_story/evidence-fusion-post-edap-full/02_epics/EPIC_11_review_queue.md
@user_story/evidence-fusion-post-edap-full/02_epics/EPIC_12_transformation_pipeline_mvp.md

Repo: LalithShankar/forensic-evidence-fusion
Base: main (Epic 9 merged — manifest + provenance metadata on artifacts)

Execution order (strict — each phase uses prior phase code):
  Phase 1: Epic 10  (LAL-14, LAL-48, LAL-49)
  Phase 2: Epic 11  (LAL-15, LAL-50, LAL-51) — requires Epic 10 classification
  Phase 3: Epic 12  (LAL-16, LAL-52, LAL-53) — requires Epic 11 ready_for_transformation

Branch strategy (stacked — do NOT wait for merge between phases):
  1. git checkout main && git pull origin main
  2. git checkout -b epic-10-bulk-upload-and-categorization
  3. … implement Epic 10 → commit → push → PR #1 to main → gh pr merge --auto --merge
  4. git checkout -b epic-11-review-queue   # FROM epic-10 branch
  5. … implement Epic 11 → commit → push → PR #2 to main → gh pr merge --auto --merge
  6. git checkout -b epic-12-transformation-pipeline-mvp   # FROM epic-11 branch
  7. … implement Epic 12 → commit → push → PR #3 to main → gh pr merge --auto --merge

Note: PR2/PR3 include prior epic commits until earlier PRs merge. That is expected.

---

## Phase 1 — Epic 10: Bulk Upload and Categorization

### Goal
Multi-file upload; partial failure handling; batch grouping; rule-based classification with confidence.

### Story 10.1 (LAL-48)
- [ ] Multiple files → each gets own Artifact
- [ ] One failure in batch → successes preserved, failures reported
- [ ] Batch grouping visible in recent uploads UI

### Backend
- `bulk_upload_service.py` — orchestrate multi-file upload reusing `artifact_service`
- Extend `artifacts.py` — e.g. `POST /cases/{case_id}/artifacts/bulk-upload` (multipart files[])
- Optional: `upload_batch_id` (UUID) on artifacts + migration for batch grouping
- Tests: multi success, partial failure, access control

### Frontend
- `BulkUpload.tsx` (or extend CaseUpload) — multi file picker, per-file results, batch label
- Route/link from case upload flow

### Story 10.2 (LAL-49)
- [ ] WhatsApp-like filename → suggest ThirdParty / WhatsApp + confidence
- [ ] Takeout ZIP → suggest Google / Takeout + confidence
- [ ] Low confidence → mark needs review (extend status or add `review_status` / `classification_confidence` fields — migration OK)

### Backend
- `classification_service.py` — rule-based (filename/MIME/extension), no LLM
- Run classification after successful preserve; store suggested metadata + confidence
- Tests for rules + low-confidence → needs review flag

### Frontend
- `ClassificationBadge.tsx` — show suggestion + confidence on artifact list/detail

Commit: `Epic 10: bulk upload and rule-based classification.`
Push + PR + auto-merge. Continue immediately to Phase 2 — do not wait for Manager.

---

## Phase 2 — Epic 11: Review Queue

### Goal
Queue for low-confidence / blocked artifacts; manual correction; approve → ready for transformation.

### Story 11.1 (LAL-50)
- [ ] Low-confidence artifacts in queue with suggested category + reason
- [ ] Blocked artifacts show blocker notes
- [ ] Empty state when nothing needs review

### Backend
- `review_queue.py` API + `review_service.py`
- `GET /cases/{case_id}/review-queue` — viewer+
- Filter: needs_review, blocked, low confidence (use fields from Epic 10)

### Frontend
- `ReviewQueue.tsx` + components under `components/review/`
- Route e.g. `/cases/:caseId/review`

### Story 11.2 (LAL-51)
- [ ] Correct source_group / source_family / artifact_type on review item
- [ ] Approve → status `ready_for_transformation` (extend ArtifactStatus or parallel field — document choice)
- [ ] Preserve-only → not eligible for auto transformation

### Backend
- `PATCH /cases/{case_id}/review-queue/{artifact_id}` or similar — contributor+
- Audit log for review actions

### Frontend
- `ReviewActions.tsx` — edit metadata, approve, preserve-only

Commit: `Epic 11: review queue and classification correction.`
Push + PR + auto-merge. Continue immediately to Phase 3.

---

## Phase 3 — Epic 12: Transformation Pipeline MVP

### Goal
State machine + MVP parsers (CSV, JSON, PDF text); outputs to readable/structured namespaces (Epic 8 paths).

Fast Track override: Epic 12 rubric says design doc first — write a **short** `docs/design/EPIC_12_transformation_mvp.md` in this PR (no separate Manager gate). Keep MVP synchronous or simple background task (no Azure workers yet).

### Story 12.1 (LAL-52)
- [ ] Ready artifact → start transformation → TransformationRecord created
- [ ] Stages visible: preserved → classified → preprocessed → extracted → readable_generated → structured_generated → blocked
- [ ] Stage failure → failure + limitation notes stored

### Backend
- Migration: `transformation_records` table
- `transformation_pipeline.py` — state machine, transitions, idempotency
- `transformations.py` API — e.g. POST start, GET status (case access)
- Enqueue/trigger when artifact is `ready_for_transformation` (manual POST OK for MVP)
- Write outputs via `StorageBackend` + `storage_paths` (readable / structured namespaces)

### Story 12.2 (LAL-53)
- [ ] CSV → structured rows + metadata
- [ ] JSON → readable + structured outputs
- [ ] PDF (extractable text) → text preview in readable namespace
- Parsers: `backend/app/parsers/csv_parser.py`, `json_parser.py`, `pdf_parser.py` + tests

Commit: `Epic 12: transformation pipeline MVP with CSV/JSON/PDF parsers.`
Push + PR + auto-merge.

---

## Conventions (all phases)

- Routers thin; logic in services
- ruff + black + mypy; ESLint + Prettier + vitest + build before each push
- Tests in CI without production credentials
- No secrets in commits; update `.env.example` only if new vars
- One commit message per epic minimum; one PR per epic (non-negotiable)
- Update STATUS.md once at end with Epic 10, 11, 12 trackers
- Update Linear LAL-14/15/16 + story issues → In Review, then Done after merge if possible

---

## Before each push

cd backend && .venv/bin/pytest && .venv/bin/ruff check . && .venv/bin/black --check . && .venv/bin/mypy app
cd frontend && npm run lint && npm run test && npm run build

---

## End of batch — single report for Manager

Output ONE AGENTS.md report covering all three epics:

### Report
1. **Done:** bullet per epic
2. **Changed:** files grouped by epic
3. **PRs:** URL for PR #10, #11, #12 + auto-merge enabled yes/no
4. **Requirements:** each epic AC → met / not met
5. **Open:** anything left
6. **Risks/assumptions:** stacked PR merge order, Epic 12 scope choices

Manager action after report: none required if auto-merge + CI green. Merge order 10 → 11 → 12 if GitHub queues them.
Do NOT start Epic 13.
```

## Git (optional — agent can run)

```bash
cd /Users/lalithshankar/Documents/projects/forensic_v2
git checkout main && git pull origin main
# Agent creates branches per phase above
```

## Your workflow (Manager)

1. Paste the block above once into Agent mode.
2. Go do something else.
3. Optionally skim the **one** final report (not three separate reviews).
4. If auto-merge is on, PRs merge themselves when CI passes (merge #10 first, then #11, #12).

## Next batch (later)

After 10–12 merge, create `batch_13_14_…` using the same pattern when dependencies allow.
