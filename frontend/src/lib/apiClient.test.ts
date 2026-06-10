import { afterEach, describe, expect, it, vi } from "vitest";

import { createApiClient } from "./apiClient";

describe("createApiClient", () => {
  afterEach(() => {
    vi.restoreAllMocks();
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

    expect(fetchMock).toHaveBeenCalledWith("http://localhost:9000/health");
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

    expect(fetchMock).toHaveBeenCalledWith("http://localhost:9000/health");
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
      "Health check failed: 503",
    );
  });
});
