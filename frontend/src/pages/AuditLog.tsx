import {
  Box,
  Field,
  Heading,
  Input,
  Link,
  NativeSelect,
  Stack,
  Table,
  Text,
} from "@chakra-ui/react";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link as RouterLink, useParams } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

export function AuditLogPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const { client } = useAuth();
  const [actionFilter, setActionFilter] = useState("");
  const [objectTypeFilter, setObjectTypeFilter] = useState("");
  const [offset, setOffset] = useState(0);
  const limit = 25;

  const auditQuery = useQuery({
    queryKey: ["audit", caseId, actionFilter, objectTypeFilter, offset],
    queryFn: () =>
      client.listAuditLogs(caseId ?? "", {
        action: actionFilter || undefined,
        object_type: objectTypeFilter || undefined,
        limit,
        offset,
      }),
    enabled: Boolean(caseId),
  });

  if (!caseId) {
    return <Text>Missing case identifier.</Text>;
  }

  const total = auditQuery.data?.total ?? 0;
  const items = auditQuery.data?.items ?? [];

  return (
    <Stack gap={8}>
      <Box>
        <Link asChild variant="plain" fontSize="sm" mb={2} display="inline-block">
          <RouterLink to={`/cases/${caseId}`}>← Back to case</RouterLink>
        </Link>
        <Heading size="lg">Audit log</Heading>
        <Text mt={2} color="gray.600">
          Trace case activity with filters by action and object type.
        </Text>
      </Box>

      <Stack direction={{ base: "column", md: "row" }} gap={4} maxW="3xl">
        <Field.Root>
          <Field.Label>Action</Field.Label>
          <Input
            value={actionFilter}
            onChange={(event) => {
              setOffset(0);
              setActionFilter(event.target.value);
            }}
            placeholder="e.g. report.generated"
          />
        </Field.Root>
        <Field.Root>
          <Field.Label>Object type</Field.Label>
          <NativeSelect.Root>
            <NativeSelect.Field
              value={objectTypeFilter}
              onChange={(event) => {
                setOffset(0);
                setObjectTypeFilter(event.target.value);
              }}
            >
              <option value="">All</option>
              <option value="case">case</option>
              <option value="artifact">artifact</option>
              <option value="claim">claim</option>
              <option value="report">report</option>
            </NativeSelect.Field>
          </NativeSelect.Root>
        </Field.Root>
      </Stack>

      {auditQuery.isLoading && <Text>Loading audit entries…</Text>}
      {auditQuery.isError && (
        <Text color="red.500">Unable to load audit log.</Text>
      )}

      {!auditQuery.isLoading && items.length === 0 && (
        <Text color="gray.600">No audit entries match the current filters.</Text>
      )}

      {items.length > 0 && (
        <Box overflowX="auto">
          <Table.Root size="sm">
            <Table.Header>
              <Table.Row>
                <Table.ColumnHeader>Timestamp</Table.ColumnHeader>
                <Table.ColumnHeader>Action</Table.ColumnHeader>
                <Table.ColumnHeader>Object</Table.ColumnHeader>
                <Table.ColumnHeader>User</Table.ColumnHeader>
                <Table.ColumnHeader>Reason</Table.ColumnHeader>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {items.map((entry) => (
                <Table.Row key={entry.audit_id}>
                  <Table.Cell>
                    {new Date(entry.timestamp).toLocaleString()}
                  </Table.Cell>
                  <Table.Cell>{entry.action}</Table.Cell>
                  <Table.Cell>
                    {entry.object_type} · {entry.object_id.slice(0, 8)}…
                  </Table.Cell>
                  <Table.Cell>{entry.user_id.slice(0, 8)}…</Table.Cell>
                  <Table.Cell>{entry.reason ?? "—"}</Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table.Root>
        </Box>
      )}

      {total > limit && (
        <Stack direction="row" gap={4} align="center">
          <Text fontSize="sm">
            Showing {offset + 1}–{Math.min(offset + limit, total)} of {total}
          </Text>
          <Link
            as="button"
            fontSize="sm"
            opacity={offset === 0 ? 0.5 : 1}
            onClick={() => setOffset(Math.max(0, offset - limit))}
          >
            Previous
          </Link>
          <Link
            as="button"
            fontSize="sm"
            opacity={offset + limit >= total ? 0.5 : 1}
            onClick={() => setOffset(offset + limit)}
          >
            Next
          </Link>
        </Stack>
      )}
    </Stack>
  );
}
