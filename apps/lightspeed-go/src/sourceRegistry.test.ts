import { describe, expect, it } from "vitest";

import { sourceLinks } from "./sourceRegistry";

describe("canonical source registry", () => {
  it("keeps every operator-facing source unique and HTTPS-bound", () => {
    const names = sourceLinks.map(([name]) => name);
    const urls = sourceLinks.map(([, url]) => url);

    expect(new Set(names).size).toBe(sourceLinks.length);
    expect(new Set(urls).size).toBe(sourceLinks.length);
    expect(urls.every((url) => url.startsWith("https://"))).toBe(true);
  });

  it("exposes the implementation, review, canon, reconciliation and public surfaces", () => {
    const byName = Object.fromEntries(sourceLinks.map(([name, url]) => [name, url]));

    expect(byName["LightSpeed Git"]).toContain("achillesromer-coder/LightSpeed");
    expect(byName["Type 1 Digital Review"]).toMatch(/\/pull\/46$/);
    expect(byName["Type 1 Römer Canon"]).toContain("1refNFmebTcmPVojCuZsyILJEWaKz-sVzYLfZtqMl8k8");
    expect(byName["ACR3 Handoffs"]).toContain("1AgAhLPNtrO91C_-ea7EdOkOsyXrCCYvFVvmDSGq8uls");
    expect(byName["Römer Industries"]).toBe("https://romer.industries");
  });
});
