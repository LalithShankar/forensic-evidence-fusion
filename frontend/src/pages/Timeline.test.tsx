import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TimelinePage } from "./Timeline";
import { configureApiClientAuth } from "../lib/apiClient";
import { renderWithProviders } from "../test/renderWithProviders";

const caseId = "22222222-2222-2222-2222-222222222222";
const eventAId = "33333333-3333-3333-3333-333333333333";
const eventBId = "44444444-4444-4444-4444-444444444444";

const authenticatedUser = {
  id: "11111111-1111-1111-1111-111111111111",
  email: "analyst@local.dev",
  display_name: "Local Analyst",
  role: "analyst" as const,
  status: "active" as const,
};

const sampleEvents = [
  {
    id: eventAId,
    case_id: caseId,
    artifact_id: "55555555-5555-5555-5555-555555555555",
    transformation_id: null,
    structured_dataset_id: null,
    event_type: "message_sent",
    event_subtype: "structured_row",
    original_timestamp_text: "2024-06-01",
    normalized_timestamp: "2024-06-01T10:00:00Z",
    title: "Message from Alice",
    description: "Transfer confirmed",
    payload_json: { sender: "Alice", message: "Transfer confirmed" },
    source_confidence: 0.85,
    provenance_pointer: "structured_dataset:x:row:0",
    review_status: "pending" as const,
    source_group: "ThirdParty",
    created_at: "2026-06-11T10:00:00Z",
    updated_at: "2026-06-11T10:00:00Z",
  },
  {
    id: eventBId,
    case_id: caseId,
    artifact_id: "66666666-6666-6666-6666-666666666666",
    transformation_id: null,
    structured_dataset_id: null,
    event_type: "transaction_observed",
    event_subtype: "generic",
    original_timestamp_text: "2024-06-02",
    normalized_timestamp: "2024-06-02T12:00:00Z",
    title: "Transaction row 1",
    description: "50.00",
    payload_json: { amount: "50.00" },
    source_confidence: 0.7,
    provenance_pointer: "structured_dataset:y:row:0",
    review_status: "reviewed" as const,
    source_group: "Bank",
    created_at: "2026-06-11T11:00:00Z",
    updated_at: "2026-06-11T11:00:00Z",
  },
];

function mockTimelineFetch(events: typeof sampleEvents = sampleEvents) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes(`/cases/${caseId}/events/${eventAId}`)) {
        return {
          ok: true,
          json: async () => sampleEvents[0],
        };
      }
      if (url.includes(`/cases/${caseId}/events?`)) {
        const parsed = new URL(url, "http://localhost");
        const eventType = parsed.searchParams.get("event_type");
        const filtered = eventType
          ? events.filter((event) => event.event_type === eventType)
          : events;
        return {
          ok: true,
          json: async () => filtered,
        };
      }
      if (url.endsWith(`/cases/${caseId}/events`)) {
        return {
          ok: true,
          json: async () => events,
        };
      }
      return {
        ok: false,
        status: 404,
        json: async () => ({ detail: "Not found" }),
      };
    }),
  );
}

describe("TimelinePage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    configureApiClientAuth(() => null);
  });

  it("renders empty state guidance when no events exist", async () => {
    configureApiClientAuth(() => "test-token");
    mockTimelineFetch([]);

    renderWithProviders(
      <Routes>
        <Route path="/cases/:caseId/timeline" element={<TimelinePage />} />
      </Routes>,
      {
        routerProps: { initialEntries: [`/cases/${caseId}/timeline`] },
        authProps: {
          initialToken: "test-token",
          initialUser: authenticatedUser,
        },
      },
    );

    expect(await screen.findByLabelText("Empty timeline")).toBeInTheDocument();
    expect(
      screen.getByText(/transform artifacts to generate structured datasets/i),
    ).toBeInTheDocument();
  });

  it("filters events by event type", async () => {
    configureApiClientAuth(() => "test-token");
    mockTimelineFetch();
    const user = userEvent.setup();

    renderWithProviders(
      <Routes>
        <Route path="/cases/:caseId/timeline" element={<TimelinePage />} />
      </Routes>,
      {
        routerProps: { initialEntries: [`/cases/${caseId}/timeline`] },
        authProps: {
          initialToken: "test-token",
          initialUser: authenticatedUser,
        },
      },
    );

    expect(await screen.findByText("Message from Alice")).toBeInTheDocument();
    expect(screen.getByText("Transaction row 1")).toBeInTheDocument();

    await user.selectOptions(
      screen.getByLabelText("Event type"),
      "message_sent",
    );

    await waitFor(() => {
      expect(screen.getByText("Message from Alice")).toBeInTheDocument();
      expect(screen.queryByText("Transaction row 1")).not.toBeInTheDocument();
    });
  });

  it("shows detail panel after selecting an event", async () => {
    configureApiClientAuth(() => "test-token");
    mockTimelineFetch();
    const user = userEvent.setup();

    renderWithProviders(
      <Routes>
        <Route path="/cases/:caseId/timeline" element={<TimelinePage />} />
      </Routes>,
      {
        routerProps: { initialEntries: [`/cases/${caseId}/timeline`] },
        authProps: {
          initialToken: "test-token",
          initialUser: authenticatedUser,
        },
      },
    );

    await user.click(await screen.findByText("Message from Alice"));

    expect(await screen.findByText(/payload summary/i)).toBeInTheDocument();
    expect(screen.getByText(/sender: Alice/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /view source artifact/i }))
      .toHaveAttribute(
        "href",
        `/cases/${caseId}/artifacts/55555555-5555-5555-5555-555555555555`,
      );
  });
});
