# Epic Evaluation Rubric

Read PROJECT_PLAN.md. For EACH epic, score the four factors below (1-3),
then apply the decision table to assign an agent strategy and batch.

## Scoring factors
| Factor       | 1 (Low)            | 2 (Medium)            | 3 (High)                       |
|--------------|--------------------|-----------------------|--------------------------------|
| Complexity   | <5 files, simple   | several files/modules | many files, new architecture   |
| Dependencies | none               | depends on 1 epic     | depends on multiple epics      |
| Risk         | cosmetic / internal| user-facing feature   | auth, payments, data, security |
| Uncertainty  | clear spec         | some unknowns         | spec vague / research needed   |

## Decision table
- Total 4-6   -> Single Builder, standard pipeline. Parallel-eligible if Dependencies = 1.
- Total 7-9   -> Single Builder, but SPLIT the epic into smaller tasks; Builder may
                 use /multitask for independent tasks. Mandatory Integration + QA.
- Total 10-12 -> Do NOT auto-build. Planner first writes a design doc; Manager
                 reviews design before any Builder starts. High-risk -> human pairing.

## Parallelization
- Two epics may run in parallel ONLY if they share NO files and NO API contracts.
- If unsure, treat as dependent -> sequential.

## Output of evaluation (produce this table)
| Epic | Cmplx | Deps | Risk | Uncert | Total | Strategy            | Batch | Runtime       |
|------|-------|------|------|--------|-------|---------------------|-------|---------------|
| 1    | 2     | 1    | 3    | 1      | 7     | Split + multitask   | 1     | cloud, own PR |
| 2    | 1     | 1    | 1    | 1      | 4     | Single builder      | 1     | worktree      |
| 3    | 2     | 3    | 2    | 2      | 9     | Split, after #1,#2  | 2     | cloud, own PR |

## Batching rule
- Batch = set of epics that can run in parallel safely.
- An epic goes in the EARLIEST batch where all its dependencies are already merged.
