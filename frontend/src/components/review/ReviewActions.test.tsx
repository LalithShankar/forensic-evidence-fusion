import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ReviewActions } from "./ReviewActions";
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

function renderActions(onUpdated = vi.fn()) {
  const artifact = makeArtifact({
    original_filename: "mystery.bin",
    status: "needs_review",
  });
  renderWithProviders(
    <ReviewActions caseId={caseId} artifact={artifact} onUpdated={onUpdated} />,
    {
      authProps: { initialToken: "test-token", initialUser: authenticatedUser },
    },
  );
  return { artifact, onUpdated };
}

function mockPatchOnce(status: string) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        artifact: makeArtifact({ status: status as never }),
        message: "ok",
      }),
    }),
  );
}

describe("ReviewActions", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    configureApiClientAuth(() => null);
  });

  it("approves an artifact via PATCH with approve action", async () => {
    configureApiClientAuth(() => "test-token");
    mockPatchOnce("ready_for_transformation");
    const { onUpdated } = renderActions();

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /approve/i }));

    await waitFor(() => expect(onUpdated).toHaveBeenCalled());
    const fetchMock = globalThis.fetch as unknown as ReturnType<typeof vi.fn>;
    const body = JSON.parse(fetchMock.mock.calls[0][1].body as string);
    expect(body.action).toBe("approve");
  });

  it("sends corrected metadata with the correct action", async () => {
    configureApiClientAuth(() => "test-token");
    mockPatchOnce("needs_review");
    renderActions();

    const user = userEvent.setup();
    const sourceGroup = screen.getByLabelText(/source group/i);
    await user.clear(sourceGroup);
    await user.type(sourceGroup, "ThirdParty");
    await user.click(screen.getByRole("button", { name: /save correction/i }));

    await waitFor(() => {
      const fetchMock = globalThis.fetch as unknown as ReturnType<typeof vi.fn>;
      expect(fetchMock).toHaveBeenCalled();
      const body = JSON.parse(fetchMock.mock.calls[0][1].body as string);
      expect(body.action).toBe("correct");
      expect(body.source_group).toBe("ThirdParty");
    });
  });

  it("marks an artifact preserve-only", async () => {
    configureApiClientAuth(() => "test-token");
    mockPatchOnce("preserve_only");
    renderActions();

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /preserve only/i }));

    await waitFor(() => {
      const fetchMock = globalThis.fetch as unknown as ReturnType<typeof vi.fn>;
      const body = JSON.parse(fetchMock.mock.calls[0][1].body as string);
      expect(body.action).toBe("preserve_only");
    });
  });
});
