import {
  Box,
  Button,
  Dialog,
  NativeSelect,
  Portal,
  Stack,
  Text,
} from "@chakra-ui/react";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { useAuth } from "../../context/AuthContext";
import type {
  ReadableViewContentPublic,
  ReadableViewPublic,
} from "../../lib/apiClient";

function formatViewType(viewType: string): string {
  return viewType.replace(/_/g, " ");
}

interface ReadablePreviewPanelProps {
  caseId: string;
  artifactId: string;
}

export function ReadablePreviewPanel({
  caseId,
  artifactId,
}: ReadablePreviewPanelProps) {
  const { client } = useAuth();
  const [open, setOpen] = useState(false);
  const [selectedViewId, setSelectedViewId] = useState<string | null>(null);

  const viewsQuery = useQuery({
    queryKey: ["readable-views", caseId, artifactId],
    queryFn: () => client.listReadableViews(caseId, artifactId),
    enabled: open,
  });

  const views = viewsQuery.data ?? [];
  const activeViewId = selectedViewId ?? views[0]?.id ?? null;

  const contentQuery = useQuery({
    queryKey: ["readable-content", caseId, artifactId, activeViewId],
    queryFn: () =>
      client.fetchReadableContent(caseId, artifactId, activeViewId ?? ""),
    enabled: open && Boolean(activeViewId),
  });

  const selectedView = useMemo(
    () => views.find((view) => view.id === activeViewId),
    [views, activeViewId],
  );

  return (
    <>
      <Button size="sm" variant="outline" onClick={() => setOpen(true)}>
        Preview
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
                <Dialog.Title>Readable preview</Dialog.Title>
              </Dialog.Header>
              <Dialog.Body>
                {viewsQuery.isLoading && <Text>Loading previews…</Text>}

                {!viewsQuery.isLoading && views.length === 0 && (
                  <Text color="gray.600">
                    No readable preview is available for this artifact yet.
                    Transform the artifact to generate a preview.
                  </Text>
                )}

                {views.length > 0 && (
                  <Stack gap={4}>
                    {views.length > 1 && (
                      <Box>
                        <Text fontSize="sm" mb={1} color="gray.600">
                          View type
                        </Text>
                        <NativeSelect.Root size="sm">
                          <NativeSelect.Field
                            value={activeViewId ?? ""}
                            onChange={(event) =>
                              setSelectedViewId(event.target.value)
                            }
                          >
                            {views.map((view: ReadableViewPublic) => (
                              <option key={view.id} value={view.id}>
                                {formatViewType(view.view_type)} ({view.status})
                              </option>
                            ))}
                          </NativeSelect.Field>
                        </NativeSelect.Root>
                      </Box>
                    )}

                    {selectedView && selectedView.status === "failed" && (
                      <Text color="red.500" fontSize="sm">
                        Generation failed: {selectedView.error_notes ?? "Unknown error"}
                      </Text>
                    )}

                    {selectedView && selectedView.status === "partial" && (
                      <Text color="orange.600" fontSize="sm">
                        Partial preview — {selectedView.error_notes}
                      </Text>
                    )}

                    {contentQuery.isLoading && <Text>Loading content…</Text>}

                    {contentQuery.data && (
                      <PreviewContent body={contentQuery.data} />
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

function PreviewContent({ body }: { body: ReadableViewContentPublic }) {
  return (
    <Box
      as="pre"
      p={3}
      bg="gray.50"
      borderWidth="1px"
      borderRadius="md"
      fontSize="sm"
      whiteSpace="pre-wrap"
      maxH="400px"
      overflowY="auto"
    >
      {body.content}
      {body.truncated && (
        <Text mt={2} fontSize="xs" color="gray.500">
          Preview truncated for safety.
        </Text>
      )}
    </Box>
  );
}
