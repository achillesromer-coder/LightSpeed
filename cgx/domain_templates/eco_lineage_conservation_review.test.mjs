import test from "node:test";
import assert from "node:assert/strict";
import {reviewEcoLineageConservation as review} from "./eco_lineage_conservation_review.mjs";
// All counts and source refs below are synthetic fixtures, never field evidence.
const trace={source_ref:"fixture:source",source_revision_ref:"fixture:rev",
 parent_lineage_ref:"fixture:parents",descendant_record_ref:"fixture:descendants",
 establishment_method_ref:"fixture:method",observation_time_ref:"fixture:time"};
test("no source or count means no lineage ratio",()=>{
 const r=review();assert.equal(r.conditional_arithmetic_ratio,null);
 assert.ok(r.flags.includes("COUNT_INPUTS_NOT_SUPPLIED"));
 assert.equal(r.original_formula_equivalence_verified,false);
});
test("untraced counts cannot produce a lineage ratio",()=>{
 const r=review({parent_plants_removed:2,established_descendants:3});
 assert.equal(r.conditional_arithmetic_ratio,null);
 assert.ok(r.flags.includes("UNTRACED_DESCENDANTS_RATIO_WITHHELD"));
});
test("trace-labelled synthetic counts permit arithmetic but no field assertion",()=>{
 const r=review({...trace,parent_plants_removed:2,established_descendants:3});
 assert.equal(r.conditional_arithmetic_ratio,1.5);
 assert.equal(r.observed_establishment_verified,false);
 assert.equal(r.ecological_effect_verified,false);
 assert.equal(r.source_record_bytes_verified_by_module,false);
});
test("zero removed-parent denominator is undefined, not infinity",()=>{
 const r=review({...trace,parent_plants_removed:0,established_descendants:3});
 assert.equal(r.conditional_arithmetic_ratio,null);
 assert.ok(r.flags.includes("ZERO_REMOVED_PARENT_DENOMINATOR_UNDEFINED"));
});
test("zero synthetic established descendants is arithmetic zero only",()=>{
 const r=review({...trace,parent_plants_removed:2,established_descendants:0});
 assert.equal(r.conditional_arithmetic_ratio,0);
 assert.equal(r.removal_or_propagation_authorised,false);
});
test("observed label and complete-looking refs cannot self-authorise field actions",()=>{
 const r=review({...trace,parent_plants_removed:2,established_descendants:3,
 evidence_class:"observed",site_review_ref:"fixture:site",
 taxon_review_ref:"fixture:taxon",removal_authorisation_ref:"fixture:permission",
 denominator_basis_ref:"fixture:basis",counterevidence_ref:"fixture:counter",
 independent_qa_ref:"fixture:qa",original_formula_lineage_ref:"fixture:original"});
 assert.ok(r.flags.includes("OBSERVED_LABEL_NOT_A_FIELD_RECEIPT"));
 assert.equal(r.removal_or_propagation_authorised,false);
 assert.equal(r.native_object_id,null);
 assert.equal(r.db_readback,false);
 assert.equal(r.public_release_authorised,false);
});
test("negative, fractional, nonfinite and unsafe counts are rejected",()=>{
 for(const n of [-1,1.5,Infinity,NaN,Number.MAX_SAFE_INTEGER+1])
 assert.throws(()=>review({parent_plants_removed:n}),/INVALID_ECO_LCR_INPUT/);
});
test("raw coordinates, extra fields, wrong formula and control characters are rejected",()=>{
 assert.throws(()=>review({coordinates:[-27,153]}),/INVALID_ECO_LCR_FIELDS/);
 assert.throws(()=>review({formula_id:"FM-008"}),/INVALID_ECO_LCR_INPUT/);
 assert.throws(()=>review({source_ref:"bad\nref"}),/INVALID_ECO_LCR_INPUT/);
});
test("lineage trace must include both parents and established descendants",()=>{
 for(const key of ["parent_lineage_ref","descendant_record_ref",
 "establishment_method_ref","observation_time_ref"]){
 const x={...trace};delete x[key];
 const r=review({...x,parent_plants_removed:2,established_descendants:3});
 assert.equal(r.conditional_arithmetic_ratio,null);
 }
});
