import { Heading, Text } from "@chakra-ui/react";

export function NotFoundPage() {
  return (
    <>
      <Heading size="lg">Page not found</Heading>
      <Text mt={4}>The page you requested does not exist.</Text>
    </>
  );
}
