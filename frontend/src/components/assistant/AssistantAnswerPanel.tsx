import { Alert, Box, Stack, Text } from "@chakra-ui/react";

import type { AssistantAnswerPublic } from "../../lib/apiClient";
import { SourceReferences } from "./SourceReferences";

interface AssistantAnswerPanelProps {
  caseId: string;
  answer: AssistantAnswerPublic | null;
  isLoading: boolean;
}

export function AssistantAnswerPanel({
  caseId,
  answer,
  isLoading,
}: AssistantAnswerPanelProps) {
  if (isLoading) {
    return <Text>Generating answer…</Text>;
  }

  if (!answer) {
    return (
      <Box
        borderWidth="1px"
        borderRadius="md"
        p={6}
        aria-label="Assistant answer"
      >
        <Text color="gray.600">
          Ask a question about indexed evidence in this case.
        </Text>
      </Box>
    );
  }

  return (
    <Box borderWidth="1px" borderRadius="md" p={6} aria-label="Assistant answer">
      <Stack gap={4}>
        {answer.limitation_text && (
          <Alert.Root status="warning">
            <Alert.Indicator />
            <Alert.Content>
              <Alert.Title>Limitations</Alert.Title>
              <Alert.Description>{answer.limitation_text}</Alert.Description>
            </Alert.Content>
          </Alert.Root>
        )}

        {answer.insufficient_evidence && (
          <Alert.Root status="info">
            <Alert.Indicator />
            <Alert.Content>
              <Alert.Title>Insufficient evidence</Alert.Title>
              <Alert.Description>{answer.answer_text}</Alert.Description>
            </Alert.Content>
          </Alert.Root>
        )}

        {!answer.insufficient_evidence && (
          <Text whiteSpace="pre-wrap">{answer.answer_text}</Text>
        )}

        <Text fontSize="sm" color="gray.600">
          Confidence: {(answer.confidence * 100).toFixed(0)}%
        </Text>

        <SourceReferences caseId={caseId} sources={answer.source_references} />
      </Stack>
    </Box>
  );
}
