# Epic 15 — Canonical Mapping MVP

## Scope
Map structured datasets to `EvidenceEvent` records with provenance. MVP subset only — no claim reasoning, dedup, or RAG.

## Models (MVP)
- `Entity` — generic entity row with `entity_type` (person, account, device, app, location)
- `EvidenceEvent` — normalized observations with provenance + confidence
- `Claim`, `ClaimResolution`, `AnalystNote`, `Report` — stub tables for schema alignment

## Normalization trigger
Pipeline calls `normalize_structured_dataset` automatically after `StructuredDataset` registration. Manual re-run via `POST /cases/{case_id}/artifacts/{artifact_id}/normalize`.

## Row heuristics
- **Message-like**: keys matching `message`, `body`, `text`, `content`, `chat` → `message_sent` event
- **Transaction-like**: keys matching `amount`, `transaction`, `payment`, `debit`, `credit` → `transaction_observed` event
- **Weak timestamp**: unparseable or missing date text stored in `original_timestamp_text` with confidence ≤ 0.5

## Out of scope
Entity resolution, deduplication, claim testing, AI retrieval.
