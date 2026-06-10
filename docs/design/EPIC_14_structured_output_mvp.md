# Epic 14 — Structured Output MVP

## Scope
Link parser structured outputs to `StructuredDataset` DB records with metadata and safe preview API/UI. No canonical event mapping (Epic 15).

## Record fields
- `dataset_type`: derived from parser `format` (csv, json, pdf)
- `row_count`: from structured JSON `row_count` when present; 1 for single JSON objects
- `schema_version`: `1.0` for MVP
- `confidence`: artifact `classification_confidence` or default `0.75`
- `status`: `generated` on successful storage; `failed` when storage or parse metadata fails

## Pipeline hook
After `structured_generated` stage writes storage, create/update `StructuredDataset` linked to `transformation_id`.

## Preview API
- List datasets per artifact (viewer+)
- Paginated/safe preview: first 50 rows for CSV; truncated JSON string (max 50k chars)

## Out of scope
- Canonical normalization, editing structured data, full dataset download UI
