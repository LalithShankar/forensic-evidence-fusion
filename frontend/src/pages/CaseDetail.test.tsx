import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CaseDetailPage } from "./CaseDetail";
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
  name: "Detail Case",
  description: "Notes",
  scenario_type: "money_laundering" as const,
  date_range_start: "2025-06-01",
  date_range_end: "2025-12-31",
  created_by: authenticatedUser.id,
  created_at: "2026-06-01T10:00:00Z",
  updated_at: "2026-06-01T10:00:00Z",
};

function renderCaseDetail(initialEntry: string) {
  renderWithProviders(
    <Routes>
      <Route path="/cases/:caseId" element={<CaseDetailPage />} />
    </Routes>,
    {
      routerProps: { initialEntries: [initialEntry] },
      authProps: {
        initialToken: "test-token",
        initialUser: authenticatedUser,
      },
    },
  );
}

describe("CaseDetailPage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    configureApiClientAuth(() => null);
  });

  it("shows case metadata on the detail page", async () => {
    configureApiClientAuth(() => "test-token");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => sampleCase,
      }),
    );

    renderCaseDetail("/cases/22222222-2222-2222-2222-222222222222");

    expect(await screen.findByRole("heading", { name: /detail case/i })).toBeInTheDocument();
    expect(screen.getByText(/notes/i)).toBeInTheDocument();
    expect(screen.getByText(/2025-06-01/)).toBeInTheDocument();
    expect(screen.getByText(/scenario: money laundering/i)).toBeInTheDocument();
  });

  it("saves updated case values", async () => {
    configureApiClientAuth(() => "test-token");
    const updatedCase = {
      ...sampleCase,
      name: "Updated Case",
      updated_at: "2026-06-02T10:00:00Z",
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => sampleCase,
      })
      .mockResolvedValue({
        ok: true,
        json: async () => updatedCase,
      });
    vi.stubGlobal("fetch", fetchMock);

    const user = userEvent.setup();
    renderCaseDetail("/cases/22222222-2222-2222-2222-222222222222");

    const nameInput = await screen.findByLabelText(/^name$/i);
    await user.clear(nameInput);
    await user.type(nameInput, "Updated Case");
    await user.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/cases/22222222-2222-2222-2222-222222222222",
        expect.objectContaining({ method: "PATCH" }),
      );
    });
    expect(await screen.findByRole("status")).toHaveTextContent(/changes saved/i);
  });

  it("shows a safe not-found state for inaccessible cases", async () => {
    configureApiClientAuth(() => "test-token");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: async () => ({ detail: "Case not found" }),
      }),
    );

    renderCaseDetail("/cases/00000000-0000-0000-0000-000000000099");

    expect(await screen.findByRole("heading", { name: /case not found/i })).toBeInTheDocument();
    expect(
      screen.getByText(/does not exist or you do not have permission/i),
    ).toBeInTheDocument();
  });
});
