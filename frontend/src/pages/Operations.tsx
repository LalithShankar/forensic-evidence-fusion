import { Box, Heading, SimpleGrid, Stack, Text } from "@chakra-ui/react";
import { useQuery } from "@tanstack/react-query";

import { useAuth } from "../context/AuthContext";

export function OperationsPage() {
  const { client } = useAuth();

  const summaryQuery = useQuery({
    queryKey: ["operations", "summary"],
    queryFn: () => client.getOperationsSummary(),
  });

  if (summaryQuery.isLoading) {
    return <Text>Loading operations summary…</Text>;
  }

  if (summaryQuery.isError) {
    return (
      <Text color="red.500">
        Unable to load operations summary. Manager or admin access required.
      </Text>
    );
  }

  const summary = summaryQuery.data;
  if (!summary) {
    return <Text>No operations data available.</Text>;
  }

  const cards = [
    { label: "Cases", value: summary.cases_count },
    { label: "Failed artifacts", value: summary.artifacts.failed },
    { label: "Blocked artifacts", value: summary.artifacts.blocked },
    { label: "Needs review", value: summary.artifacts.needs_review },
    { label: "Running transformations", value: summary.transformations.running },
    { label: "Failed transformations", value: summary.transformations.failed },
    { label: "Blocked transformations", value: summary.transformations.blocked },
    { label: "Index failures", value: summary.search_chunks.failed },
    { label: "Pending index chunks", value: summary.search_chunks.pending },
  ];

  const allZero = cards.every((card) => card.value === 0);

  return (
    <Stack gap={8}>
      <Box>
        <Heading size="lg">Operations</Heading>
        <Text mt={2} color="gray.600">
          Platform-wide processing backlog and failure counts.
        </Text>
      </Box>

      {allZero && (
        <Text color="gray.600" role="status">
          No failed, blocked, or pending work detected.
        </Text>
      )}

      <SimpleGrid columns={{ base: 1, md: 3 }} gap={4}>
        {cards.map((card) => (
          <Box
            key={card.label}
            borderWidth="1px"
            borderRadius="md"
            p={4}
            bg="gray.50"
          >
            <Text fontSize="sm" color="gray.600">
              {card.label}
            </Text>
            <Heading size="md" mt={1}>
              {card.value}
            </Heading>
          </Box>
        ))}
      </SimpleGrid>
    </Stack>
  );
}
