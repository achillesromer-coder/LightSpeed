import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

const readPublic = (relative: string) =>
  readFileSync(new URL("../public/" + relative, import.meta.url), "utf8");

describe("UTP maturity/composition object-review projections", () => {
  it("publishes bounded UTP-148 and UTP-149 review objects", () => {
    const manifest = JSON.parse(readPublic("data/cgx_object_review_catalogue.json"));
    const byId = new Map((manifest.bridge_review_objects || []).map((row: any) => [row.id, row]));

    const maturity: any = byId.get("cgx:utp_148_maturity");
    const composition: any = byId.get("cgx:utp_149_4d_composition");
    const ingest: any = byId.get("cgx:utp_150_ingest_maturation");

    expect(maturity).toBeTruthy();
    expect(composition).toBeTruthy();
    expect(ingest).toBeTruthy();
    expect(ingest.physical_state).toContain("PHYSICAL_NOT_RUN");
    expect(manifest.maturity_projection.artifact_id).toBe("UTP-150");
    expect(manifest.maturity_projection.maturity_axes).toHaveLength(10);
    expect(manifest.maturity_projection.numeric_routes).toEqual(["NUMERIC", "SYMBOLIC", "HOLD"]);
    expect(manifest.maturity_projection.next_witness_ladder).toContain("P0_IDENTITY");
    expect(manifest.maturity_projection.proof_fixture_count).toBeGreaterThanOrEqual(3);
    expect(maturity.physical_state).toContain("PHYSICAL_NOT_RUN");
    expect(composition.physical_state).toContain("PHYSICAL_NOT_RUN");
    expect(maturity.geometry_state).toContain("SYMBOLIC");
    expect(composition.geometry_state).toContain("SYMBOLIC");
    expect(manifest.coverage.symbolic_system_lineage_plates).toBeGreaterThanOrEqual(8);
  });

  it("ships both source-grounded symbolic review plates", () => {
    const maturity = readPublic("review/renders/utp_148_maturity_review.svg");
    const composition = readPublic("review/renders/utp_149_4d_composition_review.svg");

    for (const svg of [maturity, composition]) {
      expect(svg).toContain("SYMBOLIC SYSTEM PLATE");
      expect(svg).toContain("REVIEW ONLY");
      expect(svg).toContain("PHYSICAL_NOT_RUN");
    }
    expect(composition).toContain("2D");
    expect(composition).toContain("3D");
    expect(composition).toContain("4D");
  });
});
