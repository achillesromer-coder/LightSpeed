import { describe, expect, it } from "vitest";
import projection from "../public/data/cgx_internal_review_projection.json";
import { renderCgxReviewProjection } from "./cgxReview";

describe("CGX internal review lens", () => {
  it("projects the existing BUILD-070 queue without creating parallel state", () => {
    expect(projection.authority.queue_id).toBe("BUILD-070");
    expect(projection.instances).toHaveLength(8);
    expect(projection.metrics.archetypes).toBe(411);
    expect(projection.metrics.matrix_fields).toBe(60);
    expect(projection.kernels).toHaveLength(20);
    expect(projection.volumetric_kernels).toHaveLength(36);
    expect(projection.metrics.volumetric_kernels).toBe(36);
    expect(projection.metrics.printable_4d_templates).toBe(411);
    expect(projection.printable_4d.template_count).toBe(411);
    expect(projection.printable_4d.coupled_stack_kernel).toBe("VGK-036");
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
    const html = renderCgxReviewProjection(projection);
    expect(html).toContain(".cgx interactive review lens");
    expect(html).toContain("CGXI queue");
    expect(html).toContain("Equation kernels");
    expect(html).toContain("Volumetric kernels");
    expect(html).toContain("Printable 4D");
    expect(html).toContain("411");
    expect(html).toContain("CGX-PRINTABLE-4D-COMPONENT/0.1");
    expect(html).toContain("VGK-036");
    expect(html).toContain("Showcase-safe");
    expect(html).toContain("NOT_PUBLISHED");
    expect(html).toContain("read-only projection");
  });

  it("keeps printable 4D packets machine-neutral and nonduplicative", () => {
    expect(projection.printable_4d.invariants.join(" ")).toContain("no second engineering catalogue");
    expect(projection.printable_4d.invariants.join(" ")).toContain("Parameter slots may remain open");
    expect(projection.printable_4d.invariants.join(" ")).toContain("machine programs remain unavailable");
    expect(projection.printable_4d.exact_examples.every((item) => item.state.includes("HOLD"))).toBe(true);
  });

  it("keeps showcase-safe content free of owner credentials and local paths", () => {
    const publicText = JSON.stringify(projection.showcase).toLowerCase();
    expect(publicText).not.toContain("c:\\");
    expect(publicText).not.toContain("password");
    expect(publicText).not.toContain("hotdogg3211");
    expect(publicText).not.toContain("spreadsheet_id");
  });
});