import {
  Box,
  Button,
  Field,
  Heading,
  Input,
  Link,
  Stack,
  Text,
  Textarea,
} from "@chakra-ui/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { Link as RouterLink, useParams } from "react-router-dom";

import { ClaimResolutionPanel } from "../components/claims/ClaimResolutionPanel";
import { useAuth } from "../context/AuthContext";
import {
  ApiRequestError,
  formatValidationErrors,
  type ClaimCreateInput,
} from "../lib/apiClient";

export function ClaimsPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const { client } = useAuth();
  const queryClient = useQueryClient();

  const [claimText, setClaimText] = useState("");
  const [claimant, setClaimant] = useState("");
  const [claimedTime, setClaimedTime] = useState("");
  const [claimedPeople, setClaimedPeople] = useState("");
  const [claimSource, setClaimSource] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [expandedClaimId, setExpandedClaimId] = useState<string | null>(null);

  const claimsQuery = useQuery({
    queryKey: ["claims", caseId],
    queryFn: () => client.listClaims(caseId ?? ""),
    enabled: Boolean(caseId),
  });

  const createMutation = useMutation({
    mutationFn: (input: ClaimCreateInput) => client.createClaim(caseId ?? "", input),
    onSuccess: async () => {
      setFormError(null);
      await queryClient.invalidateQueries({ queryKey: ["claims", caseId] });
    },
    onError: (error: unknown) => {
      if (error instanceof ApiRequestError && error.status === 422) {
        setFormError(formatValidationErrors(error.detail));
        return;
      }
      setFormError("Unable to save claim. Please try again.");
    },
  });

  if (!caseId) {
    return <Text>Missing case identifier.</Text>;
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);

    const people = claimedPeople
      .split(",")
      .map((entry) => entry.trim())
      .filter(Boolean);

    createMutation.mutate(
      {
        claim_text: claimText.trim(),
        claimant: claimant.trim() || null,
        claimed_time_text: claimedTime.trim() || null,
        claimed_people: people.length > 0 ? people : null,
        claim_source: claimSource.trim() || null,
      },
      {
        onSuccess: () => {
          setClaimText("");
          setClaimant("");
          setClaimedTime("");
          setClaimedPeople("");
          setClaimSource("");
        },
      },
    );
  }

  return (
    <Stack gap={8}>
      <Box>
        <Link asChild variant="plain" fontSize="sm" mb={2} display="inline-block">
          <RouterLink to={`/cases/${caseId}`}>← Back to case</RouterLink>
        </Link>
        <Heading size="lg">Claims</Heading>
        <Text mt={2} color="gray.600">
          Enter narrative claims and compare them against timeline evidence.
        </Text>
      </Box>

      <Box as="section" aria-label="Create claim">
        <Heading size="md" mb={4}>
          Add claim
        </Heading>
        <form noValidate onSubmit={handleSubmit}>
          <Stack gap={4} maxW="2xl">
            <Field.Root required>
              <Field.Label>Claim text</Field.Label>
              <Textarea
                value={claimText}
                onChange={(event) => setClaimText(event.target.value)}
                rows={4}
              />
            </Field.Root>
            <Field.Root>
              <Field.Label>Claimant</Field.Label>
              <Input
                value={claimant}
                onChange={(event) => setClaimant(event.target.value)}
              />
            </Field.Root>
            <Field.Root>
              <Field.Label>Claimed time</Field.Label>
              <Input
                value={claimedTime}
                onChange={(event) => setClaimedTime(event.target.value)}
                placeholder="2024-06-01 or free text"
              />
            </Field.Root>
            <Field.Root>
              <Field.Label>Claimed people</Field.Label>
              <Input
                value={claimedPeople}
                onChange={(event) => setClaimedPeople(event.target.value)}
                placeholder="Alice, Bob"
              />
            </Field.Root>
            <Field.Root>
              <Field.Label>Source</Field.Label>
              <Input
                value={claimSource}
                onChange={(event) => setClaimSource(event.target.value)}
                placeholder="interview, document, analyst_note"
              />
            </Field.Root>
            {formError && (
              <Text color="red.500" role="alert">
                {formError}
              </Text>
            )}
            <Button
              type="submit"
              colorPalette="blue"
              loading={createMutation.isPending}
            >
              Save claim
            </Button>
          </Stack>
        </form>
      </Box>

      <Box as="section" aria-label="Claims list">
        <Heading size="md" mb={4}>
          Stored claims
        </Heading>

        {claimsQuery.isLoading && <Text>Loading claims…</Text>}
        {claimsQuery.isError && (
          <Text color="red.500">Could not load claims for this case.</Text>
        )}

        {claimsQuery.data && claimsQuery.data.length === 0 && (
          <Text color="gray.600">No claims yet. Add a narrative claim above.</Text>
        )}

        {claimsQuery.data && claimsQuery.data.length > 0 && (
          <Stack gap={4}>
            {claimsQuery.data.map((claim) => {
              const expanded = expandedClaimId === claim.id;
              return (
                <Box key={claim.id} borderWidth="1px" borderRadius="md" p={4}>
                  <Text fontWeight="medium">{claim.claim_text}</Text>
                  <Text fontSize="sm" color="gray.600" mt={2}>
                    Added {new Date(claim.created_at).toLocaleString()} · parse
                    confidence {(claim.parse_confidence * 100).toFixed(0)}%
                  </Text>
                  <Button
                    size="sm"
                    variant="outline"
                    mt={3}
                    onClick={() =>
                      setExpandedClaimId(expanded ? null : claim.id)
                    }
                  >
                    {expanded ? "Hide resolution" : "Show resolution"}
                  </Button>
                  {expanded && (
                    <ClaimResolutionPanel caseId={caseId} claim={claim} />
                  )}
                </Box>
              );
            })}
          </Stack>
        )}
      </Box>
    </Stack>
  );
}
