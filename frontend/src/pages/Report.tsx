import {
  Accordion,
  Box,
  Button,
  Heading,
  Link,
  Stack,
  Text,
} from "@chakra-ui/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link as RouterLink, useParams } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import type { ReportSectionPublic } from "../lib/apiClient";

export function ReportPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const { client } = useAuth();
  const queryClient = useQueryClient();

  const reportsQuery = useQuery({
    queryKey: ["reports", caseId],
    queryFn: () => client.listReports(caseId ?? ""),
    enabled: Boolean(caseId),
  });

  const generateMutation = useMutation({
    mutationFn: () => client.generateReport(caseId ?? ""),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["reports", caseId] });
    },
  });

  if (!caseId) {
    return <Text>Missing case identifier.</Text>;
  }

  const latestReport = reportsQuery.data?.[0];

  return (
    <Stack gap={8}>
      <Box>
        <Link asChild variant="plain" fontSize="sm" mb={2} display="inline-block">
          <RouterLink to={`/cases/${caseId}`}>← Back to case</RouterLink>
        </Link>
        <Heading size="lg">Report draft</Heading>
        <Text mt={2} color="gray.600">
          Structured case findings from timeline events, claim resolutions, and
          source artifacts.
        </Text>
      </Box>

      <Box>
        <Button
          colorPalette="blue"
          loading={generateMutation.isPending}
          onClick={() => generateMutation.mutate()}
        >
          {latestReport ? "Regenerate draft" : "Generate draft"}
        </Button>
        {generateMutation.isError && (
          <Text mt={2} color="red.500" role="alert">
            Unable to generate report. Please try again.
          </Text>
        )}
      </Box>

      {reportsQuery.isLoading && <Text>Loading reports…</Text>}

      {latestReport && (
        <Box as="section" aria-label="Report draft viewer">
          <Heading size="md" mb={2}>
            {latestReport.title}
          </Heading>
          <Text fontSize="sm" color="gray.600" mb={4}>
            Status: {latestReport.status} · Updated{" "}
            {new Date(latestReport.updated_at).toLocaleString()}
          </Text>
          {latestReport.content_json?.summary && (
            <Text mb={4}>{latestReport.content_json.summary}</Text>
          )}
          <Accordion.Root multiple defaultValue={["timeline_summary"]}>
            {(latestReport.content_json?.sections ?? []).map(
              (section: ReportSectionPublic) => (
                <Accordion.Item key={section.key} value={section.key}>
                  <Accordion.ItemTrigger>
                    <Accordion.ItemIndicator />
                    {section.title}
                  </Accordion.ItemTrigger>
                  <Accordion.ItemContent>
                    <Box
                      as="pre"
                      whiteSpace="pre-wrap"
                      fontSize="sm"
                      p={3}
                      bg="gray.50"
                      borderRadius="md"
                    >
                      {JSON.stringify(section.content, null, 2)}
                    </Box>
                  </Accordion.ItemContent>
                </Accordion.Item>
              ),
            )}
          </Accordion.Root>
        </Box>
      )}

      {!reportsQuery.isLoading && !latestReport && (
        <Text color="gray.600">No report draft yet. Generate one to begin.</Text>
      )}
    </Stack>
  );
}
