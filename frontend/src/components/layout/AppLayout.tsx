import { Box, Container, Flex, Heading, Link } from "@chakra-ui/react";
import { Link as RouterLink, Outlet } from "react-router-dom";

export function AppLayout() {
  return (
    <Box minH="100vh" bg="gray.50">
      <Box as="header" bg="white" borderBottomWidth="1px" py={4}>
        <Container maxW="container.xl">
          <Flex align="center" gap={6}>
            <Heading size="md">
              <Link asChild variant="plain">
                <RouterLink to="/">Forensic Evidence Fusion</RouterLink>
              </Link>
            </Heading>
            <Flex gap={4} as="nav" aria-label="Main navigation">
              <Link asChild variant="plain">
                <RouterLink to="/">Dashboard</RouterLink>
              </Link>
            </Flex>
          </Flex>
        </Container>
      </Box>
      <Container maxW="container.xl" py={8} as="main">
        <Outlet />
      </Container>
    </Box>
  );
}
