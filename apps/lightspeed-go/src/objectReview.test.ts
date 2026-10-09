import { describe, expect, it } from "vitest";
import { renderObjectReview, type ComponentAtlas, type ObjectReviewCatalogue } from "./objectReview";

const manifest: ObjectReviewCatalogue = {
  schema: "CGX-OBJECT-REVIEW-CATALOGUE/0.1",
  generated_from_git: "test",
  status: "INTERNAL_REVIEW",
  authority: "Drive owner + Git mirror",
  visual_system: { palette: {}, rule: "Do not invent geometry.", render_plate: "resolution-independent SVG" },
  coverage: { printable_4d_archetypes: 411, macro_source_meshes: 1, symbolic_core_component_stack_plates: 1, physical_tests_complete: 0 },
  tiers: [{ id: "T0", label: "component", description: "component review" }],
  micro_review_objects: [{
    id:"cgx:diode",label:"Diode",role:"hybrid seed",level:"component",source:"CGX",
    render:"/review/renders/diode.svg",geometry_state:"SYMBOLIC",physical_state:"NOT_RUN",
    review_rules:["not as-built"],
  }],
  macro_review_objects: [{
    id:"macro:luke",label:"Luke",role:"system",level:"system",source:"repo mesh",
    render:"/review/renders/luke.svg",geometry_state:"CONCEPT_REFERENCE_MESH",physical_state:"NOT_AS_BUILT / REVIEW_ONLY",
    review_rules:["review only"],stats:{vertices:10,faces:12,extents:[1,2,3],bytes:42},
  }],
  atlas_ref:"/data/component_geometry_atlas_public_review.json",
  pending_owner_layers:["UTP-143"],
  boundary:"No render is physical proof.",
};

const atlas: ComponentAtlas = {
  schema:"CGX-COMPONENT-GEOMETRY-ATLAS/0.1",status:"review",record_count:1,
  records:[{
    ID:"CGA-D-001",Domain:"Semiconductor",Family:"Diode","Component Archetype":"PN rectifier diode",
    "Primary Function":"rectification","Baseline Geometry":"seed package on carrier",
    "Geometric Parameters":"package; pad; carrier","Current CGX Build Class":"INSERT-SEED",
    "Current Manufacturing Route":"seed + printed carrier","Primary Physics":"semiconductor conduction",
    "4D Fields":"V; I; T; t","Evidence State":"ESTABLISHED","Source Authority Class":"datasheet",
  }],
};

describe("CGX object review catalogue", () => {
  it("renders source-mesh and symbolic review plates without claiming physical completion", () => {
    const html=renderObjectReview(manifest,atlas);
    expect(html).toContain("Component → stack → Luke / Mark / InterSol");
    expect(html).toContain("Diode");
    expect(html).toContain("Luke");
    expect(html).toContain("NOT_RUN");
    expect(html).toContain("NOT_AS_BUILT");
    expect(html).toContain("No render is physical proof");
  });

  it("keeps the complete component atlas reviewable without duplicating printable compiler semantics", () => {
    const html=renderObjectReview(manifest,atlas);
    expect(html).toContain("411 component catalogue");
    expect(html).toContain("CGA-D-001");
    expect(html).toContain("INSERT-SEED");
    expect(html).toContain("seed package on carrier");
    expect(html).toContain("adjacent CGX lens");
  });
});
