import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import App from "./App";
import { renderWithProviders } from "./test/renderWithProviders";

const authenticatedUser = {
  id: "11111111-1111-1111-1111-111111111111",
  email: "analyst@local.dev",
  display_name: "Local Analyst",
  role: "analyst" as const,
  status: "active" as const,
};

describe("routing", () => {
  it("renders base routes without full page reload", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          status: "ok",
          app_env: "local",
          secrets_source: "dotenv",
        }),
      }),
    );

    const user = userEvent.setup();
    renderWithProviders(<App />, {
      routerProps: { initialEntries: ["/"] },
      authProps: {
        initialToken: "test-token",
        initialUser: authenticatedUser,
      },
    });

    expect(
      screen.getByRole("heading", { name: /dashboard/i }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: /dashboard/i }));

    expect(
      screen.getByRole("heading", { name: /dashboard/i }),
    ).toBeInTheDocument();
    expect(screen.queryByText(/page not found/i)).not.toBeInTheDocument();
  });

  it("shows a not-found page for unknown routes", () => {
    renderWithProviders(<App />, {
      routerProps: { initialEntries: ["/unknown-route"] },
      authProps: {
        initialToken: "test-token",
        initialUser: authenticatedUser,
      },
    });

    expect(
      screen.getByRole("heading", { name: /page not found/i }),
    ).toBeInTheDocument();
  });
});
