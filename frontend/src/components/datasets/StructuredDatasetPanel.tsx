import {
  Box,
  Button,
  Dialog,
  Portal,
  Stack,
  Text,
} from "@chakra-ui/react";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { useAuth } from "../../context/AuthContext";

interface StructuredDatasetPanelProps {
  caseId: string;
  artifactId: string;
}

export function StructuredDatasetPanel({
  caseId,
  artifactId,
}: StructuredDatasetPanelProps) {
  const { client } = useAuth();
  const [open, setOpen] = useState(false);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null);

  const datasetsQuery = useQuery({
    queryKey: ["structured-datasets", caseId, artifactId],
    queryFn: () => client.listStructuredDatasets(caseId, artifactId),
    enabled: open,
  });

  const datasets = datasetsQuery.data ?? [];
  const activeDatasetId = selectedDatasetId ?? datasets[0]?.id ?? null;

  const previewQuery = useQuery({
    queryKey: ["structured-preview", caseId, artifactId, activeDatasetId],
    queryFn: () =>
      client.fetchStructuredDatasetPreview(
        caseId,
        artifactId,
        activeDatasetId ?? "",
      ),
    enabled: open && Boolean(activeDatasetId),
  });

  return (
    <>
      <Button size="sm" variant="outline" onClick={() => setOpen(true)}>
        Structured data
      </Button>

      <Dialog.Root
        open={open}
        onOpenChange={(details) => setOpen(details.open)}
        size="xl"
      >
        <Portal>
          <Dialog.Backdrop />
          <Dialog.Positioner>
            <Dialog.Content>
              <Dialog.Header>
                <Dialog.Title>Structured dataset</Dialog.Title>
              </Dialog.Header>
              <Dialog.Body>
                {datasetsQuery.isLoading && <Text>Loading datasets…</Text>}

                {!datasetsQuery.isLoading && datasets.length === 0 && (
                  <Text color="gray.600">
                    No structured dataset is available for this artifact yet.
                  </Text>
                )}

                {datasets.length > 0 && (
                  <Stack gap={4}>
                    {datasets.map((dataset) => (
                      <Box
                        key={dataset.id}
                        p={3}
                        borderWidth="1px"
                        borderRadius="md"
                        cursor="pointer"
                        bg={
                          activeDatasetId === dataset.id ? "blue.50" : "transparent"
                        }
                        onClick={() => setSelectedDatasetId(dataset.id)}
                      >
                        <Text fontWeight="medium">
                          {dataset.dataset_type} · {dataset.row_count ?? "?"} rows
                        </Text>
                        <Text fontSize="sm" color="gray.600">
                          Schema {dataset.schema_version} · confidence{" "}
                          {(dataset.confidence * 100).toFixed(0)}% · {dataset.status}
                        </Text>
                      </Box>
                    ))}

                    {previewQuery.isLoading && <Text>Loading preview…</Text>}

                    {previewQuery.data && (
                      <Box>
                        <Text fontSize="sm" mb={2} color="gray.600">
                          Confidence: {(previewQuery.data.confidence * 100).toFixed(0)}%
                        </Text>
                        {previewQuery.data.preview_rows && (
                          <Box
                            as="pre"
                            p={3}
                            bg="gray.50"
                            borderWidth="1px"
                            borderRadius="md"
                            fontSize="sm"
                            maxH="300px"
                            overflowY="auto"
                          >
                            {JSON.stringify(previewQuery.data.preview_rows, null, 2)}
                          </Box>
                        )}
                        {previewQuery.data.preview_json && (
                          <Box
                            as="pre"
                            p={3}
                            bg="gray.50"
                            borderWidth="1px"
                            borderRadius="md"
                            fontSize="sm"
                            whiteSpace="pre-wrap"
                            maxH="300px"
                            overflowY="auto"
                          >
                            {previewQuery.data.preview_json}
                          </Box>
                        )}
                        {previewQuery.data.truncated && (
                          <Text mt={2} fontSize="xs" color="gray.500">
                            Preview truncated for safety.
                          </Text>
                        )}
                      </Box>
                    )}
                  </Stack>
                )}
              </Dialog.Body>
              <Dialog.Footer>
                <Button variant="outline" onClick={() => setOpen(false)}>
                  Close
                </Button>
              </Dialog.Footer>
            </Dialog.Content>
          </Dialog.Positioner>
        </Portal>
      </Dialog.Root>
    </>
  );
}
