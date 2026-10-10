import { describe, expect, it } from "vitest";
import { meshViewerButtonMarkup } from "./meshViewer";

describe("CGX source mesh viewer controls", () => {
  it("emits a bounded interactive trigger with source and evidence metadata", () => {
    const html=meshViewerButtonMarkup({
      url:"/review/mesh/luke_family.json",
      label:"Luke family",
      source:"repo:assets/models/luke_family.obj",
      sourceHash:"abc123",
      physicalState:"NOT_AS_BUILT / REVIEW_ONLY",
    });
    expect(html).toContain("Interactive 3D");
    expect(html).toContain("/review/mesh/luke_family.json");
    expect(html).toContain("abc123");
    expect(html).toContain("NOT_AS_BUILT");
  });
});
