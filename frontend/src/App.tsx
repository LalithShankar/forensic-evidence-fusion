import { Box, Heading, Text } from "@chakra-ui/react";

import { loadConfig } from "./config";

export default function App() {
  const config = loadConfig();

  return (
    <Box p={8}>
      <Heading size="lg">Forensic Evidence Fusion</Heading>
      <Text mt={4}>Environment: {config.appEnv}</Text>
      <Text>API: {config.apiBaseUrl}</Text>
    </Box>
  );
}
