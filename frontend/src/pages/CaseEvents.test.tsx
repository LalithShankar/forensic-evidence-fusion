import { screen } from "@testing-library/react";
import { Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CaseEventsPage } from "./CaseEvents";
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

  it("renders event list from API", async () => {
    configureApiClientAuth(() => "test-token");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => [
          {
            id: "33333333-3333-3333-3333-333333333333",
            case_id: caseId,
            artifact_id: "44444444-4444-4444-4444-444444444444",
            transformation_id: null,
            structured_dataset_id: null,
            event_type: "message_sent",
            event_subtype: "structured_row",
            original_timestamp_text: "Tuesday",
            normalized_timestamp: null,
            title: "Message from Bob",
            description: "Hello",
            payload_json: {},
            source_confidence: 0.45,
            provenance_pointer: "structured_dataset:x:row:0",
            review_status: "pending",
            created_at: "2026-06-11T10:00:00Z",
            updated_at: "2026-06-11T10:00:00Z",
          },
        ],
      }),
    );

    renderWithProviders(
      <Routes>
        <Route path="/cases/:caseId/events" element={<CaseEventsPage />} />
      </Routes>,
      {
        routerProps: { initialEntries: [`/cases/${caseId}/events`] },
        authProps: {
          initialToken: "test-token",
          initialUser: authenticatedUser,
        },
      },
    );

    expect(await screen.findByText("Message from Bob")).toBeInTheDocument();
    expect(screen.getByText(/confidence 45%/i)).toBeInTheDocument();
  });
});
