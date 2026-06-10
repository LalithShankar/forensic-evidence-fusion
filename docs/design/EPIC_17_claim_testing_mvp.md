# Epic 17 — Claim testing MVP (deterministic)

## Scope

Epic 17 delivers narrative claim entry, heuristic parsing, and **deterministic** evidence matching against timeline events. No LLM participates in verdict selection.

## Verdict labels

From `claim_schema.md`:

- `supported`
- `partially_supported`
- `unresolved`
- `weakly_contradicted`
- `strongly_contradicted`
- `not_testable`

## Parsing (non-LLM)

`claim_parse_service.py` extracts:

- ISO-like dates from `claimed_time_text` or claim body
- Capitalized name tokens and explicit `claimed_people`
- `parse_confidence` from how many structured signals were found

## Resolution (deterministic)

`claim_resolution_service.py` loads case events via `event_service.list_timeline_events` and scores each event:

1. **Keyword overlap** between claim text and event title/description/payload
2. **People match** against payload/title text
3. **Time proximity** when `claimed_time_normalized` is present (±24h support; ≥2–7d contradiction)

Threshold mapping:

| Condition | Label |
|-----------|-------|
| contradiction ≥ 0.7 | strongly_contradicted |
| contradiction ≥ 0.4 and support < 0.5 | weakly_contradicted |
| support ≥ 0.7 and contradiction < 0.3 | supported |
| support ≥ 0.5 and contradiction < 0.4 | partially_supported |
| no matches | unresolved (+ reason) |
| low parse confidence, no time | not_testable |

Re-resolve is idempotent: updates the existing `claim_resolutions` row.

## Out of scope

- LLM parsing or verdict explanation
- Legal conclusions or auto-approval
- Azure Search / assistant integration (Epics 18–19)
