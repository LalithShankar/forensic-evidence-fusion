import { screen, waitFor } from "@testing-library/react";
import { Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ReviewQueuePage } from "./ReviewQueue";
import { configureApiClientAuth } from "../lib/apiClient";
import { makeArtifact } from "../test/fixtures";
import { renderWithProviders } from "../test/renderWithProviders";

const caseId = "22222222-2222-2222-2222-222222222222";

const authenticatedUser = {
  id: "11111111-1111-1111-1111-111111111111",
  email: "analyst@local.dev",
  display_name: "Local Analyst",
  role: "analyst" as const,
  status: "active" as const,
};

function renderReviewQueue() {
  renderWithProviders(
    <Routes>
      <Route path="/cases/:caseId/review" element={<ReviewQueuePage />} />
    </Routes>,
    {
      routerProps: { initialEntries: [`/cases/${caseId}/review`] },
      authProps: { initialToken: "test-token", initialUser: authenticatedUser },
    },
  );
}

describe("ReviewQueuePage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    configureApiClientAuth(() => null);
  });

  it("shows empty state when nothing needs review", async () => {
    configureApiClientAuth(() => "test-token");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({ items: [], total: 0 }),
      }),
    );

    renderReviewQueue();

    expect(
      await screen.findByLabelText(/empty review queue/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/all clear/i)).toBeInTheDocument();
  });

  it("lists a low-confidence item with suggestion and reason", async () => {
    configureApiClientAuth(() => "test-token");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          total: 1,
          items: [
            {
              artifact: makeArtifact({
                original_filename: "mystery.bin",
                status: "needs_review",
                classification_confidence: 0.25,
              }),
              review_reason: "Low classification confidence",
              suggested_category: "unknown / unknown",
            },
          ],
        }),
      }),
    );

    renderReviewQueue();

    expect(await screen.findByText("mystery.bin")).toBeInTheDocument();
    expect(
      screen.getByText(/Reason: Low classification confidence/),
    ).toBeInTheDocument();
  });

  it("surfaces blocker notes for blocked artifacts", async () => {
    configureApiClientAuth(() => "test-token");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          total: 1,
          items: [
            {
              artifact: makeArtifact({
                original_filename: "blocked.bin",
                status: "blocked",
                blocker_notes: "Checksum mismatch detected",
              }),
              review_reason: "Checksum mismatch detected",
              suggested_category: "Blocked",
            },
          ],
        }),
      }),
    );

    renderReviewQueue();

    await waitFor(() => {
      expect(
        screen.getByText(/Blocker: Checksum mismatch detected/),
      ).toBeInTheDocument();
    });
  });
});
