import { Link, Stack, Text } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import type { SourceReferencePublic } from "../../lib/apiClient";

interface SourceReferencesProps {
  caseId: string;
  sources: SourceReferencePublic[];
}

export function SourceReferences({ caseId, sources }: SourceReferencesProps) {
  if (sources.length === 0) {
    return null;
  }

  return (
    <Stack gap={2} aria-label="Source references">
      <Text fontWeight="medium">Sources</Text>
      {sources.map((source) => (
        <Stack key={source.chunk_id} gap={1}>
          <Link asChild fontSize="sm" colorPalette="blue">
            <RouterLink to={`/cases/${caseId}/artifacts/${source.artifact_id}`}>
              Artifact {source.artifact_id}
            </RouterLink>
          </Link>
          {source.event_id && (
            <Link asChild fontSize="sm" colorPalette="purple">
              <RouterLink
                to={`/cases/${caseId}/timeline?event=${source.event_id}`}
              >
                Timeline event {source.event_id}
              </RouterLink>
            </Link>
          )}
          {source.provenance_pointer && (
            <Text fontSize="xs" color="gray.600">
              Provenance: {source.provenance_pointer}
            </Text>
          )}
        </Stack>
      ))}
    </Stack>
  );
}
