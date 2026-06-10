import { screen, waitFor } from "@testing-library/react";
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

describe("App", () => {
  it("renders the dashboard landing page for authenticated users", async () => {
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
    await waitFor(() => {
      expect(screen.getByText(/backend status: ok/i)).toBeInTheDocument();
    });
  });

  it("redirects unauthenticated users to login", () => {
    renderWithProviders(<App />, {
      routerProps: { initialEntries: ["/"] },
    });

    expect(
      screen.getByRole("heading", { name: /sign in/i }),
    ).toBeInTheDocument();
  });
});
