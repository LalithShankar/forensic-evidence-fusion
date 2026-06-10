import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CasesPage } from "./Cases";
import { configureApiClientAuth } from "../lib/apiClient";
import { renderWithProviders } from "../test/renderWithProviders";

const authenticatedUser = {
  id: "11111111-1111-1111-1111-111111111111",
  email: "analyst@local.dev",
  display_name: "Local Analyst",
  role: "analyst" as const,
  status: "active" as const,
};

const sampleCase = {
  id: "22222222-2222-2222-2222-222222222222",
  name: "Insider Review",
  description: "Q1 review",
  scenario_type: "insider_trading" as const,
  date_range_start: "2026-01-01",
  date_range_end: "2026-03-31",
  created_by: authenticatedUser.id,
  created_at: "2026-06-01T10:00:00Z",
  updated_at: "2026-06-01T10:00:00Z",
};

describe("CasesPage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    configureApiClientAuth(() => null);
  });

  it("lists accessible cases", async () => {
    configureApiClientAuth(() => "test-token");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => [sampleCase],
      }),
    );

    renderWithProviders(<CasesPage />, {
      authProps: {
        initialToken: "test-token",
        initialUser: authenticatedUser,
      },
    });

    const listSection = await screen.findByRole("region", { name: /case list/i });
    expect(await screen.findByText("Insider Review")).toBeInTheDocument();
    expect(listSection).toHaveTextContent(/insider trading/i);
  });

  it("shows validation errors from the API", async () => {
    configureApiClientAuth(() => "test-token");
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 422,
        json: async () => ({
          detail: [{ loc: ["body", "name"], msg: "String should have at least 1 character", type: "string_too_short" }],
        }),
      });
    vi.stubGlobal("fetch", fetchMock);

    const user = userEvent.setup();
    renderWithProviders(<CasesPage />, {
      authProps: {
        initialToken: "test-token",
        initialUser: authenticatedUser,
      },
    });

    await screen.findByText(/no cases yet/i);
    await user.click(screen.getByRole("button", { name: /create case/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/name:/i);
  });

  it("creates a case and refreshes the list", async () => {
    configureApiClientAuth(() => "test-token");
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => sampleCase,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [sampleCase],
      });
    vi.stubGlobal("fetch", fetchMock);

    const user = userEvent.setup();
    renderWithProviders(<CasesPage />, {
      authProps: {
        initialToken: "test-token",
        initialUser: authenticatedUser,
      },
    });

    await screen.findByText(/no cases yet/i);
    await user.type(screen.getByLabelText(/^name$/i), "Insider Review");
    await user.click(screen.getByRole("button", { name: /create case/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/cases",
        expect.objectContaining({ method: "POST" }),
      );
    });
  });
});
