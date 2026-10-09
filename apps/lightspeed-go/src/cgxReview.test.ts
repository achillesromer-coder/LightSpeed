import { describe, expect, it } from "vitest";
import projection from "../public/data/cgx_internal_review_projection.json";
import { renderCgxReviewProjection, type CgxReviewProjection } from "./cgxReview";

describe("CGX internal review lens", () => {
  it("projects the existing BUILD-068 queue without creating parallel state", () => {
    expect(projection.authority.queue_id).toBe("BUILD-068");
    expect(projection.instances).toHaveLength(8);
    expect(projection.metrics.archetypes).toBe(411);
    expect(projection.metrics.matrix_fields).toBe(60);
    expect(projection.kernels).toHaveLength(20);
    expect(projection.metrics.physical_tests_run).toBe(0);
    expect(projection.metrics.requirement_targets_open).toBe(0);
    expect(projection.gate_counts).toEqual({
      SOURCE_IDENTITY: 1,
      LOT_PASSPORT: 5,
      PROCESS_ROUTE: 1,
      UPSTREAM_EVIDENCE: 1,
    });
  });

  it("keeps the reviewed resistor and loop targets evidence-bounded", () => {
    const resistor = projection.instances.find((item) => item.instance_id === "CGXI-P2-R-001");
    const loop = projection.instances.find((item) => item.instance_id === "CGXI-P3-LOOP-001");
    expect(resistor?.target).toContain("1.0 kΩ");
    expect(resistor?.first_open_gate).toBe("LOT_PASSPORT");
    expect(loop?.target).toContain("13.56 MHz");
    expect(loop?.first_open_gate).toBe("LOT_PASSPORT");
    expect(loop?.physical_state).toBe("NOT_RUN");
  });

  it("renders internal and showcase-safe lenses with explicit publication boundary", () => {
    const html = renderCgxReviewProjection(projection as CgxReviewProjection);
    expect(html).toContain(".cgx interactive review lens");
    expect(html).toContain("CGXI queue");
    expect(html).toContain("Equation kernels");
    expect(html).toContain("Showcase-safe");
    expect(html).toContain("NOT_PUBLISHED");
    expect(html).toContain("read-only projection");
  });

  it("keeps showcase-safe content free of owner credentials and local paths", () => {
    const publicText = JSON.stringify(projection.showcase).toLowerCase();
    expect(publicText).not.toContain("c:\\");
    expect(publicText).not.toContain("password");
    expect(publicText).not.toContain("hotdogg3211");
    expect(publicText).not.toContain("spreadsheet_id");
  });
});