import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ReadablePreviewPanel } from "./ReadablePreviewPanel";
import { configureApiClientAuth } from "../../lib/apiClient";
import { renderWithProviders } from "../../test/renderWithProviders";

const caseId = "22222222-2222-2222-2222-222222222222";
const artifactId = "33333333-3333-3333-3333-333333333333";

const authenticatedUser = {
  id: "11111111-1111-1111-1111-111111111111",
  email: "analyst@local.dev",
  display_name: "Local Analyst",
  role: "analyst" as const,
  status: "active" as const,
};

describe("ReadablePreviewPanel", () => {
  it("shows unavailable state when no readable views exist", async () => {
    configureApiClientAuth(() => "test-token");
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => [],
      }),
    );

    renderWithProviders(
      <ReadablePreviewPanel caseId={caseId} artifactId={artifactId} />,
      {
        authProps: {
          initialToken: "test-token",
          initialUser: authenticatedUser,
        },
      },
    );

    await user.click(screen.getByRole("button", { name: "Preview" }));
    expect(
      await screen.findByText(/No readable preview is available/i),
    ).toBeInTheDocument();
  });

  it("shows preview content when a readable view exists", async () => {
    configureApiClientAuth(() => "test-token");
    const user = userEvent.setup();
    const view = {
      id: "44444444-4444-4444-4444-444444444444",
      artifact_id: artifactId,
      transformation_id: "55555555-5555-5555-5555-555555555555",
      view_type: "extracted_text",
      storage_path: "readable/path.txt",
      status: "generated",
      error_notes: null,
      created_at: "2026-06-11T10:00:00Z",
      updated_at: "2026-06-11T10:00:00Z",
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (url: string) => ({
        ok: true,
        json: async () => {
          if (url.includes("/content")) {
            return {
              view_id: view.id,
              view_type: "extracted_text",
              content_type: "text/plain",
              content: "CSV summary for ledger.csv",
              truncated: false,
            };
          }
          return [view];
        },
      })),
    );

    renderWithProviders(
      <ReadablePreviewPanel caseId={caseId} artifactId={artifactId} />,
      {
        authProps: {
          initialToken: "test-token",
          initialUser: authenticatedUser,
        },
      },
    );

    await user.click(screen.getByRole("button", { name: "Preview" }));
    expect(
      await screen.findByText("CSV summary for ledger.csv"),
    ).toBeInTheDocument();
  });
});
