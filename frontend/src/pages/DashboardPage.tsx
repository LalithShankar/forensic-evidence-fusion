import { Box, Heading, Link, Text } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { apiClient } from "../lib/apiClient";
import { loadConfig } from "../config";

export function DashboardPage() {
  const config = loadConfig();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health", config.apiBaseUrl],
    queryFn: () => apiClient.fetchHealth(),
  });

  return (
    <Box>
      <Heading size="lg">Dashboard</Heading>
      <Text mt={4}>Environment: {config.appEnv}</Text>
      <Text>API: {config.apiBaseUrl}</Text>
      {isLoading && <Text mt={4}>Checking backend health…</Text>}
      {isError && (
        <Text mt={4} color="red.500">
          Backend unreachable
        </Text>
      )}
      {data && <Text mt={4}>Backend status: {data.status}</Text>}
      <Link asChild mt={6} display="inline-block" colorPalette="blue">
        <RouterLink to="/operations">Platform operations →</RouterLink>
      </Link>
    </Box>
  );
}
