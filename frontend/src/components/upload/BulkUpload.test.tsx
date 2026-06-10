import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { BulkUpload } from "./BulkUpload";
import { configureApiClientAuth } from "../../lib/apiClient";
import { makeArtifact } from "../../test/fixtures";
import { renderWithProviders } from "../../test/renderWithProviders";

const caseId = "22222222-2222-2222-2222-222222222222";

const authenticatedUser = {
  id: "11111111-1111-1111-1111-111111111111",
  email: "analyst@local.dev",
  display_name: "Local Analyst",
  role: "analyst" as const,
  status: "active" as const,
};

function renderBulkUpload() {
  renderWithProviders(<BulkUpload caseId={caseId} />, {
    authProps: { initialToken: "test-token", initialUser: authenticatedUser },
  });
}

describe("BulkUpload", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    configureApiClientAuth(() => null);
  });

  it("uploads multiple files and shows per-file results with batch summary", async () => {
    configureApiClientAuth(() => "test-token");
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        upload_batch_id: "44444444-4444-4444-4444-444444444444",
        succeeded_count: 2,
        failed_count: 0,
        results: [
          {
            filename: "notes.txt",
            artifact: makeArtifact({ original_filename: "notes.txt" }),
            error: null,
          },
          {
            filename: "data.csv",
            artifact: makeArtifact({
              original_filename: "data.csv",
              suggested_source_group: "Generic",
              suggested_source_family: "Tabular",
              classification_confidence: 0.75,
            }),
            error: null,
          },
        ],
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const user = userEvent.setup();
    renderBulkUpload();

    const fileInput = screen.getByLabelText(/evidence files/i);
    await user.upload(fileInput, [
      new File(["a"], "notes.txt", { type: "text/plain" }),
      new File(["a,b"], "data.csv", { type: "text/csv" }),
    ]);
    await user.click(screen.getByRole("button", { name: /upload batch/i }));

    await waitFor(() => {
      expect(screen.getByText(/2 succeeded, 0 failed/i)).toBeInTheDocument();
    });
    expect(screen.getByText("notes.txt")).toBeInTheDocument();
    expect(screen.getByText("data.csv")).toBeInTheDocument();
  });

  it("shows per-file errors on partial failure", async () => {
    configureApiClientAuth(() => "test-token");
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        upload_batch_id: "44444444-4444-4444-4444-444444444444",
        succeeded_count: 1,
        failed_count: 1,
        results: [
          {
            filename: "good.csv",
            artifact: makeArtifact({ original_filename: "good.csv" }),
            error: null,
          },
          {
            filename: "empty.txt",
            artifact: null,
            error: "File content is required",
          },
        ],
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const user = userEvent.setup();
    renderBulkUpload();

    const fileInput = screen.getByLabelText(/evidence files/i);
    await user.upload(fileInput, [
      new File(["a,b"], "good.csv", { type: "text/csv" }),
      new File([""], "empty.txt", { type: "text/plain" }),
    ]);
    await user.click(screen.getByRole("button", { name: /upload batch/i }));

    await waitFor(() => {
      expect(screen.getByText(/1 succeeded, 1 failed/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/File content is required/i)).toBeInTheDocument();
  });

  it("validates that at least one file is selected", async () => {
    const user = userEvent.setup();
    renderBulkUpload();

    await user.click(screen.getByRole("button", { name: /upload batch/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /choose at least one file/i,
    );
  });
});
