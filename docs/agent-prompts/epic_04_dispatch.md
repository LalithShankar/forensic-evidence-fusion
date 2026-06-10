# Epic 4 — Hybrid dispatch (Batch 3)

**State:** dispatched · branch `epic-4-database-foundation` · Linear LAL-8 (In Progress)

## Step 1 — Cloud Orchestrator (paste with `&`)

```text
& You are the EDAP Cloud Orchestrator. You do NOT write feature code.

Repo: https://github.com/LalithShankar/forensic-evidence-fusion
Read: AGENT_WORKFLOW.md, docs/agent-prompts/HYBRID_EDAP.md, STATUS.md

Epic 4 — Database Foundation
Linear: LAL-8, Stories LAL-35, LAL-36, LAL-37
Branch: epic-4-database-foundation
Depends on: Epic 2 (merged)

Your job:
1. Confirm main has Epic 2+3 merged.
2. Confirm local branch epic-4-database-foundation exists (Manager may have created it).
3. Update Linear LAL-8, LAL-35, LAL-36, LAL-37 → In Progress (if not already).
4. Output ORCHESTRATOR DISPATCH — tell Manager to paste Local Builder prompt below into local Agent chat.
5. Monitor: when PR opens → Linear In Review; when QA pass + CI green → READY FOR MERGE.
6. Update STATUS.md epic tracker via PR or instruct Manager — do not write backend code.

End: ORCHESTRATOR STATUS — DISPATCHED
Do NOT implement Epic 4 yourself. Do NOT start Epic 5.
```

## Step 2 — Local Builder (paste here, Agent mode, NO `&`)

```text
You are the EDAP Local Builder for Epic 4 ONLY.

Read:
@PROJECT_PLAN.md
@AGENTS.md
@AGENT_WORKFLOW.md
@docs/agent-prompts/HYBRID_EDAP.md
@user_story/evidence-fusion-post-edap-full/02_epics/EPIC_04_database_foundation.md

Linear: Epic LAL-8, Stories LAL-35, LAL-36, LAL-37
Branch: epic-4-database-foundation (already checked out)
Scope: backend/** only. Do NOT touch frontend/**.

Implement Stories 4.1–4.3:
- 4.1: SQLAlchemy session, Alembic migrations, DATABASE_URL from config
- 4.2: Placeholder models — user, case, artifact (IDs + timestamps)
- 4.3: audit_log table + audit_service write helper + tests

Tests: CI must pass without production Postgres (SQLite test DB or pytest fixture).
Update backend/.env.example if needed. No secrets.

When done: commit, push, open PR to main. Update STATUS.md tracker.
End with AGENTS.md report. Stop — do not run Reviewer/QA (Orchestrator dispatches next).

Do NOT start Epic 5.
```

## Step 3 — Local Reviewer (Ask mode, after PR)

```text
EDAP Local Reviewer — Epic 4 only. Do NOT edit code.

Read: @user_story/evidence-fusion-post-edap-full/02_epics/EPIC_04_database_foundation.md
Branch/PR: epic-4-database-foundation

Check all ACs in EPIC_04. Security: no credentials in code/logs.
Verdict: APPROVED FOR QA | CHANGES REQUIRED
```

## Step 4 — Local Integration (only if CI red)

```text
EDAP Local Integration — Epic 4. CI/wiring only. Branch: epic-4-database-foundation.
Fix backend CI until green. No new features. No frontend/**.
```

## Step 5 — Local QA

```text
EDAP Local QA — Epic 4. Run pytest + lint on backend.
Map each EPIC_04 AC → pass/fail.
End: PIPELINE STATUS READY FOR MERGE or BLOCKED.
Update STATUS.md. Tell Manager to ping Cloud Orchestrator.
```

## Step 6 — Cloud Orchestrator status ping

```text
& Batch status for Epic 4?
PR + CI + STATUS.md + Linear LAL-8. READY FOR MERGE or BLOCKED?
No feature code.
```
