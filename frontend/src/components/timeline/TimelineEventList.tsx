import { Badge, Box, Stack, Text } from "@chakra-ui/react";

import type { EvidenceEventPublic } from "../../lib/apiClient";

interface TimelineEventListProps {
  events: EvidenceEventPublic[];
  selectedEventId: string | null;
  onSelect: (eventId: string) => void;
}

function formatEventDate(event: EvidenceEventPublic): string {
  if (event.normalized_timestamp) {
    return new Date(event.normalized_timestamp).toLocaleString();
  }
  if (event.original_timestamp_text) {
    return event.original_timestamp_text;
  }
  return new Date(event.created_at).toLocaleString();
}

function formatReviewStatus(status: string): string {
  return status.replace(/_/g, " ");
}

export function TimelineEventList({
  events,
  selectedEventId,
  onSelect,
}: TimelineEventListProps) {
  return (
    <Stack gap={2} aria-label="Timeline events">
      {events.map((event) => {
        const isSelected = event.id === selectedEventId;
        return (
          <Box
            key={event.id}
            as="button"
            width="100%"
            textAlign="left"
            p={4}
            borderWidth="1px"
            borderRadius="md"
            borderColor={isSelected ? "blue.500" : "gray.200"}
            bg={isSelected ? "blue.50" : "white"}
            cursor="pointer"
            onClick={() => onSelect(event.id)}
            aria-pressed={isSelected}
            aria-label={`Timeline event ${event.title ?? event.event_type}`}
          >
            <Text fontSize="sm" color="gray.600">
              {formatEventDate(event)}
            </Text>
            <Text fontWeight="medium" mt={1}>
              {event.title ?? event.event_type.replace(/_/g, " ")}
            </Text>
            <Stack direction="row" gap={2} mt={2} flexWrap="wrap">
              <Badge size="sm" colorPalette="gray">
                {event.source_group ?? "unknown source"}
              </Badge>
              <Badge size="sm" colorPalette="blue">
                {(event.source_confidence * 100).toFixed(0)}% confidence
              </Badge>
              <Badge size="sm" colorPalette="purple">
                {formatReviewStatus(event.review_status)}
              </Badge>
            </Stack>
          </Box>
        );
      })}
    </Stack>
  );
}
