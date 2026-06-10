import { render, screen } from "@testing-library/react";
import { ChakraProvider, defaultSystem } from "@chakra-ui/react";
import { describe, expect, it } from "vitest";

import App from "./App";

describe("App", () => {
  it("renders the platform title", () => {
    render(
      <ChakraProvider value={defaultSystem}>
        <App />
      </ChakraProvider>,
    );

    expect(
      screen.getByRole("heading", { name: /forensic evidence fusion/i }),
    ).toBeInTheDocument();
  });
});
