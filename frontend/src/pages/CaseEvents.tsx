import { Box, Heading, Link, Stack, Text } from "@chakra-ui/react";
import { useQuery } from "@tanstack/react-query";
import { Link as RouterLink, useParams } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

export function CaseEventsPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const { client } = useAuth();

  const eventsQuery = useQuery({
    queryKey: ["case-events", caseId],
    queryFn: () => client.listCaseEvents(caseId ?? ""),
    enabled: Boolean(caseId),
  });

  if (!caseId) {
    return <Text>Missing case identifier.</Text>;
  }

  return (
    <Stack gap={6}>
      <Box>
        <Link asChild variant="plain" fontSize="sm" mb={2} display="inline-block">
          <RouterLink to={`/cases/${caseId}`}>← Back to case</RouterLink>
        </Link>
        <Heading size="lg">Evidence events</Heading>
        <Text mt={2} color="gray.600">
          Normalized observations from structured datasets.
        </Text>
      </Box>

      {eventsQuery.isLoading && <Text>Loading events…</Text>}

      {eventsQuery.isError && (
        <Text color="red.500">Could not load events for this case.</Text>
      )}

      {eventsQuery.data && eventsQuery.data.length === 0 && (
        <Text color="gray.600">
          No events yet. Transform artifacts to generate structured data and events.
        </Text>
      )}

      {eventsQuery.data && eventsQuery.data.length > 0 && (
        <Stack gap={3}>
          {eventsQuery.data.map((event) => (
            <Box
              key={event.id}
              p={4}
              borderWidth="1px"
              borderRadius="md"
              aria-label={`Event ${event.event_type}`}
            >
              <Text fontWeight="medium">
                {event.title ?? event.event_type.replace(/_/g, " ")}
              </Text>
              <Text fontSize="sm" color="gray.600">
                {event.event_type}
                {event.original_timestamp_text
                  ? ` · ${event.original_timestamp_text}`
                  : ""}
                {" · confidence "}
                {(event.source_confidence * 100).toFixed(0)}%
              </Text>
              {event.description && <Text mt={2}>{event.description}</Text>}
            </Box>
          ))}
        </Stack>
      )}
    </Stack>
  );
}
