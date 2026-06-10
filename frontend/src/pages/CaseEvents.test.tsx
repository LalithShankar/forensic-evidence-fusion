import { screen } from "@testing-library/react";
import { Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CaseEventsPage } from "./CaseEvents";
import { TimelinePage } from "./Timeline";
import { configureApiClientAuth } from "../lib/apiClient";
import { renderWithProviders } from "../test/renderWithProviders";

const caseId = "22222222-2222-2222-2222-222222222222";

const authenticatedUser = {
  id: "11111111-1111-1111-1111-111111111111",
  email: "analyst@local.dev",
  display_name: "Local Analyst",
  role: "analyst" as const,
  status: "active" as const,
};

describe("CaseEventsPage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    configureApiClientAuth(() => null);
  });

  it("redirects legacy events route to timeline", async () => {
    configureApiClientAuth(() => "test-token");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => [],
      }),
    );

    renderWithProviders(
      <Routes>
        <Route path="/cases/:caseId/events" element={<CaseEventsPage />} />
        <Route path="/cases/:caseId/timeline" element={<TimelinePage />} />
      </Routes>,
      {
        routerProps: { initialEntries: [`/cases/${caseId}/events`] },
        authProps: {
          initialToken: "test-token",
          initialUser: authenticatedUser,
        },
      },
    );

    expect(await screen.findByRole("heading", { name: /timeline/i }))
      .toBeInTheDocument();
  });
});
