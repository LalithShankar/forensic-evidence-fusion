import { Box, Heading, Link, Stack, Text } from "@chakra-ui/react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link as RouterLink, useParams } from "react-router-dom";

import { ClassificationBadge } from "../components/artifacts/ClassificationBadge";
import { ReviewActions } from "../components/review/ReviewActions";
import { useAuth } from "../context/AuthContext";

export function ReviewQueuePage() {
  const { caseId } = useParams<{ caseId: string }>();
  const { client } = useAuth();
  const queryClient = useQueryClient();

  const queueQuery = useQuery({
    queryKey: ["review-queue", caseId],
    queryFn: () => client.getReviewQueue(caseId ?? ""),
    enabled: Boolean(caseId),
  });

  if (!caseId) {
    return <Text>Missing case identifier.</Text>;
  }

  function handleUpdated() {
    void queryClient.invalidateQueries({ queryKey: ["review-queue", caseId] });
    void queryClient.invalidateQueries({ queryKey: ["artifacts", caseId] });
  }

  return (
    <Stack gap={8}>
      <Box>
        <Link asChild variant="plain" fontSize="sm" mb={2} display="inline-block">
          <RouterLink to={`/cases/${caseId}`}>← Back to case</RouterLink>
        </Link>
        <Heading size="lg">Review queue</Heading>
        <Text mt={2} color="gray.600">
          Correct uncertain classifications before transformation.
        </Text>
      </Box>

      {queueQuery.isLoading && <Text>Loading review queue…</Text>}
      {queueQuery.isError && (
        <Text color="red.500">Unable to load review queue.</Text>
      )}

      {queueQuery.data && queueQuery.data.total === 0 && (
        <Box
          borderWidth="1px"
          borderRadius="md"
          p={8}
          textAlign="center"
          aria-label="Empty review queue"
        >
          <Heading size="sm" mb={2}>
            All clear
          </Heading>
          <Text color="gray.600">
            No artifacts need review for this case.
          </Text>
        </Box>
      )}

      {queueQuery.data && queueQuery.data.items.length > 0 && (
        <Stack gap={4}>
          {queueQuery.data.items.map((item) => (
            <Box
              key={item.artifact.id}
              borderWidth="1px"
              borderRadius="md"
              p={4}
            >
              <Link asChild fontWeight="semibold">
                <RouterLink
                  to={`/cases/${caseId}/artifacts/${item.artifact.id}`}
                >
                  {item.artifact.original_filename}
                </RouterLink>
              </Link>
              <Text fontSize="sm" color="gray.600" mt={1}>
                Suggested: {item.suggested_category}
              </Text>
              <Text fontSize="sm" color="gray.600">
                Reason: {item.review_reason}
              </Text>
              {item.artifact.blocker_notes && (
                <Text fontSize="sm" color="orange.600" mt={1}>
                  Blocker: {item.artifact.blocker_notes}
                </Text>
              )}
              <Box mt={2}>
                <ClassificationBadge artifact={item.artifact} />
              </Box>
              <ReviewActions
                caseId={caseId}
                artifact={item.artifact}
                onUpdated={handleUpdated}
              />
            </Box>
          ))}
        </Stack>
      )}
    </Stack>
  );
}
