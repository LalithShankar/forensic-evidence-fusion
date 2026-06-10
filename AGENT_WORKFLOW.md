# Agent Workflow — Epic-Driven Agent Pipeline (EDAP)

## Goal
Build this project epic by epic using AI agents, with a human review gate at
every step. The human is the Manager. Agents do the building; nothing merges
without human sign-off.

## Core rule
- ONE Builder agent owns ONE epic at a time.
- The "4 agents" are 4 SEQUENTIAL ROLES applied to that single epic:
  Build -> Review -> Integration -> QA.
- Parallelism happens ACROSS independent epics, never inside one epic.
- A single complex epic may use /multitask subagents for INDEPENDENT tasks,
  but still produces ONE PR reviewed as a unit.

## Roles
| Role          | Mode       | Job                                                  | Edits code?  |
|---------------|------------|------------------------------------------------------|--------------|
| Manager (you) | —          | Plan, assign, review diffs, approve merges           | No (gate)    |
| Planner       | Plan / Ask | Read PROJECT_PLAN.md, produce epics + evaluation     | No           |
| Builder       | Agent      | Implement one epic, open PR, write report            | Yes          |
| Reviewer      | Ask/Agent  | Check code vs acceptance criteria, comment           | No (report)  |
| Integration   | Agent      | Wiring, config, CI, merge conflicts only             | Yes (limited)|
| QA            | Agent      | Run tests + edge cases, pass/fail per criterion      | No (report)  |

## Pipeline per epic
1. Builder implements the epic on branch `epic-<n>-<slug>` -> opens PR -> writes report.
2. Manager reviews the diff (accept / change / add).
3. Builder fine-tunes from feedback.
4. Integration agent: conflicts with main, wiring, CI status. Fixes integration only.
5. QA agent: runs tests, verifies every acceptance criterion, reports pass/fail.
6. Manager final sign-off -> merge.
7. Next epic inherits the clean, merged codebase.

## Parallel vs sequential
- Independent epics (no shared files/contracts) -> run Builders in PARALLEL,
  each in its own worktree (`/worktree`) or cloud agent (own PR).
- Dependent epics -> run in the NEXT batch after the dependency merges.
- Batch size: start with 2-3 parallel epics, scale up only once stable.

## Local vs Cloud
- Local / worktree: fast dev loop, you watch live. Good for first epics.
- Cloud agent: long jobs, fire-and-forget, opens its own PR; monitor at
  cursor.com/agents. Good once prompts + rules are proven.

## Human review loop (non-negotiable)
- Keep epics SMALL so diffs are reviewable.
- Never trust "done" — require QA pass against acceptance criteria.
- Run the app / tests yourself at each gate.
- Merge promptly so branches don't drift from main.

## Agent Isolation Guardrails (one agent must not affect another)
- **One worktree/branch per agent.** Each Builder works in its own `/worktree` (or cloud agent) on its own `epic-<n>-<slug>` branch. No two agents share a working directory.
- **No shared files in a parallel batch.** Two epics run in the same batch ONLY if they share no files and no API contracts (see `01_backlog/batch_plan.md`). If a Builder must touch shared code, STOP and report — do not edit across the boundary.
- **Contracts are frozen within a batch.** A parallel agent may not change an interface another parallel agent depends on. Contract changes wait for the next batch.
- **No cross-talk through main.** Agents branch from the latest merged main; they do not pull each other's in-flight branches. Integration happens only after merge, via the Integration agent.
- **Scope-limited roles.** Builder = assigned epic only; Reviewer = comments only; Integration = wiring/CI/conflicts only; QA = tests only. No role edits another epic's files.
- **Serialize on conflict.** If isolation cannot be guaranteed, treat the epics as dependent and run them sequentially.

## Definition of Done (per epic)
- All acceptance criteria pass (QA report).
- CI green on the PR.
- No unresolved conflicts with main.
- STATUS.md updated.
- Manager approved the merge.

## Sprint & release gates (Manager-set)
- Every sprint: feature usable in the UI (where applicable) + test coverage in the sprint DoD (`07_execution/test_and_quality_strategy.md`).
- Every release (R1–R4): a per-release integration test pass over that release's chain.
- Project completion: a final full integration + regression pass across all releases (`07_execution/release_plan.md`).
