import { Box, Heading, Link, Stack, Text } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";

import type { EvidenceEventPublic } from "../../lib/apiClient";

interface TimelineEventDetailProps {
  caseId: string;
  event: EvidenceEventPublic | null;
  isLoading: boolean;
}

function summarizePayload(payload: Record<string, unknown> | null): string {
  if (!payload || Object.keys(payload).length === 0) {
    return "No structured payload fields.";
  }
  const entries = Object.entries(payload).slice(0, 6);
  return entries
    .map(([key, value]) => `${key}: ${String(value)}`)
    .join(" · ");
}

export function TimelineEventDetail({
  caseId,
  event,
  isLoading,
}: TimelineEventDetailProps) {
  if (isLoading) {
    return <Text>Loading event details…</Text>;
  }

  if (!event) {
    return (
      <Box
        borderWidth="1px"
        borderRadius="md"
        p={6}
        aria-label="Timeline event detail"
      >
        <Text color="gray.600">Select an event to inspect details.</Text>
      </Box>
    );
  }

  return (
    <Box
      borderWidth="1px"
      borderRadius="md"
      p={6}
      aria-label="Timeline event detail"
    >
      <Heading size="sm" mb={4}>
        Event detail
      </Heading>
      <Stack gap={3}>
        <Text>
          <strong>Type:</strong> {event.event_type.replace(/_/g, " ")}
        </Text>
        {event.description && (
          <Text>
            <strong>Description:</strong> {event.description}
          </Text>
        )}
        <Text>
          <strong>Provenance:</strong> {event.provenance_pointer ?? "—"}
        </Text>
        <Text>
          <strong>Payload summary:</strong>{" "}
          {summarizePayload(event.payload_json)}
        </Text>
        <Link asChild colorPalette="blue">
          <RouterLink to={`/cases/${caseId}/artifacts/${event.artifact_id}`}>
            View source artifact
          </RouterLink>
        </Link>
      </Stack>
    </Box>
  );
}
