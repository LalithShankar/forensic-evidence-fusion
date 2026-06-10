import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import App from "./App";
import { renderWithProviders } from "./test/renderWithProviders";

describe("App", () => {
  it("renders the dashboard landing page", async () => {
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

    renderWithProviders(<App />);

    expect(
      screen.getByRole("heading", { name: /dashboard/i }),
    ).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/backend status: ok/i)).toBeInTheDocument();
    });
  });
});
