# Agent prompts

## Fast Track (default — solo Manager)

| File | Use |
|------|-----|
| [FAST_TRACK.md](./FAST_TRACK.md) | Process: one agent, one PR, auto-merge on CI green |
| [epic_one_shot_builder.md](./epic_one_shot_builder.md) | Generic template (fill placeholders) |
| `epic_<NN>_<slug>.md` | **Ready-to-paste** prompt per epic (preferred) |

## Per-epic prompts (copy → Agent mode)

| Epic | File | Status |
|------|------|--------|
| 6 | [epic_06_case_management.md](./epic_06_case_management.md) | merged (reference) |
| 7 | [epic_07_evidence_upload_and_raw_preservation.md](./epic_07_evidence_upload_and_raw_preservation.md) | merged (reference) |
| 8 | [epic_08_blob_storage_integration.md](./epic_08_blob_storage_integration.md) | merged (reference) |
| 9 | [epic_09_artifact_manifest_and_metadata.md](./epic_09_artifact_manifest_and_metadata.md) | **next** |

## Legacy multi-role EDAP (optional)

| File | Role |
|------|------|
| [HYBRID_EDAP.md](./HYBRID_EDAP.md) | Cloud orchestrator + local workers |
| [local_builder.md](./local_builder.md) | Generic builder template |
| [local_reviewer.md](./local_reviewer.md) | Reviewer (Ask mode) |
| [local_integration.md](./local_integration.md) | CI/wiring fixes |
| [local_qa.md](./local_qa.md) | QA pass/fail report |
| [cloud_orchestrator.md](./cloud_orchestrator.md) | Cloud dispatch template |
| [epic_04_dispatch.md](./epic_04_dispatch.md) | Epic 4 filled example |

## Paste pattern (every epic)

```text
Follow @docs/agent-prompts/FAST_TRACK.md

@docs/agent-prompts/epic_09_artifact_manifest_and_metadata.md
```

Replace the epic file for each new epic.
