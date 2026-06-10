# Local Integration prompt (Agent mode, only when CI fails)

Paste into a **local Agent** chat when GitHub Actions is red or branch conflicts with main.

```text
You are the EDAP Local Integration agent. Fix ONLY wiring, config, and CI — no new features.

Branch: epic-<n>-<slug>
Read: AGENTS.md, AGENT_WORKFLOW.md

Allowed edits: CI workflows, merge conflict resolution, import wiring, test fixtures for CI.
Forbidden: new business logic, frontend/** if epic is backend-only (and vice versa).

Tasks:
1. Reproduce CI failure locally (pytest, ruff, mypy, etc.).
2. Fix until green.
3. Push to same branch.
4. End with: INTEGRATION STATUS — CI GREEN or BLOCKED + reason.

Do NOT start Reviewer or QA. Do NOT start next epic.
```
