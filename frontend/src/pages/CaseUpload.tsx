import {
  Box,
  Button,
  Field,
  Heading,
  Input,
  Link,
  Stack,
  Text,
} from "@chakra-ui/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { Link as RouterLink, useParams } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import {
  ApiRequestError,
  type ArtifactPublic,
  formatValidationErrors,
} from "../lib/apiClient";

function formatStatus(status: ArtifactPublic["status"]): string {
  return status.replace(/_/g, " ");
}

export function CaseUploadPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const { client } = useAuth();
  const queryClient = useQueryClient();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const artifactsQuery = useQuery({
    queryKey: ["artifacts", caseId],
    queryFn: () => client.listArtifacts(caseId ?? ""),
    enabled: Boolean(caseId),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => client.uploadArtifact(caseId ?? "", file),
    onSuccess: () => {
      setSuccessMessage("Evidence uploaded and preserved.");
      setFormError(null);
      setSelectedFile(null);
      void queryClient.invalidateQueries({ queryKey: ["artifacts", caseId] });
    },
    onError: (error: unknown) => {
      setSuccessMessage(null);
      if (error instanceof ApiRequestError) {
        setFormError(
          typeof error.detail === "string"
            ? error.detail
            : formatValidationErrors(error.detail),
        );
        return;
      }
      setFormError("Upload failed. Please try again.");
    },
  });

  if (!caseId) {
    return <Text>Missing case identifier.</Text>;
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    setSuccessMessage(null);
    if (!selectedFile) {
      setFormError("Choose a file to upload.");
      return;
    }
    uploadMutation.mutate(selectedFile);
  }

  return (
    <Stack gap={8}>
      <Box>
        <Link asChild variant="plain" fontSize="sm" mb={2} display="inline-block">
          <RouterLink to={`/cases/${caseId}`}>← Back to case</RouterLink>
        </Link>
        <Heading size="lg">Upload evidence</Heading>
        <Text mt={2} color="gray.600">
          Raw files are preserved unchanged before any processing.
        </Text>
      </Box>

      <Box as="section" aria-label="Upload evidence file">
        <form noValidate onSubmit={handleSubmit}>
          <Stack gap={4} maxW="lg">
            <Field.Root required>
              <Field.Label>Evidence file</Field.Label>
              <Input
                type="file"
                onChange={(event) => {
                  setSelectedFile(event.target.files?.[0] ?? null);
                  setFormError(null);
                  setSuccessMessage(null);
                }}
              />
            </Field.Root>
            {formError && (
              <Text color="red.500" role="alert">
                {formError}
              </Text>
            )}
            {successMessage && (
              <Text color="green.600" role="status">
                {successMessage}
              </Text>
            )}
            <Button
              type="submit"
              colorPalette="blue"
              loading={uploadMutation.isPending}
            >
              Upload and preserve
            </Button>
          </Stack>
        </form>
      </Box>

      <Box as="section" aria-label="Uploaded artifacts">
        <Heading size="md" mb={4}>
          Artifacts in this case
        </Heading>
        {artifactsQuery.isLoading && <Text>Loading artifacts…</Text>}
        {artifactsQuery.isError && (
          <Text color="red.500">Unable to load artifacts for this case.</Text>
        )}
        {artifactsQuery.data && artifactsQuery.data.length === 0 && (
          <Text>No artifacts uploaded yet.</Text>
        )}
        {artifactsQuery.data && artifactsQuery.data.length > 0 && (
          <Stack gap={3}>
            {artifactsQuery.data.map((artifact) => (
              <Box
                key={artifact.id}
                borderWidth="1px"
                borderRadius="md"
                p={4}
              >
                <Text fontWeight="semibold">{artifact.original_filename}</Text>
                <Text fontSize="sm" color="gray.600">
                  {artifact.mime_type} · {artifact.file_size_bytes} bytes ·{" "}
                  {formatStatus(artifact.status)}
                </Text>
                {artifact.uploaded_at && (
                  <Text fontSize="sm" color="gray.600">
                    Uploaded {new Date(artifact.uploaded_at).toLocaleString()}
                  </Text>
                )}
              </Box>
            ))}
          </Stack>
        )}
      </Box>
    </Stack>
  );
}
