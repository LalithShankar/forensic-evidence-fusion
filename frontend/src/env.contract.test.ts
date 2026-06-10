import { describe, expect, it } from "vitest";

import gitignore from "../../.gitignore?raw";

describe("frontend environment files", () => {
  it("keeps frontend .env out of version control", () => {
    expect(gitignore).toMatch(/^\.env$/m);
    expect(gitignore).toMatch(/^\.env\.\*$/m);
    expect(gitignore).toMatch(/^!\.env\.example$/m);
  });
});
