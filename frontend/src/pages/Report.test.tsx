import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ReportPage } from "./Report";
import { configureApiClientAuth } from "../lib/apiClient";
import { renderWithProviders } from "../test/renderWithProviders";

const caseId = "22222222-2222-2222-2222-222222222222";
const reportId = "33333333-3333-3333-3333-333333333333";

const authenticatedUser = {
  id: "11111111-1111-1111-1111-111111111111",
  email: "analyst@local.dev",
  display_name: "Local Analyst",
  role: "analyst" as const,
  status: "active" as const,
};

describe("ReportPage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    configureApiClientAuth(() => null);
  });

  it("renders and generates a report draft", async () => {
    configureApiClientAuth(() => "test-token");
    const reportPayload = {
      id: reportId,
      case_id: caseId,
      title: "Case report — Smoke",
      status: "draft",
      content_json: {
        version: 1,
        generated_at: "2026-06-11T12:00:00Z",
        summary: "0 timeline events, 0 claims, 0 unresolved.",
        sections: [
          {
            key: "timeline_summary",
            title: "Timeline summary",
            content: { event_count: 0 },
          },
        ],
      },
      created_at: "2026-06-11T12:00:00Z",
      updated_at: "2026-06-11T12:00:00Z",
    };
    let listReports: unknown[] = [];

    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.includes("/reports/generate") && init?.method === "POST") {
          listReports = [reportPayload];
          return { ok: true, json: async () => reportPayload };
        }
        if (url.includes("/reports") && (!init?.method || init.method === "GET")) {
          return { ok: true, json: async () => listReports };
        }
        return { ok: false, status: 404, json: async () => ({ detail: "Not found" }) };
      }),
    );

    const user = userEvent.setup();
    renderWithProviders(
      <Routes>
        <Route path="/cases/:caseId/report" element={<ReportPage />} />
      </Routes>,
      {
        routerProps: { initialEntries: [`/cases/${caseId}/report`] },
        authProps: {
          initialToken: "test-token",
          initialUser: authenticatedUser,
        },
      },
    );

    expect(screen.getByRole("heading", { name: /report draft/i })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /generate draft/i }));

    await waitFor(() => {
      expect(screen.getByText(/Case report — Smoke/)).toBeInTheDocument();
    });
  });
});
