# Project Status

_Last updated by: EDAP pipeline (Epic 3 Builder/Reviewer/Integration/QA) on 2026-06-10_

## Batch plan
| Batch | Epics          | State        |
|-------|----------------|--------------|
| 1     | Epic 1, Epic 2 | in progress  |
| 2     | Epic 3         | in progress  |

## Epic 1 tracker (LAL-5)
Branch: `epic-1-repo-rules-and-local-dev-foundation` · Merged to main

| Story | Linear | Requirement / criterion | Status | PR | QA | Notes |
|-------|--------|-------------------------|--------|----|----|-------|
| 1.1 | LAL-27 | Repo folders exist | ✅ | merged | pass | backend, frontend, docs, infra, tests, scripts |
| 1.1 | LAL-27 | Root agent docs available | ✅ | merged | pass | PROJECT_PLAN, AGENTS, AGENT_WORKFLOW, EPIC_*, STATUS |
| 1.1 | LAL-27 | README setup instructions | ✅ | merged | pass | local startup + conventions |
| 1.2 | LAL-28 | APP_ENV=local loads .env | ✅ | merged | pass | LocalSettings + tests |
| 1.2 | LAL-28 | APP_ENV=deployed uses Key Vault + MI | ✅ | merged | pass | DeployedSettings contract + tests |
| 1.2 | LAL-28 | .env ignored; .env.example tracked | ✅ | merged | pass | .gitignore verified |
| 1.3 | LAL-29 | CI: backend lint/type-check/pytest | ✅ | merged | pass | ruff, black, mypy, pytest |
| 1.3 | LAL-29 | CI: frontend lint/type-check/tests | ✅ | merged | pass | eslint, tsc, vitest |
| 1.3 | LAL-29 | CI: secret scan fails on .env/secrets | ✅ | merged | pass | tracked-.env check + gitleaks job |
| 1.3 | LAL-29 | main branch protection (PR + checks + approval) | ⏳ | merged | partial | documented in docs/branch-protection.md; GitHub settings pending |

## Epic 3 tracker (LAL-7)
Branch: `epic-3-core-frontend-app-shell` · PR: pending

| Story | Linear | Requirement / criterion | Status | PR | QA | Notes |
|-------|--------|-------------------------|--------|----|----|-------|
| 3.1 | LAL-33 | Basic landing/dashboard page loads | ✅ | open | pass | `DashboardPage` + `AppLayout` |
| 3.1 | LAL-33 | Base routes render without full page reload | ✅ | open | pass | React Router `BrowserRouter` + client nav tests |
| 3.1 | LAL-33 | Smoke test renders app successfully | ✅ | open | pass | `App.test.tsx` |
| 3.2 | LAL-34 | VITE_APP_ENV=local reads VITE_API_BASE_URL from .env | ✅ | open | pass | `config.test.ts` with `vi.stubEnv` |
| 3.2 | LAL-34 | API client health call targets configured backend URL | ✅ | open | pass | `lib/apiClient.ts` + tests |
| 3.2 | LAL-34 | Frontend .env not tracked in Git | ✅ | open | pass | `.gitignore` + `git check-ignore` |

Status key: ❌ not started · ⏳ in progress · ✅ done

## Change log (per merged epic)
| Date | Epic | PR | Summary of changes | Conflicts resolved |
|------|------|----|--------------------|--------------------|
| 2026-06-10 | 1 | merged | Repo scaffold, env contract, CI foundation | none |

## Open questions for the Manager
- Apply GitHub branch protection on `main` per `docs/branch-protection.md`.
- Epic 3 PR ready for human merge review.
