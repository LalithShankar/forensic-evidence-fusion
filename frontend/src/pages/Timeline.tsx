import { Box, Heading, Link, SimpleGrid, Stack, Text } from "@chakra-ui/react";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link as RouterLink, useParams } from "react-router-dom";

import { TimelineEventDetail } from "../components/timeline/TimelineEventDetail";
import {
  TimelineFilters,
  type TimelineFilterValues,
} from "../components/timeline/TimelineFilters";
import { TimelineEventList } from "../components/timeline/TimelineEventList";
import { useAuth } from "../context/AuthContext";

const EMPTY_FILTERS: TimelineFilterValues = {
  event_type: "",
  source_group: "",
  review_status: "",
};

export function TimelinePage() {
  const { caseId } = useParams<{ caseId: string }>();
  const { client } = useAuth();
  const [filters, setFilters] = useState<TimelineFilterValues>(EMPTY_FILTERS);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);

  const allEventsQuery = useQuery({
    queryKey: ["timeline-events-all", caseId],
    queryFn: () => client.listTimelineEvents(caseId ?? ""),
    enabled: Boolean(caseId),
  });

  const filteredEventsQuery = useQuery({
    queryKey: ["timeline-events", caseId, filters],
    queryFn: () =>
      client.listTimelineEvents(caseId ?? "", {
        event_type: filters.event_type || undefined,
        source_group: filters.source_group || undefined,
        review_status: filters.review_status || undefined,
      }),
    enabled: Boolean(caseId),
  });

  const selectedEventQuery = useQuery({
    queryKey: ["timeline-event", caseId, selectedEventId],
    queryFn: () => client.getTimelineEvent(caseId ?? "", selectedEventId ?? ""),
    enabled: Boolean(caseId && selectedEventId),
  });

  const filterOptions = useMemo(() => {
    const events = allEventsQuery.data ?? [];
    return {
      eventTypes: [...new Set(events.map((event) => event.event_type))].sort(),
      sourceGroups: [
        ...new Set(
          events
            .map((event) => event.source_group)
            .filter((group): group is string => Boolean(group)),
        ),
      ].sort(),
    };
  }, [allEventsQuery.data]);

  if (!caseId) {
    return <Text>Missing case identifier.</Text>;
  }

  const events = filteredEventsQuery.data ?? [];

  return (
    <Stack gap={6}>
      <Box>
        <Link asChild variant="plain" fontSize="sm" mb={2} display="inline-block">
          <RouterLink to={`/cases/${caseId}`}>← Back to case</RouterLink>
        </Link>
        <Heading size="lg">Timeline</Heading>
        <Text mt={2} color="gray.600">
          Chronological evidence events with filters and source drill-down.
        </Text>
      </Box>

      <TimelineFilters
        values={filters}
        eventTypes={filterOptions.eventTypes}
        sourceGroups={filterOptions.sourceGroups}
        onChange={(nextFilters) => {
          setFilters(nextFilters);
          setSelectedEventId(null);
        }}
      />

      {filteredEventsQuery.isLoading && <Text>Loading timeline…</Text>}

      {filteredEventsQuery.isError && (
        <Text color="red.500">Could not load timeline for this case.</Text>
      )}

      {filteredEventsQuery.data && filteredEventsQuery.data.length === 0 && (
        <Box
          borderWidth="1px"
          borderRadius="md"
          p={8}
          textAlign="center"
          aria-label="Empty timeline"
        >
          <Heading size="sm" mb={2}>
            No events yet
          </Heading>
          <Text color="gray.600">
            Transform artifacts to generate structured datasets and normalized
            events for this case.
          </Text>
        </Box>
      )}

      {events.length > 0 && (
        <SimpleGrid columns={{ base: 1, lg: 2 }} gap={6}>
          <TimelineEventList
            events={events}
            selectedEventId={selectedEventId}
            onSelect={setSelectedEventId}
          />
          <TimelineEventDetail
            caseId={caseId}
            event={selectedEventQuery.data ?? null}
            isLoading={selectedEventQuery.isFetching}
          />
        </SimpleGrid>
      )}
    </Stack>
  );
}
