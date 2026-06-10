/**
 * UI smoke test: key Epic 10–11 routes render and accept primary actions
 * with mocked API responses (no live backend required).
 */
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CaseUploadPage } from "../pages/CaseUpload";
import { ReviewQueuePage } from "../pages/ReviewQueue";
import { configureApiClientAuth } from "../lib/apiClient";
import { makeArtifact } from "../test/fixtures";
import { renderWithProviders } from "../test/renderWithProviders";

const caseId = "22222222-2222-2222-2222-222222222222";

const user = {
  id: "11111111-1111-1111-1111-111111111111",
  email: "analyst@local.dev",
  display_name: "Local Analyst",
  role: "analyst" as const,
  status: "active" as const,
};

const authProps = { initialToken: "test-token", initialUser: user };

describe("Pipeline UI smoke (Epics 10–11)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    configureApiClientAuth(() => null);
  });

  it("smoke: upload page lists artifacts and bulk upload succeeds", async () => {
    configureApiClientAuth(() => "test-token");
    const artifact = makeArtifact({
      original_filename: "ledger.csv",
      upload_batch_id: "44444444-4444-4444-4444-444444444444",
      suggested_source_group: "Generic",
      classification_confidence: 0.75,
    });

    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => [artifact] })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          upload_batch_id: "44444444-4444-4444-4444-444444444444",
          succeeded_count: 1,
          failed_count: 0,
          results: [
            { filename: "ledger.csv", artifact, error: null },
          ],
        }),
      })
      .mockResolvedValueOnce({ ok: true, json: async () => [artifact] });
    vi.stubGlobal("fetch", fetchMock);

    renderWithProviders(
      <Routes>
        <Route path="/cases/:caseId/upload" element={<CaseUploadPage />} />
      </Routes>,
      {
        routerProps: { initialEntries: [`/cases/${caseId}/upload`] },
        authProps,
      },
    );

    expect(await screen.findByText("ledger.csv")).toBeInTheDocument();
    expect(screen.getByText(/Batch 44444444/)).toBeInTheDocument();

    const bulkSection = screen.getByRole("region", { name: /bulk upload/i });
    const fileInput = within(bulkSection).getByLabelText(/evidence files/i);
    const uploader = userEvent.setup();
    await uploader.upload(
      fileInput,
      new File(["a,b"], "ledger.csv", { type: "text/csv" }),
    );
    await uploader.click(screen.getByRole("button", { name: /upload batch/i }));

    await waitFor(() => {
      expect(screen.getByText(/1 succeeded, 0 failed/i)).toBeInTheDocument();
    });
  });

  it("smoke: review queue shows item and approve action fires", async () => {
    configureApiClientAuth(() => "test-token");
    const reviewArtifact = makeArtifact({
      original_filename: "mystery.bin",
      status: "needs_review",
      classification_confidence: 0.25,
    });

    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          total: 1,
          items: [
            {
              artifact: reviewArtifact,
              review_reason: "No matching classification rule",
              suggested_category: "unknown / unknown",
            },
          ],
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          artifact: { ...reviewArtifact, status: "ready_for_transformation" },
          message: "Artifact approved for transformation.",
        }),
      });
    vi.stubGlobal("fetch", fetchMock);

    renderWithProviders(
      <Routes>
        <Route path="/cases/:caseId/review" element={<ReviewQueuePage />} />
      </Routes>,
      {
        routerProps: { initialEntries: [`/cases/${caseId}/review`] },
        authProps,
      },
    );

    expect(await screen.findByText("mystery.bin")).toBeInTheDocument();

    const uploader = userEvent.setup();
    await uploader.click(screen.getByRole("button", { name: /^approve$/i }));

    await waitFor(() => {
      const patchCalls = fetchMock.mock.calls.filter(
        (call) => (call[1] as RequestInit | undefined)?.method === "PATCH",
      );
      expect(patchCalls.length).toBeGreaterThanOrEqual(1);
      const patchCall = patchCalls[0];
      expect(String(patchCall[0])).toContain("/review-queue/");
      const body = JSON.parse(patchCall[1]?.body as string);
      expect(body.action).toBe("approve");
    });
  });
});
