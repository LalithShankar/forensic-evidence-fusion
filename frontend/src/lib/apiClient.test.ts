import { afterEach, describe, expect, it, vi } from "vitest";

import {
  configureApiClientAuth,
  createApiClient,
} from "./apiClient";

describe("createApiClient", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    configureApiClientAuth(() => null);
  });

  it("targets the configured backend URL for health calls", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        status: "ok",
        app_env: "local",
        secrets_source: "dotenv",
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = createApiClient({
      appEnv: "local",
      apiBaseUrl: "http://localhost:9000",
    });

    const health = await client.fetchHealth();

    expect(fetchMock).toHaveBeenCalledWith("http://localhost:9000/health", {
      headers: new Headers(),
    });
    expect(health.status).toBe("ok");
    expect(client.baseUrl).toBe("http://localhost:9000");
  });

  it("strips trailing slashes from the base URL", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        status: "ok",
        app_env: "local",
        secrets_source: "dotenv",
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = createApiClient({
      appEnv: "local",
      apiBaseUrl: "http://localhost:9000/",
    });

    await client.fetchHealth();

    expect(fetchMock).toHaveBeenCalledWith("http://localhost:9000/health", {
      headers: new Headers(),
    });
  });

  it("throws when the health response is not ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
      }),
    );

    const client = createApiClient({
      appEnv: "local",
      apiBaseUrl: "http://localhost:8000",
    });

    await expect(client.fetchHealth()).rejects.toThrow(
      "Request failed: 503",
    );
  });

  it("attaches Bearer auth headers for authenticated requests", async () => {
    configureApiClientAuth(() => "test-token");
    const fetchMock = vi.fn().mockResolvedValue({
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

    const client = createApiClient({
      appEnv: "local",
      apiBaseUrl: "http://localhost:8000",
    });

    await client.fetchMe();

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/auth/me",
      expect.objectContaining({
        headers: expect.any(Headers),
      }),
    );
    const headers = fetchMock.mock.calls[0][1].headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer test-token");
  });

  it("calls unauthorized handler on 401 responses", async () => {
    const onUnauthorized = vi.fn();
    configureApiClientAuth(() => "expired-token", onUnauthorized);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
      }),
    );

    const client = createApiClient({
      appEnv: "local",
      apiBaseUrl: "http://localhost:8000",
    });

    await expect(client.fetchMe()).rejects.toThrow("Request failed: 401");
    expect(onUnauthorized).toHaveBeenCalledTimes(1);
  });
});
