import { afterEach, describe, expect, it, vi } from "vitest";

import { loadConfig } from "./config";

describe("loadConfig", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("defaults to local environment", () => {
    const config = loadConfig();
    expect(config.appEnv).toBe("local");
    expect(config.apiBaseUrl).toBeTruthy();
  });

  it("reads VITE_API_BASE_URL when VITE_APP_ENV is local", () => {
    vi.stubEnv("VITE_APP_ENV", "local");
    vi.stubEnv("VITE_API_BASE_URL", "http://localhost:9000");

    const config = loadConfig();

    expect(config.appEnv).toBe("local");
    expect(config.apiBaseUrl).toBe("http://localhost:9000");
  });

  it("uses deployed environment when VITE_APP_ENV is deployed", () => {
    vi.stubEnv("VITE_APP_ENV", "deployed");
    vi.stubEnv("VITE_API_BASE_URL", "https://api.example.com");

    const config = loadConfig();

    expect(config.appEnv).toBe("deployed");
    expect(config.apiBaseUrl).toBe("https://api.example.com");
  });
});
