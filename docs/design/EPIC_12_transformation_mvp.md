# Epic 12 — Transformation Pipeline MVP (design)

## Scope

Synchronous MVP pipeline from `ready_for_transformation` artifact to readable/structured
outputs. No Azure worker queue in this epic; `POST /transformations/start` triggers
inline execution.

## State machine

Stages (in order):

1. `preserved` — raw bytes already stored
2. `classified` — provenance confirmed for parser routing
3. `preprocessed` — format validated, raw bytes loaded
4. `extracted` — parser produced intermediate representation
5. `readable_generated` — human-readable output written (`readable/` namespace)
6. `structured_generated` — machine-readable output written (`structured/` namespace)

Terminal states:

- `completed` — all stages succeeded
- `blocked` — stage failure; `failure_notes` + `limitation_notes` stored on record

## Storage

Outputs use existing `build_object_key()` conventions:

- Readable: `readable/{case_id}/{artifact_id}/{filename}`
- Structured: `structured/{case_id}/{artifact_id}/{filename}`

`StorageBackend.write_output()` added for both local and Azure backends.

## Parsers (MVP)

| Format | Parser | Readable output | Structured output |
|--------|--------|-----------------|-------------------|
| CSV | `csv_parser` | row/column summary | JSON rows + metadata |
| JSON | `json_parser` | pretty-printed JSON | normalized JSON object |
| PDF | `pdf_parser` | text preview (literal-string extraction) | metadata + text excerpt |

## Idempotency

`TransformationRecord.idempotency_key` = `{artifact_id}:{content_hash}`. Re-running
start with the same key returns the existing record unless prior run failed.

## API

- `POST /cases/{case_id}/artifacts/{artifact_id}/transformations/start`
- `GET /cases/{case_id}/artifacts/{artifact_id}/transformations/latest`

## Out of scope

- OCR, WhatsApp/Gmail parsers, async workers, retry queues
