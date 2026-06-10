# Project Plan

> This is the single source of truth every agent reads first. Keep it filled and current.
> Decided: **Chakra UI** and **Azure Container Apps** (current direction — may change based on the deployment strategy we finalize). Auth approach (local-first vs Entra) is still the Manager's open call.
> Tooling decisions are tracked in `06_validation/DECISIONS_LOG.md`.

## 1. Overview
- Product name: Forensic Evidence Fusion Platform
- One-line goal: A secure web platform that collects, preserves, transforms, indexes, and analyzes digital evidence from Apple, Google, third-party apps, screenshots, exports, archives, and narrative statements — with provenance and human review at every step.
- Target users: analysts/reviewers first; later case managers, investigators, and legal reviewers.

## 2. Tech stack
- Frontend: React + TypeScript + Vite + **Chakra UI** + TanStack Query + React Router
- Backend: Python + FastAPI + Pydantic + SQLAlchemy + Alembic
- Database: PostgreSQL (Azure Database for PostgreSQL when deployed)
- File storage: local `/data` or Azurite locally; Azure Blob Storage when deployed
- AI / search: Azure OpenAI + Azure AI Search
- Infra / hosting: **Azure Container Apps** (backend + workers), Static Web Apps/App Service (frontend), Azure Key Vault, Application Insights
- Testing framework: Pytest (backend), Vitest + React Testing Library (frontend)

> Chakra UI and Azure Container Apps are the current decisions; the hosting target in particular may change once the deployment strategy is finalized. Auth approach (local-first vs Entra) remains open.

## 3. Non-negotiable constraints
- Security / compliance: login required; no anonymous evidence intake; case-level access; uploader identity captured; audit trail for evidence/claim/report actions; never commit secrets; deployed secrets only from Azure Key Vault via Managed Identity.
- Evidence integrity: preserve raw evidence before any parsing; never overwrite originals; every derived record must trace back to its raw artifact; honest limitation logging.
- AI grounding: AI answers only from transformed, source-linked, indexed evidence; cite sources; surface uncertainty and missing data; no legal conclusions.
- Performance: large-file uploads must not block the API; long-running transformation runs execute on workers, not request threads.
- Coding standards / style: see section 7.
- Must-use: PostgreSQL as primary relational store; APP_ENV local/deployed split. Must-avoid: committing `.env` or secrets; auto-merge; agents editing out-of-scope files.

## 4. Epics (high level)
22 epics; full detail in `02_epics/` and `01_backlog/EDAP_BACKLOG.md`.

| ID | Epic name | Outcome (what user can do) | Depends on |
|----|-----------|----------------------------|------------|
| 1  | Repo, Rules, Local Dev Foundation | Clean repo + env contract + CI agents can build on | — |
| 2  | Core Backend App Skeleton | Running FastAPI with health, config, logging | 1 |
| 3  | Core Frontend App Shell | Running React shell with routing + API client | 1 |
| 4  | Database Foundation | Postgres + migrations + base models + audit table | 2 |
| 5  | Auth and User Access MVP | Log in; user/role/case-access shape | 2, 4 |
| 6  | Case Management | Create/list/view/update cases | 4, 5 |
| 7  | Evidence Upload and Raw Preservation | Upload + preserve raw artifact with hash | 6 |
| 8  | Blob Storage Integration | Local/Azure storage swap by APP_ENV | 7 |
| 9  | Artifact Manifest and Metadata | Source hierarchy, parser class, provenance | 7, 8 |
| 10 | Bulk Upload and Categorization | Mixed/ZIP upload + suggested categories | 9 |
| 11 | Review Queue | Resolve low-confidence/blocked artifacts | 10 |
| 12 | Transformation Pipeline MVP | State machine + basic parsers on workers | 9, 11 |
| 13 | Readable Preview Layer | Human-readable previews | 12 |
| 14 | Structured Dataset Generation | Structured JSON/CSV outputs | 12 |
| 15 | Canonical Evidence Schema Integration | Map outputs to canonical events/entities | 14 |
| 16 | Timeline and Event Workspace | Chronological event review | 15 |
| 17 | Narrative and Claim Testing | Enter + resolve claims vs evidence | 15, 16 |
| 18 | Azure AI Search Indexing | Source-linked chunks indexed | 13, 15 |
| 19 | Evidence-grounded AI Assistant | Ask grounded questions with citations | 18 |
| 20 | Reporting and Audit Trail | Reviewable reports + audit views | 15, 17 |
| 21 | Deployment Foundation | Deploy to Azure with Key Vault | 2, 3, 4, 8 |
| 22 | Observability and Operational Hardening | Logs, failures, status visibility | 12, 21 |

## 5. Out of scope (for now)
- Direct automatic collection from personal provider accounts
- Encrypted iPhone backup deep parsing / backup cracking
- Fully automated legal conclusions
- Production-grade enterprise multi-tenancy
- Mobile app
- Payment processing
- Advanced graph analytics beyond basic event/entity linking

## 6. Glossary / domain terms
- Artifact: one raw uploaded/registered evidence item.
- Raw preservation: storing the original file unchanged before any processing.
- Readable view: human-inspectable rendering of an artifact (HTML/text/inventory).
- Structured dataset: machine-readable output (JSON/CSV) derived from an artifact.
- Canonical schema: source-independent model (events/entities/claims) all evidence maps into.
- Provenance pointer: link from a derived record back to its source artifact/transformation/chunk.
- Claim: a narrative statement that can be tested against evidence.
- Grounding: AI answering only from retrieved, source-linked evidence.

## 7. Coding standards / style
- Python: ruff (lint) + black (format) + mypy (types where practical); FastAPI routers thin, logic in services.
- TypeScript: ESLint + Prettier; functional components; TanStack Query for server state.
- Tests: every acceptance criterion has a test; run before claiming done.
- Branches: `epic-<n>-<slug>`; one PR per epic; no auto-merge; human approves all merges.
- Environment: honor `APP_ENV` local/deployed; never commit secrets; `.env.example` lists variable names only.
