import { describe, expect, it } from "vitest";
import { loadType1CatalogueProjection, renderType1CatalogueProjection, type Type1CatalogueProjection } from "./utpCatalogue";

const fixture: Type1CatalogueProjection = {
  schema: "CGX-TYPE1-CATALOGUE-PROJECTION/0.2",
  generated_from: "owner",
  source_owner: { spreadsheet_id: "sheet", authority: "owner" },
  metrics: { archetypes: 411, universal_matrix_fields: 60, directional_4d_fields: 16, quantitative_factorization_fields: 8, primitive_basis_classes: 20, equation_kernel_records: 20 },
  surfaces: [{ id: "32", name: "Universal <Matrix>", role: "directional stack" }],
  contracts: ["UTP-117", "UTP-124", "UTP-125"],
  inference_example: { label: "Capacitance", equation: "C=e0*er*A/d", inputs: "bound 50 um", result: "0.6020848 pF/mm2", evidence: "engineering inference only" },
  boundary: "not physical readiness",
};

describe("Type-I catalogue projection", () => {
  it("renders owner-derived matrix metrics without authority uplift", () => {
    const html = renderType1CatalogueProjection(fixture);
    expect(html).toContain("411 archetypes");
    expect(html).toContain("60 fields");
    expect(html).toContain("quantitative compiler fields");
    expect(html).toContain("primitive basis classes");
    expect(html).toContain("equation / constitutive kernels");
    expect(html).toContain("UTP-124/125");
    expect(html).toContain("0.6020848 pF/mm2");
    expect(html).toContain("not physical readiness");
    expect(html).not.toContain("Universal <Matrix>");
    expect(html).toContain("Universal &lt;Matrix&gt;");
  });

  it("supports bounded async loading", async () => {
    const html = await loadType1CatalogueProjection(async () => fixture);
    expect(html).toContain("READ ONLY");
  });
});
