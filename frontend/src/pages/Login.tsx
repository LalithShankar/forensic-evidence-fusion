import {
  Box,
  Button,
  Field,
  Heading,
  Input,
  Stack,
  Text,
} from "@chakra-ui/react";
import { FormEvent, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

export function LoginPage() {
  const { isAuthenticated, isLoading, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const redirectPath =
    (location.state as { from?: { pathname?: string } } | null)?.from
      ?.pathname ?? "/";

  if (isAuthenticated) {
    return <Navigate to={redirectPath} replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      await login(email, password);
      navigate(redirectPath, { replace: true });
    } catch {
      setError("Invalid email or password");
    }
  }

  return (
    <Box maxW="md" mx="auto" mt={16}>
      <Heading size="lg" mb={6}>
        Sign in
      </Heading>
      <form onSubmit={(event) => void handleSubmit(event)}>
        <Stack gap={4}>
          <Field.Root required>
            <Field.Label>Email</Field.Label>
            <Input
              type="email"
              autoComplete="username"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </Field.Root>
          <Field.Root required>
            <Field.Label>Password</Field.Label>
            <Input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </Field.Root>
          {error && (
            <Text color="red.500" role="alert">
              {error}
            </Text>
          )}
          <Button type="submit" colorPalette="blue" loading={isLoading}>
            Sign in
          </Button>
        </Stack>
      </form>
    </Box>
  );
}
