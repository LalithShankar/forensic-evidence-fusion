import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { StructuredDatasetPanel } from "./StructuredDatasetPanel";
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

describe("StructuredDatasetPanel", () => {
  it("shows dataset preview with confidence", async () => {
    configureApiClientAuth(() => "test-token");
    const user = userEvent.setup();
    const dataset = {
      id: "44444444-4444-4444-4444-444444444444",
      artifact_id: artifactId,
      transformation_id: "55555555-5555-5555-5555-555555555555",
      dataset_type: "csv",
      storage_path: "structured/path.json",
      row_count: 2,
      schema_version: "1.0",
      confidence: 0.82,
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
          if (url.includes("/preview")) {
            return {
              dataset_id: dataset.id,
              dataset_type: "csv",
              confidence: 0.82,
              row_count: 2,
              preview_rows: [{ a: "1", b: "2" }],
              preview_json: null,
              truncated: false,
              total_rows: 2,
            };
          }
          return [dataset];
        },
      })),
    );

    renderWithProviders(
      <StructuredDatasetPanel caseId={caseId} artifactId={artifactId} />,
      {
        authProps: {
          initialToken: "test-token",
          initialUser: authenticatedUser,
        },
      },
    );

    await user.click(screen.getByRole("button", { name: "Structured data" }));
    expect(await screen.findByText(/confidence 82%/i)).toBeInTheDocument();
    expect(screen.getByText(/"a": "1"/)).toBeInTheDocument();
  });
});
