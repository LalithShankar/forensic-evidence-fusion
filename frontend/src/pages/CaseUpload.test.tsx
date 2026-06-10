import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CaseUploadPage } from "./CaseUpload";
import { configureApiClientAuth } from "../lib/apiClient";
import { renderWithProviders } from "../test/renderWithProviders";

const authenticatedUser = {
  id: "11111111-1111-1111-1111-111111111111",
  email: "analyst@local.dev",
  display_name: "Local Analyst",
  role: "analyst" as const,
  status: "active" as const,
};

const caseId = "22222222-2222-2222-2222-222222222222";

function renderCaseUpload(initialEntry = `/cases/${caseId}/upload`) {
  renderWithProviders(
    <Routes>
      <Route path="/cases/:caseId/upload" element={<CaseUploadPage />} />
    </Routes>,
    {
      routerProps: { initialEntries: [initialEntry] },
      authProps: {
        initialToken: "test-token",
        initialUser: authenticatedUser,
      },
    },
  );
}

const sampleArtifact = {
  id: "33333333-3333-3333-3333-333333333333",
  case_id: caseId,
  original_filename: "report.pdf",
  file_size_bytes: 12,
  file_extension: "pdf",
  mime_type: "application/pdf",
  uploaded_by: authenticatedUser.id,
  uploaded_at: "2026-06-10T10:00:00Z",
  content_hash: "abc123",
  status: "preserved" as const,
  created_at: "2026-06-10T10:00:00Z",
  updated_at: "2026-06-10T10:00:00Z",
};

describe("CaseUploadPage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    configureApiClientAuth(() => null);
  });

  it("shows uploaded artifacts after a successful upload", async () => {
    configureApiClientAuth(() => "test-token");
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => sampleArtifact,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [sampleArtifact],
      });
    vi.stubGlobal("fetch", fetchMock);

    const user = userEvent.setup();
    renderCaseUpload();

    const uploadSection = screen.getByRole("region", {
      name: /upload evidence file/i,
    });
    const fileInput = within(uploadSection).getByLabelText(/evidence file/i);
    const file = new File(["pdf-bytes"], "report.pdf", {
      type: "application/pdf",
    });
    await user.upload(fileInput, file);
    await user.click(
      screen.getByRole("button", { name: /upload and preserve/i }),
    );

    await waitFor(() => {
      expect(screen.getByText(/evidence uploaded and preserved/i)).toBeInTheDocument();
    });
    expect(await screen.findByText("report.pdf")).toBeInTheDocument();
  });

  it("shows an error when upload fails", async () => {
    configureApiClientAuth(() => "test-token");
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: "File content is required" }),
      });
    vi.stubGlobal("fetch", fetchMock);

    const user = userEvent.setup();
    renderCaseUpload();

    const uploadSection = screen.getByRole("region", {
      name: /upload evidence file/i,
    });
    const fileInput = within(uploadSection).getByLabelText(/evidence file/i);
    const file = new File(["content"], "notes.txt", { type: "text/plain" });
    await user.upload(fileInput, file);
    await user.click(
      screen.getByRole("button", { name: /upload and preserve/i }),
    );

    expect(
      await screen.findByRole("alert"),
    ).toHaveTextContent(/file content is required/i);
  });
});
