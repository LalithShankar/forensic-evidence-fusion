import { screen } from "@testing-library/react";
import { Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ArtifactDetailPage } from "./ArtifactDetail";
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
const artifactId = "33333333-3333-3333-3333-333333333333";

const sampleArtifact = {
  id: artifactId,
  case_id: caseId,
  original_filename: "report.pdf",
  file_size_bytes: 12,
  file_extension: "pdf",
  mime_type: "application/pdf",
  uploaded_by: authenticatedUser.id,
  uploaded_at: "2026-06-10T10:00:00Z",
  content_hash: "abc123",
  status: "preserved" as const,
  source_group: "financial",
  source_family: "bank_statements",
  artifact_type: "pdf_export",
  collection_method: "manual_export",
  parser_class: "direct_structured",
  provenance_notes: "Exported from analyst portal.",
  upload_batch_id: null,
  classification_confidence: 0.72,
  suggested_source_group: "Generic",
  suggested_source_family: "Document",
  suggested_artifact_type: "pdf",
  classification_reason: "PDF file extension or MIME type",
  blocker_notes: null,
  created_at: "2026-06-10T10:00:00Z",
  updated_at: "2026-06-10T10:00:00Z",
};

function renderArtifactDetail() {
  renderWithProviders(
    <Routes>
      <Route
        path="/cases/:caseId/artifacts/:artifactId"
        element={<ArtifactDetailPage />}
      />
    </Routes>,
    {
      routerProps: {
        initialEntries: [`/cases/${caseId}/artifacts/${artifactId}`],
      },
      authProps: {
        initialToken: "test-token",
        initialUser: authenticatedUser,
      },
    },
  );
}

describe("ArtifactDetailPage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    configureApiClientAuth(() => null);
  });

  it("renders provenance metadata from the API", async () => {
    configureApiClientAuth(() => "test-token");
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(async (url: string) => ({
        ok: true,
        json: async () => {
          if (url.includes("/events")) {
            return [];
          }
          return sampleArtifact;
        },
      })),
    );

    renderArtifactDetail();

    expect(await screen.findByText("report.pdf")).toBeInTheDocument();
    expect(screen.getByText("financial")).toBeInTheDocument();
    expect(screen.getByText("bank statements")).toBeInTheDocument();
    expect(screen.getByText("Exported from analyst portal.")).toBeInTheDocument();
  });
});
