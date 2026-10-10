import { describe, expect, it } from "vitest";
import { componentPlateSvg } from "./componentVisualizer";

const fixture = {
  ID: "CGA-C-001",
  Domain: "Electrical",
  Family: "Capacitor",
  "Component Archetype": "Parallel-plate capacitor",
  "Primary Function": "Store electrostatic energy / establish capacitance",
  "Baseline Geometry": "opposed electrodes separated by dielectric",
  "Geometric Parameters": "area, gap, thickness, guard geometry",
  "Typical Material Stack": "conductor / dielectric / conductor",
  "Primary Physics": "electrostatic field",
  "Baseline Model / Equation": "C≈ε0εrA/d in valid uniform-field regime",
  "Ports / Interfaces": "two electrical terminals",
  "Current Manufacturing Route": "printed conductor + dielectric stack",
  "Current CGX Build Class": "PRINTED_FUNCTIONAL",
  "Scale Band": "coupon→embedded",
  "4D Fields": "V,Q,E,T,RH,aging",
  "Acceptance Tests": "LCR / leakage / thickness",
  "Failure Modes": "pinholes / contamination / delamination",
  "Evidence State": "SOURCE-CANDIDATE BOUND / PHYSICAL_NOT_RUN",
  "Source Authority Class": "owner matrix + attributable source",
};

describe("component 4K symbolic visualizer", () => {
  it("creates a resolution-independent 3840x2160 corpus-derived plate", () => {
    const svg = componentPlateSvg(fixture);
    expect(svg).toContain('width="3840"');
    expect(svg).toContain('height="2160"');
    expect(svg).toContain("CGA-C-001");
    expect(svg).toContain("Parallel-plate capacitor");
    expect(svg).toContain("C≈ε0εrA/d");
    expect(svg).toContain("SYMBOLIC 4K PLATE");
    expect(svg).toContain("NOT RELEASED GEOMETRY");
    expect(svg).toContain("PHYSICAL_NOT_RUN");
  });

  it("does not promote symbolic visualization into released geometry", () => {
    const svg = componentPlateSvg(fixture);
    expect(svg).toContain("Exact CGXI/source/lot/geometry/process/tool/calibration/test evidence governs realization.");
  });
});
