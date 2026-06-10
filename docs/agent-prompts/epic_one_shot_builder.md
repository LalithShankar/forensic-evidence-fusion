# One-shot epic builder (Fast Track)

Paste into **Agent mode** in `forensic_v2`. Replace `<…>` placeholders.

```text
Fast Track — Epic <N> ONLY. One session: build → test → push → PR. Do not start the next epic.

Read:
@docs/agent-prompts/FAST_TRACK.md
@PROJECT_PLAN.md
@AGENTS.md
@user_story/evidence-fusion-post-edap-full/02_epics/EPIC_<NN>_<slug>.md

Branch: epic-<n>-<slug> (check out or confirm)
Linear: LAL-<epic>, stories LAL-<story>, …
Repo: LalithShankar/forensic-evidence-fusion

Implement all stories in the epic file. Match existing code style.
Scope: <backend/** | frontend/** | both — from epic file>
Out of scope: anything in the next epic.

Before push, run and fix until green:
- backend: .venv/bin/pytest && .venv/bin/ruff check . && .venv/bin/black --check .
- frontend (if touched): npm run lint && npm run test && npm run build

Then: commit, git push origin epic-<n>-<slug>, gh pr create --base main --head epic-<n>-<slug>

Enable auto-merge (Manager uses auto-merge when CI green):
gh pr merge --auto --merge

End with short report: Done | Changed | each AC met/not met | CI-ready yes/no | PR URL.
Do NOT manually merge without --auto unless CI failed and was fixed.
```

## Git commands (you or agent, start of epic)

```bash
cd /Users/lalithshankar/Documents/projects/forensic_v2
git checkout main && git pull origin main
git checkout -b epic-<n>-<slug>
git push -u origin epic-<n>-<slug>
```

## After CI green (you)

```bash
gh pr merge --merge    # or merge on GitHub
git checkout main && git pull origin main
```
