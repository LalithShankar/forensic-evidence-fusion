# Project Status

_Last updated by: EDAP pipeline (Epic 2 Builder/QA) on 2026-06-10_

## Batch plan
| Batch | Epics          | State        |
|-------|----------------|--------------|
| 1     | Epic 1, Epic 2 | in progress  |
| 2     | Epic 3         | blocked (needs 1,2) |

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

## Epic 2 tracker (LAL-6)
Branch: `epic-2-core-backend-app-skeleton` · PR: https://github.com/LalithShankar/forensic-evidence-fusion/compare/main...epic-2-core-backend-app-skeleton

| Story | Linear | Requirement / criterion | Status | PR | QA | Notes |
|-------|--------|-------------------------|--------|----|----|-------|
| 2.1 | LAL-30 | /health returns status ok | ✅ | open | pass | `api/router.py` + TestClient |
| 2.1 | LAL-30 | APP_ENV visible in safe non-secret response | ✅ | open | pass | no secret_key/database_url in payload |
| 2.1 | LAL-30 | Health test passes in pytest | ✅ | open | pass | test_health.py |
| 2.1 | LAL-30 | CORS allows local frontend origin | ✅ | open | pass | config + middleware + test_health.py |
| 2.2 | LAL-31 | pytest runs from documented command | ✅ | open | pass | README + pyproject.toml dev extras |
| 2.2 | LAL-31 | ruff/black/mypy report style errors | ✅ | open | pass | CI + local green |
| 2.2 | LAL-31 | Deterministic dependency install | ✅ | open | pass | pip install -e ".[dev]" |
| 2.3 | LAL-32 | Structured logs with correlation/request ID | ✅ | open | pass | JSON formatter + X-Request-ID middleware |
| 2.3 | LAL-32 | user/case/artifact IDs attached when set | ✅ | open | pass | bind_log_context + formatter test |
| 2.3 | LAL-32 | Secrets never logged (redaction test) | ✅ | open | pass | test_logging_safety.py |

Status key: ❌ not started · ⏳ in progress · ✅ done

## Change log (per merged epic)
| Date | Epic | PR | Summary of changes | Conflicts resolved |
|------|------|----|--------------------|--------------------|
| 2026-06-10 | 1 | merged | Repo scaffold, env contract, CI foundation | none |

## Open questions for the Manager
- Apply GitHub branch protection on `main` per `docs/branch-protection.md`.
- Epic 2 PR open; awaiting human merge approval.
