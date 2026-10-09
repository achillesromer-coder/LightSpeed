import { describe, expect, it } from "vitest";
import { renderObjectReview, type ObjectReviewCatalogue, type PrintableCatalogue } from "./objectReview";

const manifest: ObjectReviewCatalogue = {
  schema: "CGX-OBJECT-REVIEW-CATALOGUE/0.1",
  generated_from_git: "test",
  status: "INTERNAL_REVIEW",
  authority: "Drive owner + Git mirror",
  visual_system: { palette: {}, rule: "Do not invent geometry.", render_plate: "3840x2160" },
  coverage: { printable_4d_archetypes: 411, macro_source_meshes: 1, symbolic_core_component_stack_plates: 1, physical_tests_complete: 0 },
  tiers: [{ id: "T0", label: "component", description: "component review" }],
  micro_review_objects: [{
    id:"cgx:diode",label:"Diode",role:"hybrid seed",level:"component",source:"CGX",
    render:"/review/renders/diode.png",geometry_state:"SYMBOLIC",physical_state:"NOT_RUN",
    review_rules:["not as-built"],
  }],
  macro_review_objects: [{
    id:"macro:luke",label:"Luke",role:"system",level:"system",source:"repo mesh",
    render:"/review/renders/luke.png",geometry_state:"CONCEPT_REFERENCE_MESH",physical_state:"NOT_AS_BUILT / REVIEW_ONLY",
    review_rules:["review only"],stats:{vertices:10,faces:12,extents:[1,2,3],bytes:42},
  }],
  catalogue_ref:"/data/printable_4d_catalogue_full.json",
  pending_owner_layers:["UTP-143"],
  boundary:"No render is physical proof.",
};

const catalogue: PrintableCatalogue = {
  schema:"CGX-PRINTABLE-4D-CATALOGUE/0.1",artifact_id:"UTP-138",archetype_count:411,
  compound_parent_decomposition_count:9,authority_boundary:"Derived projection only.",
  records:[{
    archetype_id:"CGA-D-001",domain:"Semiconductor",family:"Diode",name:"PN rectifier diode",
    print_path:"PRINT_PLUS_SEED_INSERT_PATH",packet_state:"CATALOGUE_TEMPLATE",
    topology_kernel_ids:["VGK-034"],topology_tokens:["VOL_ACTIVE_SEED"],
    geometry_parameter_slots:["package","carrier"],candidate_material_stack:"seed + carrier",
    physical_execution:false,
  }],
};

describe("CGX object review catalogue", () => {
  it("renders source-mesh and symbolic review plates without claiming physical completion", () => {
    const html=renderObjectReview(manifest,catalogue);
    expect(html).toContain("Component → stack → Luke / Mark / InterSol");
    expect(html).toContain("Diode");
    expect(html).toContain("Luke");
    expect(html).toContain("NOT_RUN");
    expect(html).toContain("NOT_AS_BUILT");
    expect(html).toContain("No render is physical proof");
  });

  it("keeps the complete printable catalogue reviewable as a derived projection", () => {
    const html=renderObjectReview(manifest,catalogue);
    expect(html).toContain("411 printable components");
    expect(html).toContain("CGA-D-001");
    expect(html).toContain("VGK-034");
    expect(html).toContain("PRINT_PLUS_SEED_INSERT_PATH");
  });
});
