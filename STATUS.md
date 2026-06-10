# Project Status

_Last updated by: Agent on 2026-06-11 (Epics 10–12 in review)_

## Batch plan
| Batch | Epics          | State        |
|-------|----------------|--------------|
| 1     | Epic 1         | merged       |
| 2     | Epic 2, Epic 3 | merged       |
| 3     | Epic 4         | merged       |
| 4     | Epic 5         | merged       |
| 5     | Epic 6         | merged       |
| 6     | Epic 7         | merged (PR #11) |
| 7     | Epic 8         | merged (PR #12) |
| 8     | Epic 9         | merged          |
| 9     | Epic 10, 11, 12 | in review (stacked PRs) |

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
Branch: `epic-2-core-backend-app-skeleton` · Merged to main (PR #4)

| Story | Linear | Requirement / criterion | Status | PR | QA | Notes |
|-------|--------|-------------------------|--------|----|----|-------|
| 2.1 | LAL-30 | /health returns status ok | ✅ | merged | pass | `api/router.py` + TestClient |
| 2.1 | LAL-30 | APP_ENV visible in safe non-secret response | ✅ | merged | pass | no secret_key/database_url in payload |
| 2.1 | LAL-30 | Health test passes in pytest | ✅ | merged | pass | test_health.py |
| 2.1 | LAL-30 | CORS allows local frontend origin | ✅ | merged | pass | config + middleware + test_health.py |
| 2.2 | LAL-31 | pytest runs from documented command | ✅ | merged | pass | README + pyproject.toml dev extras |
| 2.2 | LAL-31 | ruff/black/mypy report style errors | ✅ | merged | pass | CI + local green |
| 2.2 | LAL-31 | Deterministic dependency install | ✅ | merged | pass | pip install -e ".[dev]" |
| 2.3 | LAL-32 | Structured logs with correlation/request ID | ✅ | merged | pass | JSON formatter + X-Request-ID middleware |
| 2.3 | LAL-32 | user/case/artifact IDs attached when set | ✅ | merged | pass | bind_log_context + formatter test |
| 2.3 | LAL-32 | Secrets never logged (redaction test) | ✅ | merged | pass | test_logging_safety.py |

## Epic 3 tracker (LAL-7)
Branch: `epic-3-core-frontend-app-shell` · Merged to main (PR #5)

| Story | Linear | Requirement / criterion | Status | PR | QA | Notes |
|-------|--------|-------------------------|--------|----|----|-------|
| 3.1 | LAL-33 | Basic landing/dashboard page loads | ✅ | merged | pass | `DashboardPage` + `AppLayout` |
| 3.1 | LAL-33 | Base routes render without full page reload | ✅ | merged | pass | React Router `BrowserRouter` + client nav tests |
| 3.1 | LAL-33 | Smoke test renders app successfully | ✅ | merged | pass | `App.test.tsx` |
| 3.2 | LAL-34 | VITE_APP_ENV=local reads VITE_API_BASE_URL from .env | ✅ | merged | pass | `config.test.ts` with `vi.stubEnv` |
| 3.2 | LAL-34 | API client health call targets configured backend URL | ✅ | merged | pass | `lib/apiClient.ts` + tests |
| 3.2 | LAL-34 | Frontend .env not tracked in Git | ✅ | merged | pass | `.gitignore` + `git check-ignore` |

## Epic 4 tracker (LAL-8)
Branch: `epic-4-database-foundation` · Merged to main (PR #6)

| Story | Linear | Requirement / criterion | Status | PR | QA | Notes |
|-------|--------|-------------------------|--------|----|----|-------|
| 4.1 | LAL-35 | DATABASE_URL init on backend start | ✅ | merged | pass | `app/db/session.py` + lifespan in `main.py` |
| 4.1 | LAL-35 | Alembic migrations create/update schema | ✅ | merged | pass | `alembic/` + `001_initial_schema` migration |
| 4.1 | LAL-35 | Tests use SQLite, no production credentials | ✅ | merged | pass | `tests/conftest.py` + `test_db_session.py` |
| 4.2 | LAL-36 | users/cases/artifacts placeholder tables | ✅ | merged | pass | Alembic migration + ORM models |
| 4.2 | LAL-36 | SQLAlchemy metadata loads without circular imports | ✅ | merged | pass | `app/models/__init__.py` + test_models.py |
| 4.2 | LAL-36 | Models have required IDs and timestamps | ✅ | merged | pass | UUIDPrimaryKeyMixin + TimestampMixin |
| 4.3 | LAL-37 | audit_log table with required columns | ✅ | merged | pass | `app/models/audit.py` + migration |
| 4.3 | LAL-37 | audit helper writes acting user + target object | ✅ | merged | pass | `app/services/audit_service.py` |
| 4.3 | LAL-37 | Simulated audit creates exactly one row | ✅ | merged | pass | `tests/test_audit_service.py` |

Status key: ❌ not started · ⏳ in progress · ✅ done

## Change log (per merged epic)
| Date | Epic | PR | Summary of changes | Conflicts resolved |
|------|------|----|--------------------|--------------------|
| 2026-06-10 | 1 | merged | Repo scaffold, env contract, CI foundation | none |
| 2026-06-10 | 2 | #4 | FastAPI shell, structured logging, backend tests | STATUS.md |
| 2026-06-10 | 3 | #5 | React shell, routing, API client | STATUS.md |
| 2026-06-10 | 4 | #6 | SQLAlchemy session, Alembic migrations, placeholder models, audit_log | none |
| 2026-06-10 | 5 | #9 | Local auth MVP with JWT login and protected routes | none |
| 2026-06-10 | 6 | #10 | Case CRUD APIs, case_memberships migration, membership-based access, case list/detail UI | none |
| 2026-06-10 | 7 | #11 | Evidence upload API, local raw preservation + SHA-256, CaseUpload UI | none |
| 2026-06-10 | 8 | #12 | StorageBackend abstraction, Azure/local swap, raw/readable/structured paths | none |

## Epic 10 tracker (LAL-14)
Branch: `epic-10-bulk-upload-and-categorization` · In review

| Story | Linear | Requirement / criterion | Status | PR | QA | Notes |
|-------|--------|-------------------------|--------|----|----|-------|
| 10.1 | LAL-48 | Multiple files → each gets own Artifact | ✅ | pending | pass | `bulk_upload_service` + bulk-upload API |
| 10.1 | LAL-48 | Partial failure preserves successes | ✅ | pending | pass | per-file results in response |
| 10.1 | LAL-48 | Batch grouping visible in UI | ✅ | pending | pass | `upload_batch_id` + `BulkUpload.tsx` |
| 10.2 | LAL-49 | WhatsApp filename → ThirdParty/WhatsApp + confidence | ✅ | pending | pass | `classification_service` rules |
| 10.2 | LAL-49 | Takeout ZIP → Google/Takeout + confidence | ✅ | pending | pass | filename rule |
| 10.2 | LAL-49 | Low confidence → needs review | ✅ | pending | pass | `ArtifactStatus.needs_review` |

## Epic 11 tracker (LAL-15)
Branch: `epic-11-review-queue` · In review (stacked on Epic 10)

| Story | Linear | Requirement / criterion | Status | PR | QA | Notes |
|-------|--------|-------------------------|--------|----|----|-------|
| 11.1 | LAL-50 | Low-confidence items in queue with suggestion + reason | ✅ | pending | pass | `GET /review-queue` |
| 11.1 | LAL-50 | Blocked artifacts show blocker notes | ✅ | pending | pass | `blocker_notes` field |
| 11.1 | LAL-50 | Empty state when nothing needs review | ✅ | pending | pass | `ReviewQueue.tsx` |
| 11.2 | LAL-51 | Correct source_group/family/type | ✅ | pending | pass | PATCH review-queue |
| 11.2 | LAL-51 | Approve → ready_for_transformation | ✅ | pending | pass | extended `ArtifactStatus` |
| 11.2 | LAL-51 | Preserve-only excludes auto transformation | ✅ | pending | pass | `preserve_only` status |

## Epic 12 tracker (LAL-16)
Branch: `epic-12-transformation-pipeline-mvp` · In review (stacked on Epic 11)

| Story | Linear | Requirement / criterion | Status | PR | QA | Notes |
|-------|--------|-------------------------|--------|----|----|-------|
| 12.1 | LAL-52 | Ready artifact → TransformationRecord created | ✅ | pending | pass | `transformation_pipeline.start` |
| 12.1 | LAL-52 | Stages visible through structured_generated | ✅ | pending | pass | state machine + API response |
| 12.1 | LAL-52 | Stage failure stores failure/limitation notes | ✅ | pending | pass | blocked status + notes |
| 12.2 | LAL-53 | CSV → structured rows + metadata | ✅ | pending | pass | `csv_parser.py` |
| 12.2 | LAL-53 | JSON → readable + structured outputs | ✅ | pending | pass | `json_parser.py` |
| 12.2 | LAL-53 | PDF extractable text → readable preview | ✅ | pending | pass | `pdf_parser.py` (literal extraction MVP) |

## Epic 9 tracker (LAL-13)
Branch: `epic-9-artifact-manifest-and-metadata` · Merged

| Story | Linear | Requirement / criterion | Status | PR | QA | Notes |
|-------|--------|-------------------------|--------|----|----|-------|
| 9.1 | LAL-46 | Upload stores source_group, source_family, artifact_type, collection_method, parser_class | ✅ | merged | pass | multipart form + migration 005 |
| 9.1 | LAL-46 | Omitted metadata → safe defaults (unknown) | ✅ | merged | pass | `resolve_provenance_field` |
| 9.1 | LAL-46 | Artifact detail shows provenance_notes | ✅ | merged | pass | `ArtifactDetailPage` |
| 9.2 | LAL-47 | Manifest lists id, case_id, storage_path, status, hash, metadata | ✅ | merged | pass | `GET /cases/{id}/artifacts/manifest` |
| 9.2 | LAL-47 | Manifest reflects current status/metadata | ✅ | merged | pass | `build_case_manifest` |
| 9.2 | LAL-47 | Tests: required provenance fields never null | ✅ | merged | pass | `test_manifest_service.py` |

## Epic 8 tracker (LAL-12)
Branch: `epic-8-blob-storage-integration` · Merged to main (PR #12)

| Story | Linear | Requirement / criterion | Status | PR | QA | Notes |
|-------|--------|-------------------------|--------|----|----|-------|
| 8.1 | LAL-44 | APP_ENV=local → local filesystem (or Azurite when connection string set) | ✅ | merged | pass | `StorageBackend` + factory |
| 8.1 | LAL-44 | APP_ENV=deployed → Azure Blob backend | ✅ | merged | pass | `AzureBlobStorageBackend` |
| 8.1 | LAL-44 | API/services use abstraction only | ✅ | merged | pass | no direct SDK in routers |
| 8.2 | LAL-45 | Raw artifacts under raw/ namespace | ✅ | merged | pass | `storage_paths.build_object_key` |
| 8.2 | LAL-45 | Readable path helper under readable/ namespace | ✅ | merged | pass | `StorageNamespace.readable` |
| 8.2 | LAL-45 | Structured path helper under structured/ namespace | ✅ | merged | pass | `StorageNamespace.structured` |

## Epic 5 tracker (LAL-9)
Branch: `epic-5-auth-and-user-access-mvp` · Merged to main (PR #9)

| Story | Linear | Requirement / criterion | Status | PR | QA | Notes |
|-------|--------|-------------------------|--------|----|----|-------|
| 5.1 | LAL-38 | Valid login returns JWT session | ✅ | merged | pass | `POST /auth/login` + `auth_service.py` |
| 5.1 | LAL-38 | Invalid credentials denied safely | ✅ | merged | pass | generic 401 message |
| 5.1 | LAL-38 | Unauthenticated protected routes return 401 | ✅ | merged | pass | `/auth/me`, `/auth/protected/ping` |
| 5.2 | LAL-39 | User model has role/status fields | ✅ | merged | pass | `UserRole`, `UserStatus` enums |
| 5.2 | LAL-39 | Protected endpoints resolve current user | ✅ | merged | pass | `get_current_user` dependency |
| 5.2 | LAL-39 | User ID attachable for audit/logging | ✅ | merged | pass | `bind_log_context` + `request.state.user_id` |

## Epic 6 tracker (LAL-10)
Branch: `epic-6-case-management` · Merged to main (PR #10) · QA pass

| Story | Linear | Requirement / criterion | Status | PR | QA | Notes |
|-------|--------|-------------------------|--------|----|----|-------|
| 6.1 | LAL-40 | Authenticated create saves case with created_by + timestamps | ✅ | merged | pass | `POST /cases` + manager membership |
| 6.1 | LAL-40 | Case list shows only accessible cases (membership-based) | ✅ | merged | pass | `list_accessible_cases` + tests |
| 6.1 | LAL-40 | Invalid input returns validation errors (API 422; form shows errors) | ✅ | merged | pass | `test_cases.py` + `Cases.test.tsx` |
| 6.2 | LAL-41 | Detail page shows name, description, scenario type, date range | ✅ | merged | pass | `CaseDetail.tsx` + `GET /cases/{id}` |
| 6.2 | LAL-41 | Save updates allowed fields; updated_at changes; values persist | ✅ | merged | pass | `PATCH /cases/{id}` + audit `case.updated` |
| 6.2 | LAL-41 | Missing/inaccessible case → safe not-found state (no info leak) | ✅ | merged | pass | 404 for missing + no membership |

## Epic 7 tracker (LAL-11)
Branch: `epic-7-evidence-upload-and-raw-preservation` · Merged to main (PR #11) · QA pass

| Story | Linear | Requirement / criterion | Status | PR | QA | Notes |
|-------|--------|-------------------------|--------|----|----|-------|
| 7.1 | LAL-42 | Upload supported file → Artifact record created | ✅ | merged | pass | `POST /cases/{id}/artifacts/upload` |
| 7.1 | LAL-42 | Metadata: filename, size, extension, MIME, uploader, upload time | ✅ | merged | pass | `ArtifactPublic` + tests |
| 7.1 | LAL-42 | Upload failure → no fake completed artifact | ✅ | merged | pass | 400/500; failed status not preserved |
| 7.2 | LAL-43 | Original file stored unchanged on disk | ✅ | merged | pass | `storage_service.preserve_raw` |
| 7.2 | LAL-43 | SHA-256 hash stored when preservation completes | ✅ | merged | pass | `content_hash` on artifact |
| 7.2 | LAL-43 | Preservation failure → status failed/blocked, not completed | ✅ | merged | pass | `test_preservation_failure_marks_artifact_failed` |

## Open questions for the Manager
- Apply GitHub branch protection on `main` per `docs/branch-protection.md`.
