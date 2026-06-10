import { Field, NativeSelect, Stack } from "@chakra-ui/react";

import type { ReviewStatus } from "../../lib/apiClient";

export interface TimelineFilterValues {
  event_type: string;
  source_group: string;
  review_status: string;
}

interface TimelineFiltersProps {
  values: TimelineFilterValues;
  eventTypes: string[];
  sourceGroups: string[];
  onChange: (values: TimelineFilterValues) => void;
}

const REVIEW_STATUS_OPTIONS: { value: ReviewStatus | ""; label: string }[] = [
  { value: "", label: "All review statuses" },
  { value: "pending", label: "Pending" },
  { value: "reviewed", label: "Reviewed" },
  { value: "disputed", label: "Disputed" },
];

export function TimelineFilters({
  values,
  eventTypes,
  sourceGroups,
  onChange,
}: TimelineFiltersProps) {
  function updateField<K extends keyof TimelineFilterValues>(
    key: K,
    value: TimelineFilterValues[K],
  ) {
    onChange({ ...values, [key]: value });
  }

  return (
    <Stack
      direction={{ base: "column", md: "row" }}
      gap={4}
      aria-label="Timeline filters"
    >
      <Field.Root flex={1}>
        <Field.Label>Event type</Field.Label>
        <NativeSelect.Root>
          <NativeSelect.Field
            value={values.event_type}
            onChange={(event) => updateField("event_type", event.target.value)}
          >
            <option value="">All event types</option>
            {eventTypes.map((eventType) => (
              <option key={eventType} value={eventType}>
                {eventType.replace(/_/g, " ")}
              </option>
            ))}
          </NativeSelect.Field>
        </NativeSelect.Root>
      </Field.Root>

      <Field.Root flex={1}>
        <Field.Label>Source group</Field.Label>
        <NativeSelect.Root>
          <NativeSelect.Field
            value={values.source_group}
            onChange={(event) =>
              updateField("source_group", event.target.value)
            }
          >
            <option value="">All source groups</option>
            {sourceGroups.map((group) => (
              <option key={group} value={group}>
                {group}
              </option>
            ))}
          </NativeSelect.Field>
        </NativeSelect.Root>
      </Field.Root>

      <Field.Root flex={1}>
        <Field.Label>Review status</Field.Label>
        <NativeSelect.Root>
          <NativeSelect.Field
            value={values.review_status}
            onChange={(event) =>
              updateField("review_status", event.target.value)
            }
          >
            {REVIEW_STATUS_OPTIONS.map((option) => (
              <option key={option.label} value={option.value}>
                {option.label}
              </option>
            ))}
          </NativeSelect.Field>
        </NativeSelect.Root>
      </Field.Root>
    </Stack>
  );
}
