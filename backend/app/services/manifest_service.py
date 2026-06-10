"""Case artifact manifest generation."""

from __future__ import annotations

import uuid

from app.models.artifact import Artifact
from app.schemas.manifest import ArtifactManifestEntry, CaseArtifactManifest


def build_case_manifest(
    case_id: uuid.UUID,
    artifacts: list[Artifact],
) -> CaseArtifactManifest:
    """Build a manifest snapshot from current artifact rows."""
    entries = [ArtifactManifestEntry.model_validate(artifact) for artifact in artifacts]
    return CaseArtifactManifest(
        case_id=case_id,
        artifact_count=len(entries),
        artifacts=entries,
    )
