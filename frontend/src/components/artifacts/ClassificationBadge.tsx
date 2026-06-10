import { Badge, HStack, Text } from "@chakra-ui/react";

import type { ArtifactPublic } from "../../lib/apiClient";

interface ClassificationBadgeProps {
  artifact: ArtifactPublic;
}

function formatLabel(value: string | undefined): string {
  if (!value || value === "unknown") {
    return "Unknown";
  }
  return value.replace(/_/g, " ");
}

export function ClassificationBadge({ artifact }: ClassificationBadgeProps) {
  const hasSuggestion =
    artifact.suggested_source_group !== "unknown" ||
    artifact.suggested_source_family !== "unknown";

  if (!hasSuggestion && artifact.classification_confidence == null) {
    return null;
  }

  const confidence =
    artifact.classification_confidence != null
      ? `${Math.round(artifact.classification_confidence * 100)}%`
      : "—";

  const group = formatLabel(
    artifact.suggested_source_group !== "unknown"
      ? artifact.suggested_source_group
      : artifact.source_group,
  );
  const family = formatLabel(
    artifact.suggested_source_family !== "unknown"
      ? artifact.suggested_source_family
      : artifact.source_family,
  );

  const needsReview = artifact.status === "needs_review";

  return (
    <HStack gap={2} flexWrap="wrap">
      <Badge colorPalette={needsReview ? "orange" : "blue"}>
        {group} / {family}
      </Badge>
      <Text fontSize="sm" color="gray.600">
        Confidence: {confidence}
      </Text>
      {artifact.classification_reason && (
        <Text fontSize="sm" color="gray.500">
          {artifact.classification_reason}
        </Text>
      )}
    </HStack>
  );
}
