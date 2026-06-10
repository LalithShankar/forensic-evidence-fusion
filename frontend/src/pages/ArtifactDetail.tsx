import {
  Box,
  Heading,
  Link,
  Stack,
  Text,
} from "@chakra-ui/react";
import { useQuery } from "@tanstack/react-query";
import { Link as RouterLink, useParams } from "react-router-dom";

import { StructuredDatasetPanel } from "../components/datasets/StructuredDatasetPanel";
import { ReadablePreviewPanel } from "../components/previews/ReadablePreviewPanel";
import { useAuth } from "../context/AuthContext";
import type { ArtifactPublic } from "../lib/apiClient";

function formatStatus(status: ArtifactPublic["status"]): string {
  return status.replace(/_/g, " ");
}

function formatProvenance(value: string): string {
  return value === "unknown" ? "Unknown" : value.replace(/_/g, " ");
}

function MetadataRow({ label, value }: { label: string; value: string }) {
  return (
    <Box>
      <Text fontSize="sm" color="gray.600">
        {label}
      </Text>
      <Text>{value}</Text>
    </Box>
  );
}

export function ArtifactDetailPage() {
  const { caseId, artifactId } = useParams<{
    caseId: string;
    artifactId: string;
  }>();
  const { client } = useAuth();

  const artifactQuery = useQuery({
    queryKey: ["artifact", caseId, artifactId],
    queryFn: () => client.getArtifact(caseId ?? "", artifactId ?? ""),
    enabled: Boolean(caseId && artifactId),
  });

  if (!caseId || !artifactId) {
    return <Text>Missing case or artifact identifier.</Text>;
  }

  if (artifactQuery.isLoading) {
    return <Text>Loading artifact…</Text>;
  }

  if (artifactQuery.isError || !artifactQuery.data) {
    return (
      <Stack gap={4}>
        <Text color="red.500">Artifact not found or inaccessible.</Text>
        <Link asChild>
          <RouterLink to={`/cases/${caseId}/upload`}>← Back to uploads</RouterLink>
        </Link>
      </Stack>
    );
  }

  const artifact = artifactQuery.data;

  return (
    <Stack gap={6}>
      <Box>
        <Link asChild variant="plain" fontSize="sm" mb={2} display="inline-block">
          <RouterLink to={`/cases/${caseId}/upload`}>← Back to uploads</RouterLink>
        </Link>
        <Heading size="lg">{artifact.original_filename}</Heading>
        <Text mt={2} color="gray.600">
          {artifact.mime_type} · {artifact.file_size_bytes} bytes ·{" "}
          {formatStatus(artifact.status)}
        </Text>
        <Stack direction="row" gap={2} mt={3}>
          <ReadablePreviewPanel caseId={caseId} artifactId={artifactId} />
          <StructuredDatasetPanel caseId={caseId} artifactId={artifactId} />
        </Stack>
      </Box>

      <Box as="section" aria-label="Provenance metadata">
        <Heading size="md" mb={4}>
          Provenance metadata
        </Heading>
        <Stack gap={3}>
          <MetadataRow
            label="Source group"
            value={formatProvenance(artifact.source_group)}
          />
          <MetadataRow
            label="Source family"
            value={formatProvenance(artifact.source_family)}
          />
          <MetadataRow
            label="Artifact type"
            value={formatProvenance(artifact.artifact_type)}
          />
          <MetadataRow
            label="Collection method"
            value={formatProvenance(artifact.collection_method)}
          />
          <MetadataRow
            label="Parser class"
            value={formatProvenance(artifact.parser_class)}
          />
          <Box>
            <Text fontSize="sm" color="gray.600">
              Provenance notes
            </Text>
            <Text>{artifact.provenance_notes ?? "—"}</Text>
          </Box>
        </Stack>
      </Box>

      <Box as="section" aria-label="Preservation details">
        <Heading size="md" mb={4}>
          Preservation details
        </Heading>
        <Stack gap={3}>
          <MetadataRow label="Content hash" value={artifact.content_hash ?? "—"} />
          <MetadataRow label="File extension" value={artifact.file_extension || "—"} />
          {artifact.uploaded_at && (
            <MetadataRow
              label="Uploaded at"
              value={new Date(artifact.uploaded_at).toLocaleString()}
            />
          )}
        </Stack>
      </Box>
    </Stack>
  );
}
