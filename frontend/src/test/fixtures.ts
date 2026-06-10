import type { ArtifactPublic } from "../lib/apiClient";

const DEFAULT_CASE_ID = "22222222-2222-2222-2222-222222222222";

let artifactCounter = 0;

/**
 * Build an ArtifactPublic with sensible defaults for tests.
 * Pass overrides to vary classification, status, or batch grouping.
 */
export function makeArtifact(
  overrides: Partial<ArtifactPublic> = {},
): ArtifactPublic {
  artifactCounter += 1;
  const id =
    overrides.id ?? `33333333-3333-3333-3333-${String(artifactCounter).padStart(12, "0")}`;
  return {
    id,
    case_id: DEFAULT_CASE_ID,
    original_filename: "report.pdf",
    file_size_bytes: 12,
    file_extension: "pdf",
    mime_type: "application/pdf",
    uploaded_by: "11111111-1111-1111-1111-111111111111",
    uploaded_at: "2026-06-10T10:00:00Z",
    content_hash: "abc123",
    status: "preserved",
    source_group: "unknown",
    source_family: "unknown",
    artifact_type: "unknown",
    collection_method: "unknown",
    parser_class: "unknown",
    provenance_notes: null,
    upload_batch_id: null,
    classification_confidence: null,
    suggested_source_group: "unknown",
    suggested_source_family: "unknown",
    suggested_artifact_type: "unknown",
    classification_reason: null,
    blocker_notes: null,
    created_at: "2026-06-10T10:00:00Z",
    updated_at: "2026-06-10T10:00:00Z",
    ...overrides,
  };
}
