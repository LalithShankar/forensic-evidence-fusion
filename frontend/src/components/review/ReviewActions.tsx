import { Button, Field, HStack, Input, Stack } from "@chakra-ui/react";
import { useMutation } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { useAuth } from "../../context/AuthContext";
import {
  ApiRequestError,
  type ArtifactPublic,
  type ReviewActionInput,
  formatValidationErrors,
} from "../../lib/apiClient";

interface ReviewActionsProps {
  caseId: string;
  artifact: ArtifactPublic;
  onUpdated: () => void;
}

export function ReviewActions({
  caseId,
  artifact,
  onUpdated,
}: ReviewActionsProps) {
  const { client } = useAuth();
  const [sourceGroup, setSourceGroup] = useState(artifact.source_group);
  const [sourceFamily, setSourceFamily] = useState(artifact.source_family);
  const [artifactType, setArtifactType] = useState(artifact.artifact_type);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (input: ReviewActionInput) =>
      client.reviewArtifact(caseId, artifact.id, input),
    onSuccess: (result) => {
      setError(null);
      setMessage(result.message);
      onUpdated();
    },
    onError: (err: unknown) => {
      setMessage(null);
      if (err instanceof ApiRequestError) {
        setError(
          typeof err.detail === "string"
            ? err.detail
            : formatValidationErrors(err.detail),
        );
        return;
      }
      setError("Review action failed.");
    },
  });

  function submitAction(action: ReviewActionInput["action"]) {
    setError(null);
    setMessage(null);
    mutation.mutate({
      action,
      source_group: sourceGroup,
      source_family: sourceFamily,
      artifact_type: artifactType,
    });
  }

  function handleCorrect(event: FormEvent) {
    event.preventDefault();
    submitAction("correct");
  }

  return (
    <Stack gap={3} mt={3}>
      <form onSubmit={handleCorrect}>
        <Stack gap={3}>
          <Field.Root>
            <Field.Label>Source group</Field.Label>
            <Input
              value={sourceGroup}
              onChange={(event) => setSourceGroup(event.target.value)}
            />
          </Field.Root>
          <Field.Root>
            <Field.Label>Source family</Field.Label>
            <Input
              value={sourceFamily}
              onChange={(event) => setSourceFamily(event.target.value)}
            />
          </Field.Root>
          <Field.Root>
            <Field.Label>Artifact type</Field.Label>
            <Input
              value={artifactType}
              onChange={(event) => setArtifactType(event.target.value)}
            />
          </Field.Root>
          <HStack gap={2} flexWrap="wrap">
            <Button
              type="submit"
              size="sm"
              colorPalette="blue"
              loading={mutation.isPending}
            >
              Save correction
            </Button>
            <Button
              type="button"
              size="sm"
              colorPalette="green"
              loading={mutation.isPending}
              onClick={() => submitAction("approve")}
            >
              Approve
            </Button>
            <Button
              type="button"
              size="sm"
              variant="outline"
              loading={mutation.isPending}
              onClick={() => submitAction("preserve_only")}
            >
              Preserve only
            </Button>
          </HStack>
        </Stack>
      </form>
      {error && (
        <span role="alert" style={{ color: "var(--chakra-colors-red-500)" }}>
          {error}
        </span>
      )}
      {message && (
        <span role="status" style={{ color: "var(--chakra-colors-green-600)" }}>
          {message}
        </span>
      )}
    </Stack>
  );
}
