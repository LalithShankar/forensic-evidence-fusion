import { screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { OperationsPage } from "./Operations";
import { configureApiClientAuth } from "../lib/apiClient";
import { renderWithProviders } from "../test/renderWithProviders";

const managerUser = {
  id: "11111111-1111-1111-1111-111111111111",
  email: "manager@local.dev",
  display_name: "Case Manager",
  role: "case_manager" as const,
  status: "active" as const,
};

describe("OperationsPage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    configureApiClientAuth(() => null);
  });

  it("renders operations counts", async () => {
    configureApiClientAuth(() => "test-token");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          cases_count: 2,
          artifacts: { failed: 1, blocked: 0, needs_review: 3, other: 5 },
          transformations: {
            running: 0,
            failed: 1,
            blocked: 0,
            completed: 4,
          },
          search_chunks: { failed: 0, pending: 2, indexed: 10 },
        }),
      }),
    );

    renderWithProviders(<OperationsPage />, {
      authProps: {
        initialToken: "test-token",
        initialUser: managerUser,
      },
    });

    await waitFor(() => {
      expect(screen.getByText("Failed artifacts")).toBeInTheDocument();
    });
    expect(screen.getAllByText("1").length).toBeGreaterThan(0);
  });
});
