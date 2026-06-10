import { Box, Button, Container, Flex, Heading, Link, Text } from "@chakra-ui/react";
import { Link as RouterLink, Outlet } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";

export function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <Box minH="100vh" bg="gray.50">
      <Box as="header" bg="white" borderBottomWidth="1px" py={4}>
        <Container maxW="container.xl">
          <Flex align="center" justify="space-between" gap={6}>
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
                <Link asChild variant="plain">
                  <RouterLink to="/cases">Cases</RouterLink>
                </Link>
              </Flex>
            </Flex>
            {user && (
              <Flex align="center" gap={4}>
                <Text fontSize="sm">{user.display_name}</Text>
                <Button size="sm" variant="outline" onClick={() => void logout()}>
                  Sign out
                </Button>
              </Flex>
            )}
          </Flex>
        </Container>
      </Box>
      <Container maxW="container.xl" py={8} as="main">
        <Outlet />
      </Container>
    </Box>
  );
}
