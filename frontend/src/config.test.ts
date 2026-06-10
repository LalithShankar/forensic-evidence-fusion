import { describe, expect, it } from "vitest";

import { loadConfig } from "./config";

describe("loadConfig", () => {
  it("defaults to local environment", () => {
    const config = loadConfig();
    expect(config.appEnv).toBe("local");
    expect(config.apiBaseUrl).toBeTruthy();
  });
});
