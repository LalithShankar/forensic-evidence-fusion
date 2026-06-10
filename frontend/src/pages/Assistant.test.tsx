import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AssistantPage } from "./Assistant";
import { configureApiClientAuth } from "../lib/apiClient";
import { renderWithProviders } from "../test/renderWithProviders";

const caseId = "22222222-2222-2222-2222-222222222222";
const artifactId = "55555555-5555-5555-5555-555555555555";

const authenticatedUser = {
  id: "11111111-1111-1111-1111-111111111111",
  email: "analyst@local.dev",
  display_name: "Local Analyst",
  role: "analyst" as const,
  status: "active" as const,
};

describe("AssistantPage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    configureApiClientAuth(() => null);
  });

  it("shows grounded answer with source links", async () => {
    configureApiClientAuth(() => "test-token");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith("/assistant/ask") && init?.method === "POST") {
          return {
            ok: true,
            json: async () => ({
              answer_text: "Alice confirmed the transfer.",
              confidence: 0.82,
              limitation_text: null,
              insufficient_evidence: false,
              source_references: [
                {
                  chunk_id: "88888888-8888-8888-8888-888888888888",
                  artifact_id: artifactId,
                  event_id: null,
                  provenance_pointer: "readable_view:x",
                  source_group: "Bank",
                },
              ],
              log_id: "99999999-9999-9999-9999-999999999999",
            }),
          };
        }
        return { ok: false, status: 404, json: async () => ({ detail: "Not found" }) };
      }),
    );

    const user = userEvent.setup();
    renderWithProviders(
      <Routes>
        <Route path="/cases/:caseId/assistant" element={<AssistantPage />} />
      </Routes>,
      {
        routerProps: { initialEntries: [`/cases/${caseId}/assistant`] },
        authProps: {
          initialToken: "test-token",
          initialUser: authenticatedUser,
        },
      },
    );

    await user.type(
      await screen.findByPlaceholderText(/what evidence mentions/i),
      "What did Alice transfer?",
    );
    await user.click(screen.getByRole("button", { name: /ask assistant/i }));

    await waitFor(() => {
      expect(screen.getByText(/Alice confirmed the transfer/i)).toBeInTheDocument();
    });
    expect(
      screen.getByRole("link", { name: new RegExp(`Artifact ${artifactId}`) }),
    ).toHaveAttribute("href", `/cases/${caseId}/artifacts/${artifactId}`);
  });

  it("shows insufficient evidence response", async () => {
    configureApiClientAuth(() => "test-token");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          answer_text: "Insufficient evidence in this case to answer that question.",
          confidence: 0,
          limitation_text: "No relevant indexed chunks matched the question.",
          insufficient_evidence: true,
          source_references: [],
          log_id: "99999999-9999-9999-9999-999999999999",
        }),
      }),
    );

    const user = userEvent.setup();
    renderWithProviders(
      <Routes>
        <Route path="/cases/:caseId/assistant" element={<AssistantPage />} />
      </Routes>,
      {
        routerProps: { initialEntries: [`/cases/${caseId}/assistant`] },
        authProps: {
          initialToken: "test-token",
          initialUser: authenticatedUser,
        },
      },
    );

    await user.type(
      screen.getByPlaceholderText(/what evidence mentions/i),
      "Unknown topic",
    );
    await user.click(screen.getByRole("button", { name: /ask assistant/i }));

    expect(
      await screen.findByText("No relevant indexed chunks matched the question."),
    ).toBeInTheDocument();
  });
});
