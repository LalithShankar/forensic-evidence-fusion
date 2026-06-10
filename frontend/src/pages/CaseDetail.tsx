import {
  Box,
  Button,
  Field,
  Heading,
  Input,
  Link,
  NativeSelect,
  Stack,
  Text,
} from "@chakra-ui/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useEffect, useState } from "react";
import { Link as RouterLink, useParams } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import {
  ApiRequestError,
  formatValidationErrors,
  type CaseScenarioType,
  type CaseUpdateInput,
} from "../lib/apiClient";

const SCENARIO_OPTIONS: { value: CaseScenarioType; label: string }[] = [
  { value: "general_investigation", label: "General investigation" },
  { value: "financial_fraud", label: "Financial fraud" },
  { value: "insider_trading", label: "Insider trading" },
  { value: "money_laundering", label: "Money laundering" },
];

function formatScenarioLabel(value: string): string {
  return value.replace(/_/g, " ");
}

export function CaseDetailPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const { client } = useAuth();
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [scenarioType, setScenarioType] =
    useState<CaseScenarioType>("general_investigation");
  const [dateRangeStart, setDateRangeStart] = useState("");
  const [dateRangeEnd, setDateRangeEnd] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  const caseQuery = useQuery({
    queryKey: ["cases", caseId],
    queryFn: () => client.getCase(caseId ?? ""),
    enabled: Boolean(caseId),
    retry: false,
  });

  useEffect(() => {
    if (!caseQuery.data) {
      return;
    }
    setName(caseQuery.data.name);
    setDescription(caseQuery.data.description ?? "");
    setScenarioType(caseQuery.data.scenario_type);
    setDateRangeStart(caseQuery.data.date_range_start ?? "");
    setDateRangeEnd(caseQuery.data.date_range_end ?? "");
  }, [caseQuery.data]);

  const updateMutation = useMutation({
    mutationFn: (input: CaseUpdateInput) =>
      client.updateCase(caseId ?? "", input),
    onSuccess: async () => {
      setFormError(null);
      setSaveMessage("Changes saved.");
      await queryClient.invalidateQueries({ queryKey: ["cases"] });
      await queryClient.invalidateQueries({ queryKey: ["cases", caseId] });
    },
    onError: (error: unknown) => {
      setSaveMessage(null);
      if (error instanceof ApiRequestError && error.status === 422) {
        setFormError(formatValidationErrors(error.detail));
        return;
      }
      setFormError("Unable to save changes. Please try again.");
    },
  });

  if (!caseId) {
    return <CaseNotFound />;
  }

  if (caseQuery.isLoading) {
    return <Text>Loading case…</Text>;
  }

  if (
    caseQuery.isError &&
    caseQuery.error instanceof ApiRequestError &&
    caseQuery.error.status === 404
  ) {
    return <CaseNotFound />;
  }

  if (caseQuery.isError || !caseQuery.data) {
    return <Text color="red.500">Unable to load case.</Text>;
  }

  const caseData = caseQuery.data;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    setSaveMessage(null);
    updateMutation.mutate({
      name: name.trim(),
      description: description.trim() || null,
      scenario_type: scenarioType,
      date_range_start: dateRangeStart || null,
      date_range_end: dateRangeEnd || null,
    });
  }

  return (
    <Stack gap={8}>
      <Box>
        <Link asChild variant="plain" fontSize="sm" mb={2} display="inline-block">
          <RouterLink to="/cases">← Back to cases</RouterLink>
        </Link>
        <Heading size="lg">{caseData.name}</Heading>
        <Text mt={2} color="gray.600">
          Scenario: {formatScenarioLabel(caseData.scenario_type)}
        </Text>
        <Stack direction="row" gap={4} mt={3}>
          <Link asChild display="inline-block" colorPalette="blue">
            <RouterLink to={`/cases/${caseId}/upload`}>Upload evidence</RouterLink>
          </Link>
          <Link asChild display="inline-block" colorPalette="blue">
            <RouterLink to={`/cases/${caseId}/review`}>Review queue</RouterLink>
          </Link>
          <Link asChild display="inline-block" colorPalette="blue">
            <RouterLink to={`/cases/${caseId}/timeline`}>Timeline</RouterLink>
          </Link>
        </Stack>
      </Box>

      <Box as="section" aria-label="Case details">
        <Heading size="md" mb={4}>
          Case details
        </Heading>
        <Stack gap={2} mb={6}>
          <Text>
            <strong>Description:</strong> {caseData.description || "—"}
          </Text>
          <Text>
            <strong>Date range:</strong>{" "}
            {caseData.date_range_start || "—"} to {caseData.date_range_end || "—"}
          </Text>
          <Text fontSize="sm" color="gray.600">
            Last updated: {new Date(caseData.updated_at).toLocaleString()}
          </Text>
        </Stack>

        <Heading size="sm" mb={4}>
          Edit case
        </Heading>
        <form noValidate onSubmit={handleSubmit}>
          <Stack gap={4} maxW="lg">
            <Field.Root required>
              <Field.Label>Name</Field.Label>
              <Input
                value={name}
                onChange={(event) => setName(event.target.value)}
              />
            </Field.Root>
            <Field.Root>
              <Field.Label>Description</Field.Label>
              <Input
                value={description}
                onChange={(event) => setDescription(event.target.value)}
              />
            </Field.Root>
            <Field.Root required>
              <Field.Label>Scenario type</Field.Label>
              <NativeSelect.Root>
                <NativeSelect.Field
                  value={scenarioType}
                  onChange={(event) =>
                    setScenarioType(event.target.value as CaseScenarioType)
                  }
                >
                  {SCENARIO_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </NativeSelect.Field>
              </NativeSelect.Root>
            </Field.Root>
            <Field.Root>
              <Field.Label>Date range start</Field.Label>
              <Input
                type="date"
                value={dateRangeStart}
                onChange={(event) => setDateRangeStart(event.target.value)}
              />
            </Field.Root>
            <Field.Root>
              <Field.Label>Date range end</Field.Label>
              <Input
                type="date"
                value={dateRangeEnd}
                onChange={(event) => setDateRangeEnd(event.target.value)}
              />
            </Field.Root>
            {formError && (
              <Text color="red.500" role="alert">
                {formError}
              </Text>
            )}
            {saveMessage && (
              <Text color="green.600" role="status">
                {saveMessage}
              </Text>
            )}
            <Button
              type="submit"
              colorPalette="blue"
              loading={updateMutation.isPending}
            >
              Save changes
            </Button>
          </Stack>
        </form>
      </Box>
    </Stack>
  );
}

function CaseNotFound() {
  return (
    <Box>
      <Heading size="lg">Case not found</Heading>
      <Text mt={4}>
        This case does not exist or you do not have permission to view it.
      </Text>
      <Link asChild mt={4} display="inline-block">
        <RouterLink to="/cases">Return to cases</RouterLink>
      </Link>
    </Box>
  );
}
