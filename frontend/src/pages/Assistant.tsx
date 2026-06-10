import {
  Box,
  Button,
  Field,
  Heading,
  Link,
  Stack,
  Text,
  Textarea,
} from "@chakra-ui/react";
import { useMutation } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { Link as RouterLink, useParams } from "react-router-dom";

import { AssistantAnswerPanel } from "../components/assistant/AssistantAnswerPanel";
import { useAuth } from "../context/AuthContext";
import { ApiRequestError, type AssistantAnswerPublic } from "../lib/apiClient";

export function AssistantPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const { client } = useAuth();
  const [question, setQuestion] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [answer, setAnswer] = useState<AssistantAnswerPublic | null>(null);

  const askMutation = useMutation({
    mutationFn: (prompt: string) => client.askAssistant(caseId ?? "", prompt),
    onSuccess: (result) => {
      setFormError(null);
      setAnswer(result);
    },
    onError: (error: unknown) => {
      if (error instanceof ApiRequestError && error.status === 422) {
        setFormError("Unable to process that question.");
        return;
      }
      setFormError("Assistant request failed. Please try again.");
    },
  });

  if (!caseId) {
    return <Text>Missing case identifier.</Text>;
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    if (!question.trim()) {
      setFormError("Enter a question about the case evidence.");
      return;
    }
    askMutation.mutate(question.trim());
  }

  return (
    <Stack gap={6}>
      <Box>
        <Link asChild variant="plain" fontSize="sm" mb={2} display="inline-block">
          <RouterLink to={`/cases/${caseId}`}>← Back to case</RouterLink>
        </Link>
        <Heading size="lg">Evidence assistant</Heading>
        <Text mt={2} color="gray.600">
          Ask questions grounded in indexed evidence for this case only.
        </Text>
      </Box>

      <Box as="section" aria-label="Assistant question form">
        <form noValidate onSubmit={handleSubmit}>
          <Stack gap={4} maxW="2xl">
            <Field.Root required>
              <Field.Label>Question</Field.Label>
              <Textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                rows={4}
                placeholder="What evidence mentions Alice's transfer?"
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
              loading={askMutation.isPending}
            >
              Ask assistant
            </Button>
          </Stack>
        </form>
      </Box>

      <AssistantAnswerPanel
        caseId={caseId}
        answer={answer}
        isLoading={askMutation.isPending}
      />
    </Stack>
  );
}
