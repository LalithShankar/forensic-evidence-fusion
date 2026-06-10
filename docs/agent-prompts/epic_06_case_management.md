# Epic 6 — Case Management (reference — merged PR #10)

Paste into **Agent mode** only if replaying or auditing. Epic 6 is already on `main`.

```text
Follow @docs/agent-prompts/FAST_TRACK.md

Fast Track — Epic 6 ONLY. One session: build → test → push → PR.

Read:
@PROJECT_PLAN.md
@AGENTS.md
@user_story/evidence-fusion-post-edap-full/02_epics/EPIC_06_case_management.md
@docs/design/EPIC_05_design.md

Branch: epic-6-case-management
Linear: LAL-10, LAL-40, LAL-41
Repo: LalithShankar/forensic-evidence-fusion

Implement Stories 6.1–6.2: case CRUD, case_memberships, replace check_case_access stub,
Cases + CaseDetail UI, tests for all ACs.

Before push: pytest, ruff, black; npm lint, test, build.
Push, gh pr create, gh pr merge --auto --merge.
End with AGENTS.md report.
```
