import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ClaimsPage } from "./Claims";
import { configureApiClientAuth } from "../lib/apiClient";
import { renderWithProviders } from "../test/renderWithProviders";

const caseId = "22222222-2222-2222-2222-222222222222";
const claimId = "77777777-7777-7777-7777-777777777777";

const authenticatedUser = {
  id: "11111111-1111-1111-1111-111111111111",
  email: "analyst@local.dev",
  display_name: "Local Analyst",
  role: "analyst" as const,
  status: "active" as const,
};

const sampleClaim = {
  id: claimId,
  case_id: caseId,
  claim_text: "Alice confirmed the transfer",
  claim_type: "general",
  claimant: "Alice",
  claimed_time_text: "2024-06-01",
  claimed_time_normalized: "2024-06-01T10:00:00Z",
  claimed_people: ["Alice"],
  claim_source: "interview",
  claim_source_artifact_id: null,
  parse_confidence: 0.8,
  created_by: authenticatedUser.id,
  status: "active",
  created_at: "2026-06-11T10:00:00Z",
  updated_at: "2026-06-11T10:00:00Z",
};

describe("ClaimsPage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    configureApiClientAuth(() => null);
  });

  it("shows validation errors without clearing entered text", async () => {
    configureApiClientAuth(() => "test-token");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith(`/cases/${caseId}/claims`) && init?.method === "POST") {
          return {
            ok: false,
            status: 422,
            json: async () => ({
              detail: [{ loc: ["body", "claim_text"], msg: "Field required", type: "value_error" }],
            }),
          };
        }
        if (url.endsWith(`/cases/${caseId}/claims`)) {
          return { ok: true, json: async () => [] };
        }
        return { ok: false, status: 404, json: async () => ({ detail: "Not found" }) };
      }),
    );

    const user = userEvent.setup();
    renderWithProviders(
      <Routes>
        <Route path="/cases/:caseId/claims" element={<ClaimsPage />} />
      </Routes>,
      {
        routerProps: { initialEntries: [`/cases/${caseId}/claims`] },
        authProps: {
          initialToken: "test-token",
          initialUser: authenticatedUser,
        },
      },
    );

    const textarea = await screen.findByLabelText(/claim text/i);
    await user.type(textarea, "Draft claim text");
    await user.click(screen.getByRole("button", { name: /save claim/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/claim_text/i);
    expect(textarea).toHaveValue("Draft claim text");
  });

  it("lists claims with parse confidence", async () => {
    configureApiClientAuth(() => "test-token");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => [sampleClaim],
      }),
    );

    renderWithProviders(
      <Routes>
        <Route path="/cases/:caseId/claims" element={<ClaimsPage />} />
      </Routes>,
      {
        routerProps: { initialEntries: [`/cases/${caseId}/claims`] },
        authProps: {
          initialToken: "test-token",
          initialUser: authenticatedUser,
        },
      },
    );

    expect(await screen.findByText(sampleClaim.claim_text)).toBeInTheDocument();
    expect(screen.getByText(/parse confidence 80%/i)).toBeInTheDocument();
  });
});

describe("ClaimResolutionPanel", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    configureApiClientAuth(() => null);
  });

  it("renders scores and event links after resolution", async () => {
    configureApiClientAuth(() => "test-token");
    const eventId = "33333333-3333-3333-3333-333333333333";

    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.includes("/resolution") && init?.method !== "POST") {
          return {
            ok: false,
            status: 404,
            json: async () => ({ detail: "Not found" }),
          };
        }
        if (url.endsWith("/resolve") && init?.method === "POST") {
          return {
            ok: true,
            json: async () => ({
              id: "88888888-8888-8888-8888-888888888888",
              case_id: caseId,
              claim_id: claimId,
              resolution_status: "completed",
              result_label: "supported",
              support_score: 0.82,
              contradiction_score: 0.1,
              supporting_event_ids: [eventId],
              contradicting_event_ids: [],
              unresolved_reason: null,
              resolution_notes: "Matched 1 supporting and 0 contradicting events.",
              created_at: "2026-06-11T10:00:00Z",
              updated_at: "2026-06-11T10:00:00Z",
            }),
          };
        }
        if (url.endsWith(`/cases/${caseId}/claims`)) {
          return { ok: true, json: async () => [sampleClaim] };
        }
        return { ok: false, status: 404, json: async () => ({ detail: "Not found" }) };
      }),
    );

    const user = userEvent.setup();
    renderWithProviders(
      <Routes>
        <Route path="/cases/:caseId/claims" element={<ClaimsPage />} />
      </Routes>,
      {
        routerProps: { initialEntries: [`/cases/${caseId}/claims`] },
        authProps: {
          initialToken: "test-token",
          initialUser: authenticatedUser,
        },
      },
    );

    await user.click(await screen.findByRole("button", { name: /show resolution/i }));
    await user.click(screen.getByRole("button", { name: /run resolution/i }));

    await waitFor(() => {
      expect(screen.getByText(/support 0.82/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/supported/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: eventId })).toHaveAttribute(
      "href",
      `/cases/${caseId}/timeline?event=${eventId}`,
    );
  });
});
