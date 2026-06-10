# Epics 18–19 — RAG MVP (indexing + grounded assistant)

## Scope

Epic 18 prepares source-linked `SearchChunk` records and pushes them through a pluggable `SearchBackend`.
Epic 19 adds a case-scoped assistant that retrieves chunks, refuses when evidence is insufficient, and logs Q&A for audit.

## Backend swap (like storage)

| APP_ENV | Search | LLM |
|---------|--------|-----|
| `local` / CI | `InMemorySearchBackend` (keyword overlap) | `MockLLMBackend` (template from chunks) |
| `deployed` | `AzureSearchBackend` when search env vars set | `AzureOpenAIBackend` when OpenAI env vars set |

If deployed vars are missing, factories fall back to in-memory/mock (never call Azure in CI).

## Chunk model

- Readable view text split ~800 chars with 100 overlap
- Enriched with `artifact.source_group`, `provenance_pointer`
- Optional event summary chunks with `event_type` / `event_id` filter metadata

## Security

- All search queries **must** filter by `case_id`
- Assistant verifies cited chunk IDs exist in retrieval set
- Case access enforced via `check_case_access`

## Out of scope

- Production embedding/ranking tuning
- Legal conclusions
- Epic 20+ features
