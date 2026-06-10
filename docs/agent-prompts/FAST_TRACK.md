# Fast Track — Solo Manager mode (default)

Use this when you are the only human: build → PR → merge on CI green.
Skip Reviewer, QA, Integration, and Cloud Orchestrator unless CI fails.

## Loop (every epic)

```bash
cd forensic_v2
git checkout main && git pull origin main
git checkout -b epic-<n>-<slug>
```

1. Paste **one** agent prompt — prefer ready-made `docs/agent-prompts/epic_<NN>_<slug>.md`, or fill `epic_one_shot_builder.md`.
2. Agent: implement → run tests → commit → push → open PR.
3. Wait for **CI green** on GitHub — PR **auto-merges** (see setup below).
4. Pull `main` and start the next epic.

## Batch mode — 3 epics, one paste (minimal Manager)

Use when epics are **dependent in a chain** (e.g. 10 → 11 → 12) and you do not want to copy-paste per epic.

| File | Use |
|------|-----|
| [batch_10_11_12_pipeline.md](./batch_10_11_12_pipeline.md) | **One paste** → agent runs Phases 1–3 → **3 PRs** (stacked branches) |

**Your job:** paste once, skim **one** combined report at the end. Enable auto-merge on each PR (agent can run `gh pr merge --auto --merge`). Merge order follows dependency (PR #10 before #11 before #12).

**Agent rules:** do not stop for Manager approval between phases unless blocked. Still **one PR per epic** — never one mega-PR.

**Not for:** unrelated epics in parallel (use separate worktrees + separate prompts instead).

## One-time auto-merge setup (do this once on GitHub)

1. **Enable auto-merge on the repo**  
   https://github.com/LalithShankar/forensic-evidence-fusion/settings  
   → General → Pull Requests → check **Allow auto-merge** → Save.

2. **Required CI checks on `main`** (Settings → Branches → `main` rule)  
   Require status checks: `backend`, `frontend`, `secret-scan`.

3. **Solo fast track — approvals** (pick one)  
   - **Easiest:** set required approvals to **0** on `main`, or  
   - Keep 1 approval → click **Approve** on your own PR, then auto-merge runs.

4. **Each PR** — agent or you runs after CI starts:
   ```bash
   gh pr merge --auto --merge
   ```
   Or on GitHub: PR page → **Enable auto-merge** → Merge commit.

After setup you only **start** each epic; merge happens when CI passes.

## Your job (Manager)

- Skim the agent report (2 min), not every line of diff.
- Merge when CI is green.
- Do not delete local branches unless you choose to.

## Agent must still do

- All acceptance criteria + tests
- `pytest` / `npm test` / lint before push
- One PR per epic to `main`
- Brief report at end (Done / Changed / AC met)

## Optional (only when needed)

| Situation | Do this |
|-----------|---------|
| CI red | Fix in same branch or ask agent to fix wiring only |
| High-risk epic (auth, AI, deploy) | Skim diff or run app once locally |
| Parallel epics | Separate branch per epic; see `batch_plan.md` |

## Not required in fast track

- Cloud Orchestrator (`&`)
- Separate Reviewer / QA / Integration chats
- STATUS.md update every epic (update on merge milestones if you want)
- Linear updates every story (batch when convenient)
