import {
  Box,
  Button,
  Field,
  Heading,
  Input,
  Stack,
  Text,
} from "@chakra-ui/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { useAuth } from "../../context/AuthContext";
import {
  ApiRequestError,
  formatValidationErrors,
  type BulkUploadResponse,
} from "../../lib/apiClient";
import { ClassificationBadge } from "../artifacts/ClassificationBadge";

interface BulkUploadProps {
  caseId: string;
}

export function BulkUpload({ caseId }: BulkUploadProps) {
  const { client } = useAuth();
  const queryClient = useQueryClient();
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [formError, setFormError] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<BulkUploadResponse | null>(
    null,
  );

  const uploadMutation = useMutation({
    mutationFn: (files: File[]) => client.bulkUploadArtifacts(caseId, files),
    onSuccess: (result) => {
      setFormError(null);
      setLastResult(result);
      setSelectedFiles([]);
      void queryClient.invalidateQueries({ queryKey: ["artifacts", caseId] });
    },
    onError: (error: unknown) => {
      setLastResult(null);
      if (error instanceof ApiRequestError) {
        setFormError(
          typeof error.detail === "string"
            ? error.detail
            : formatValidationErrors(error.detail),
        );
        return;
      }
      setFormError("Bulk upload failed. Please try again.");
    },
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    setLastResult(null);
    if (selectedFiles.length === 0) {
      setFormError("Choose at least one file to upload.");
      return;
    }
    uploadMutation.mutate(selectedFiles);
  }

  return (
    <Box as="section" aria-label="Bulk upload evidence">
      <Heading size="md" mb={2}>
        Bulk upload
      </Heading>
      <Text mb={4} color="gray.600" fontSize="sm">
        Upload multiple files at once. Successful files are preserved even when
        others fail.
      </Text>
      <form noValidate onSubmit={handleSubmit}>
        <Stack gap={4} maxW="lg">
          <Field.Root required>
            <Field.Label>Evidence files</Field.Label>
            <Input
              type="file"
              multiple
              onChange={(event) => {
                const files = event.target.files;
                setSelectedFiles(files ? Array.from(files) : []);
                setFormError(null);
                setLastResult(null);
              }}
            />
          </Field.Root>
          {selectedFiles.length > 0 && (
            <Text fontSize="sm" color="gray.600">
              {selectedFiles.length} file(s) selected
            </Text>
          )}
          {formError && (
            <Text color="red.500" role="alert">
              {formError}
            </Text>
          )}
          <Button
            type="submit"
            colorPalette="blue"
            loading={uploadMutation.isPending}
          >
            Upload batch
          </Button>
        </Stack>
      </form>

      {lastResult && (
        <Box mt={6} borderWidth="1px" borderRadius="md" p={4}>
          <Text fontWeight="semibold" mb={2}>
            Batch {lastResult.upload_batch_id.slice(0, 8)}… —{" "}
            {lastResult.succeeded_count} succeeded, {lastResult.failed_count}{" "}
            failed
          </Text>
          <Stack gap={3}>
            {lastResult.results.map((item) => (
              <Box key={item.filename} p={3} bg="gray.50" borderRadius="md">
                <Text fontWeight="medium">{item.filename}</Text>
                {item.error && (
                  <Text fontSize="sm" color="red.500">
                    {item.error}
                  </Text>
                )}
                {item.artifact && (
                  <Box mt={1}>
                    <ClassificationBadge artifact={item.artifact} />
                  </Box>
                )}
              </Box>
            ))}
          </Stack>
        </Box>
      )}
    </Box>
  );
}
