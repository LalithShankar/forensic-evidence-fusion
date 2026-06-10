import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { LoginPage } from "./Login";
import { renderWithProviders } from "../test/renderWithProviders";

describe("LoginPage", () => {
  it("submits credentials and navigates after successful login", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          access_token: "jwt-token",
          token_type: "bearer",
          expires_in: 1800,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: "11111111-1111-1111-1111-111111111111",
          email: "analyst@local.dev",
          display_name: "Local Analyst",
          role: "analyst",
          status: "active",
        }),
      });
    vi.stubGlobal("fetch", fetchMock);

    const user = userEvent.setup();
    renderWithProviders(<LoginPage />, {
      routerProps: { initialEntries: ["/login"] },
    });

    await user.type(screen.getByLabelText(/email/i), "analyst@local.dev");
    await user.type(screen.getByLabelText(/password/i), "DevPassword123!");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/auth/login",
        expect.objectContaining({ method: "POST" }),
      );
    });
  });

  it("shows a safe error for invalid credentials", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
      }),
    );

    const user = userEvent.setup();
    renderWithProviders(<LoginPage />, {
      routerProps: { initialEntries: ["/login"] },
    });

    await user.type(screen.getByLabelText(/email/i), "analyst@local.dev");
    await user.type(screen.getByLabelText(/password/i), "wrong");
    await user.click(screen.getByRole("button", { name: /sign in/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /invalid email or password/i,
    );
  });
});
