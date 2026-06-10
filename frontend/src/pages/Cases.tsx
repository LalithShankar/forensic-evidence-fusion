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
import { FormEvent, useState } from "react";
import { Link as RouterLink } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import {
  ApiRequestError,
  formatValidationErrors,
  type CaseCreateInput,
  type CaseScenarioType,
} from "../lib/apiClient";

const SCENARIO_OPTIONS: { value: CaseScenarioType; label: string }[] = [
  { value: "general_investigation", label: "General investigation" },
  { value: "financial_fraud", label: "Financial fraud" },
  { value: "insider_trading", label: "Insider trading" },
  { value: "money_laundering", label: "Money laundering" },
];

export function CasesPage() {
  const { client } = useAuth();
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [scenarioType, setScenarioType] =
    useState<CaseScenarioType>("general_investigation");
  const [dateRangeStart, setDateRangeStart] = useState("");
  const [dateRangeEnd, setDateRangeEnd] = useState("");
  const [formError, setFormError] = useState<string | null>(null);

  const casesQuery = useQuery({
    queryKey: ["cases"],
    queryFn: () => client.listCases(),
  });

  const createMutation = useMutation({
    mutationFn: (input: CaseCreateInput) => client.createCase(input),
    onSuccess: async () => {
      setName("");
      setDescription("");
      setScenarioType("general_investigation");
      setDateRangeStart("");
      setDateRangeEnd("");
      setFormError(null);
      await queryClient.invalidateQueries({ queryKey: ["cases"] });
    },
    onError: (error: unknown) => {
      if (error instanceof ApiRequestError && error.status === 422) {
        setFormError(formatValidationErrors(error.detail));
        return;
      }
      setFormError("Unable to create case. Please try again.");
    },
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    createMutation.mutate({
      name: name.trim(),
      description: description.trim() || null,
      scenario_type: scenarioType,
      date_range_start: dateRangeStart || null,
      date_range_end: dateRangeEnd || null,
    });
  }

  return (
    <Stack gap={10}>
      <Box>
        <Heading size="lg">Cases</Heading>
        <Text mt={2} color="gray.600">
          Create and manage investigation workspaces you have access to.
        </Text>
      </Box>

      <Box as="section" aria-label="Create case">
        <Heading size="md" mb={4}>
          Create case
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
            <Button
              type="submit"
              colorPalette="blue"
              loading={createMutation.isPending}
            >
              Create case
            </Button>
          </Stack>
        </form>
      </Box>

      <Box as="section" aria-label="Case list" role="region">
        <Heading size="md" mb={4}>
          Your cases
        </Heading>
        {casesQuery.isLoading && <Text>Loading cases…</Text>}
        {casesQuery.isError && (
          <Text color="red.500">Unable to load cases.</Text>
        )}
        {casesQuery.data && casesQuery.data.length === 0 && (
          <Text>No cases yet.</Text>
        )}
        {casesQuery.data && casesQuery.data.length > 0 && (
          <Stack gap={3}>
            {casesQuery.data.map((caseItem) => (
              <Box
                key={caseItem.id}
                p={4}
                borderWidth="1px"
                borderRadius="md"
                bg="white"
              >
                <Link asChild variant="plain" fontWeight="semibold">
                  <RouterLink to={`/cases/${caseItem.id}`}>
                    {caseItem.name}
                  </RouterLink>
                </Link>
                <Text fontSize="sm" color="gray.600" mt={1}>
                  {caseItem.scenario_type.replace(/_/g, " ")}
                </Text>
              </Box>
            ))}
          </Stack>
        )}
      </Box>
    </Stack>
  );
}
