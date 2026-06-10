# Hybrid EDAP — Cloud Orchestrator + Local Workers

**Default runtime from Batch 3 onward.** Cloud coordinates; local agents write code and run tests.

## Architecture

| Role | Where | Edits code? | Cost profile |
|------|-------|---------------|--------------|
| **Manager (you)** | — | No | — |
| **Cloud Orchestrator** | Cloud (`&` prefix) | No | Low — status, Linear, dispatch only |
| **Local Builder** | Local Agent mode | Yes | Medium — main implementation |
| **Local Reviewer** | Local Ask mode | No | Low — AC checklist |
| **Local Integration** | Local Agent mode | Yes (CI/wiring only) | Low — only if CI fails |
| **Local QA** | Local Agent mode | No | Low — pytest + AC map |

Cloud agents **do not** spawn local agents automatically. The Orchestrator outputs copy-paste prompts; the Manager (or you) pastes them into local Cursor sessions.

## Per-epic flow

```
1. Cloud Orchestrator  → verify main, Linear, STATUS; output local prompts + git commands
2. Local Builder       → implement epic on branch; commit; push; open PR
3. [You review diff]
4. Local Reviewer      → AC + security report (no code changes)
5. Local Integration   → only if CI red or merge conflicts
6. Local QA            → pytest/lint; AC pass/fail table
7. Cloud Orchestrator  → update Linear (In Review → Done), STATUS.md, pipeline status
8. Manager             → merge PR
```

## Launch checklist

1. `git checkout main && git pull origin main`
2. Create feature branch: `git checkout -b epic-<n>-<slug>`
3. Start **Cloud Orchestrator** (`&` + prompt from `docs/agent-prompts/cloud_orchestrator.md`)
4. Paste **Local Builder** prompt into a local Agent chat (same repo folder or worktree)
5. After PR exists, run Reviewer → Integration (if needed) → QA locally
6. Report back to Cloud Orchestrator: `Batch status for Epic <n>?`
7. Merge when Orchestrator says **READY FOR MERGE** and you approve the diff

## Parallel batches (e.g. Epic 2 ∥ Epic 3)

- One **Cloud Orchestrator** session tracks both epics
- Two **local worktrees** + two **local Builder** sessions
- Scope locked: `backend/**` vs `frontend/**` only

## Prompt files

| File | Use |
|------|-----|
| `cloud_orchestrator.md` | Reusable cloud dispatch template (`&`) |
| `local_builder.md` | Reusable local Builder template |
| `local_reviewer.md` | Reusable local Reviewer (Ask) template |
| `local_integration.md` | Reusable local Integration template |
| `local_qa.md` | Reusable local QA template |
| `epic_04_dispatch.md` | Epic 4 filled-in prompts (current batch) |

## What cloud must NOT do

- Write feature code under `backend/**` or `frontend/**`
- Run the full Builder → QA pipeline in one cloud job (that is the old full-cloud model)
- Auto-merge PRs
- Commit secrets or real `.env` files

## What local must do

- All implementation, tests, CI fixes
- Open PR to `main`
- Never start the next epic until Orchestrator confirms dependencies merged
