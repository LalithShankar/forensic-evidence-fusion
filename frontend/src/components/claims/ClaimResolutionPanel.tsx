import { Badge, Box, Button, Link, Stack, Text } from "@chakra-ui/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link as RouterLink } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";
import type { ClaimPublic } from "../../lib/apiClient";

interface ClaimResolutionPanelProps {
  caseId: string;
  claim: ClaimPublic;
}

function formatLabel(label: string | null | undefined): string {
  if (!label) {
    return "—";
  }
  return label.replace(/_/g, " ");
}

export function ClaimResolutionPanel({ caseId, claim }: ClaimResolutionPanelProps) {
  const { client } = useAuth();
  const queryClient = useQueryClient();

  const resolutionQuery = useQuery({
    queryKey: ["claim-resolution", caseId, claim.id],
    queryFn: () => client.getClaimResolution(caseId, claim.id),
    retry: false,
  });

  const resolveMutation = useMutation({
    mutationFn: () => client.resolveClaim(caseId, claim.id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["claim-resolution", caseId, claim.id],
      });
    },
  });

  const resolution = resolveMutation.data ?? resolutionQuery.data;

  return (
    <Box
      mt={4}
      p={4}
      borderWidth="1px"
      borderRadius="md"
      aria-label={`Resolution for claim ${claim.id}`}
    >
      <Stack direction="row" justify="space-between" align="center" mb={3}>
        <Text fontWeight="medium">Resolution</Text>
        <Button
          size="sm"
          colorPalette="blue"
          loading={resolveMutation.isPending}
          onClick={() => resolveMutation.mutate()}
        >
          Run resolution
        </Button>
      </Stack>

      {resolveMutation.isError && (
        <Text color="red.500" mb={2}>
          Unable to run resolution. Please try again.
        </Text>
      )}

      {!resolution && !resolutionQuery.isFetching && (
        <Text color="gray.600">No resolution yet. Run resolution to compare evidence.</Text>
      )}

      {resolution && (
        <Stack gap={3}>
          <Stack direction="row" gap={2} flexWrap="wrap">
            <Badge colorPalette="purple">{formatLabel(resolution.result_label)}</Badge>
            <Badge colorPalette="green">
              Support {(resolution.support_score ?? 0).toFixed(2)}
            </Badge>
            <Badge colorPalette="red">
              Contradiction {(resolution.contradiction_score ?? 0).toFixed(2)}
            </Badge>
          </Stack>

          {resolution.unresolved_reason && (
            <Text fontSize="sm" color="gray.700">
              {resolution.unresolved_reason}
            </Text>
          )}

          {resolution.supporting_event_ids &&
            resolution.supporting_event_ids.length > 0 && (
              <Box>
                <Text fontSize="sm" fontWeight="medium" mb={1}>
                  Supporting events
                </Text>
                <Stack gap={1}>
                  {resolution.supporting_event_ids.map((eventId) => (
                    <Link
                      key={eventId}
                      asChild
                      fontSize="sm"
                      colorPalette="blue"
                    >
                      <RouterLink to={`/cases/${caseId}/timeline?event=${eventId}`}>
                        {eventId}
                      </RouterLink>
                    </Link>
                  ))}
                </Stack>
              </Box>
            )}

          {resolution.contradicting_event_ids &&
            resolution.contradicting_event_ids.length > 0 && (
              <Box>
                <Text fontSize="sm" fontWeight="medium" mb={1}>
                  Contradicting events
                </Text>
                <Stack gap={1}>
                  {resolution.contradicting_event_ids.map((eventId) => (
                    <Link
                      key={eventId}
                      asChild
                      fontSize="sm"
                      colorPalette="orange"
                    >
                      <RouterLink to={`/cases/${caseId}/timeline?event=${eventId}`}>
                        {eventId}
                      </RouterLink>
                    </Link>
                  ))}
                </Stack>
              </Box>
            )}
        </Stack>
      )}
    </Box>
  );
}
