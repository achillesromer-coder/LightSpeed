import test from "node:test";
import assert from "node:assert/strict";
import {reviewSecondCycleClaim as review} from "./eco_second_cycle_claim_review.mjs";
const base={claim_kind:"passive_flow",evidence_class:"source_asserted"};
test("source-only model never becomes a physical or live CGX result",()=>{
 const r=review(base);
 assert.equal(r.physical_metric_verified,false);
 assert.equal(r.db_readback,false);
 assert.equal(r.native_object_id,null);
 assert.equal(r.admission_stage,"R1_REVIEW_ONLY");
 assert.ok(r.flags.includes("R0_ORIGINAL_BYTE_HASH_REQUIRED"));
});
test("source assertion, hypothesis and inference stay distinct from measured outcomes",()=>{
 const cases=[
  ["source_asserted","SOURCE_ASSERTION_NOT_MEASUREMENT_OR_VALIDATED_OUTCOME"],
  ["hypothesised","HYPOTHESIS_REQUIRES_TESTABLE_BASELINE_CONTROL_AND_FALSIFIER"],
  ["inferred","INFERENCE_REQUIRES_INPUT_EVIDENCE_AND_UNCERTAINTY"]
 ];
 for(const [evidence_class,flag] of cases){
  const r=review({claim_kind:"weather_effect",evidence_class,
   source_ref:"synthetic:source",issuer_ref:"synthetic:issuer"});
  assert.ok(r.flags.includes(flag));
  assert.ok(r.flags.includes("WEATHER_CAUSALITY_NOT_ESTABLISHED"));
  assert.equal(r.field_observation_verified,false);
  assert.equal(r.ecological_effect_verified,false);
  assert.equal(r.public_release_authorised,false);
 }
});
test("strict units prohibit velocity being presented as volumetric flow",()=>{
 assert.throws(()=>review({...base,numeric_value:1.2,unit:"m/s"}),/INVALID_SECOND_CYCLE_REVIEW_INPUT/);
});
test("validly typed numeric proxy remains unvalidated",()=>{
 const r=review({...base,numeric_value:6,unit:"L/s"});
 assert.ok(r.flags.includes("NUMERIC_VALUE_NOT_INDEPENDENTLY_VALIDATED"));
 assert.ok(r.flags.includes("NUMERIC_TIME_FRAME_ORIGIN_REQUIRED"));
 assert.equal(r.physical_metric_verified,false);
});
test("synthetic aerosol index is never accepted as physical residence time",()=>{
 const r=review({claim_kind:"aerosol_residence_index",evidence_class:"simulated",
  numeric_value:0.02,unit:"arbitrary_index"});
 assert.ok(r.flags.includes("ARBITRARY_INDEX_NOT_DIMENSIONLESS_PHYSICAL_METRIC"));
 assert.ok(r.flags.includes("SIMULATION_NOT_FIELD_OBSERVATION"));
});
test("weather causality remains on hold",()=>{
 const r=review({claim_kind:"weather_effect",evidence_class:"hypothesised"});
 assert.ok(r.flags.includes("WEATHER_CAUSALITY_NOT_ESTABLISHED"));
 assert.equal(r.ecological_effect_verified,false);
});
test("habitat design does not imply restoration",()=>{
 const r=review({claim_kind:"habitat_outcome",evidence_class:"inferred"});
 assert.ok(r.flags.includes("ECOLOGICAL_OUTCOME_NOT_VERIFIED"));
});
test("field deployment is not authorised by a source schema",()=>{
 const r=review({claim_kind:"field_deployment",evidence_class:"source_asserted"});
 assert.ok(r.flags.includes("PERMITS_BIOSECURITY_NAVIGATION_AND_CUSTODIAL_GATE_HOLD"));
 assert.equal(r.field_deployment_authorised,false);
});
test("complete-looking observation refs do not self-verify",()=>{
 const r=review({claim_kind:"water_quality_change",evidence_class:"observed",
  source_ref:"source",source_revision:"revision",issuer_ref:"issuer",
  source_sha256:"a".repeat(64),observed_at:"2026-10-30T07:00:00+10:00",
  raw_data_ref:"raw",independent_qa_ref:"qa",rights_review_ref:"rights",
  stewardship_review_ref:"stewardship"});
 assert.equal(r.field_observation_verified,false);
 assert.ok(r.flags.includes("OBSERVATION_RECEIPT_AND_INDEPENDENT_QA_REQUIRED"));
 assert.ok(r.flags.includes("HASH_DECLARATION_REQUIRES_PROVIDER_BYTE_MATCH"));
});
test("raw coordinates cannot pass the source-only boundary",()=>{
 assert.throws(()=>review({...base,coordinates:[-27,153]}),/INVALID_SECOND_CYCLE_REVIEW_FIELDS/);
 const r=review({...base,geometry_present:true});
 assert.ok(r.flags.includes("SPATIAL_SENSITIVITY_REVIEW_REQUIRED"));
});
test("credit claim cannot be monetised",()=>{
 const r=review({claim_kind:"carbon_credit",evidence_class:"hypothesised"});
 assert.ok(r.flags.includes("CREDIT_METHODOLOGY_AND_VERIFICATION_REQUIRED"));
 assert.equal(r.public_release_authorised,false);
});
test("mooring ratio is not a marine safety certification",()=>{
 const r=review({claim_kind:"mooring_margin",evidence_class:"simulated",
  numeric_value:2.5,unit:"ratio"});
 assert.ok(r.flags.includes("MOORING_ENGINEERING_SIGNOFF_REQUIRED"));
});
test("water quality needs calibrated controlled monitoring",()=>{
 const r=review({claim_kind:"water_quality_change",evidence_class:"observed"});
 assert.ok(r.flags.includes("CALIBRATED_CONTROLLED_WATER_MONITORING_REQUIRED"));
 assert.ok(r.flags.includes("OBSERVATION_EVIDENCE_INCOMPLETE"));
});
test("invalid original-byte hash declarations fail closed",()=>{
 assert.throws(()=>review({...base,source_sha256:"not-a-hash"}),/INVALID_SECOND_CYCLE_REVIEW_INPUT/);
});
test("invalid time and nonfinite or negative numbers fail closed",()=>{
 for(const row of [
  {...base,observed_at:"2026-02-29T00:00:00Z"},
  {...base,numeric_value:-1,unit:"L/s"},
  {...base,numeric_value:Infinity,unit:"L/s"}
 ])assert.throws(()=>review(row),/INVALID_SECOND_CYCLE_REVIEW_INPUT/);
});

test("hydraulic available-power screen is typed W and remains a dependent synthetic proxy",()=>{
 const r=review({claim_kind:"hydraulic_power_proxy",evidence_class:"simulated",
  numeric_value:3.1488,unit:"W",source_ref:"synthetic:source",
  issuer_ref:"synthetic:issuer"});
 assert.equal(r.declared_unit,"W");
 assert.ok(r.flags.includes("HYDRAULIC_POWER_PROXY_NOT_NET_OR_EXTRACTABLE_POWER"));
 assert.ok(r.flags.includes("SAME_INPUT_ALGEBRA_NOT_INDEPENDENT_PHYSICAL_VALIDATION"));
 assert.ok(r.flags.includes("HYDRAULIC_LOSSES_GEOMETRY_AND_BENCH_CALIBRATION_REQUIRED"));
 assert.ok(r.flags.includes("SIMULATION_NOT_FIELD_OBSERVATION"));
 assert.equal(r.physical_metric_verified,false);
 assert.equal(r.field_observation_verified,false);
 assert.equal(r.native_object_id,null);
 assert.equal(r.db_readback,false);
 assert.equal(r.public_release_authorised,false);
 for(const unit of ["J","kW","L/s","mÂ²"])
  assert.throws(()=>review({claim_kind:"hydraulic_power_proxy",
   evidence_class:"simulated",numeric_value:3.1488,unit}),
   /INVALID_SECOND_CYCLE_REVIEW_INPUT/);
});
test("hydraulic source assertion or observed label cannot self-verify a power outcome",()=>{
 for(const evidence_class of ["source_asserted","observed"]){
  const r=review({claim_kind:"hydraulic_power_proxy",evidence_class,
   numeric_value:3.1488,unit:"W",source_ref:"synthetic:source",
   source_revision:"synthetic:revision",issuer_ref:"synthetic:issuer"});
  assert.equal(r.physical_metric_verified,false);
  assert.equal(r.field_observation_verified,false);
  assert.equal(r.owner_accepted,false);
  assert.equal(r.public_release_authorised,false);
  assert.ok(r.flags.includes("SAME_INPUT_ALGEBRA_NOT_INDEPENDENT_PHYSICAL_VALIDATION"));
 }
});

import {reviewSecondCycleCoefficientRoles as rolesReview} from "./eco_second_cycle_claim_review.mjs";
test("synthetic Second Cycle coefficient symbol collision is held without numeric disclosure",()=>{
 const src={source_ref:"synthetic:second-cycle",source_revision:"synthetic:revision",
   source_sha256:"a".repeat(64)};
 const flow={formula_id:"FM-001",sheet_ref:"07_Flow_Mist_Model",
   parameter_cell_ref:"B5",role:"flow_coefficient",symbol:"Cd",
   numeric_value:0.5,unit:"ratio",evidence_class:"simulated"};
 const drag={formula_id:"FM-004",sheet_ref:"11_Anchor_Mooring",
   parameter_cell_ref:"B4",role:"drag_coefficient",symbol:"Cd",
   numeric_value:1.2,unit:"ratio",evidence_class:"simulated"};
 const review=rolesReview({...src,flow,drag});
 assert.equal(review.state,"R1_COEFFICIENT_SYMBOL_OVERLOAD_HOLD");
 assert.equal(review.same_symbol_distinct_roles,true);
 assert.equal(review.different_declared_baselines,true);
 assert.equal(review.coefficient_interchange_allowed,false);
 assert.equal(review.physical_model_validated,false);
 assert.equal(review.native_admitted,false);
 assert.equal(JSON.stringify(review).includes("0.5"),false);
 const separated=rolesReview({...src,flow:{...flow,symbol:"Cflow"},drag});
 assert.equal(separated.same_symbol_distinct_roles,false);
 assert.equal(separated.physical_model_validated,false);
 for(const bad of [
   {...src,flow:{...flow,parameter_cell_ref:"B4"},drag},
   {...src,flow,drag:{...drag,role:"flow_coefficient"}},
   {...src,flow,drag:{...drag,evidence_class:"observed"}},
   {...src,flow:{...flow,coordinates:[0,0]},drag},
   {...src,flow:{...flow,unit:"m/s"},drag},
   {...src,flow:{...flow,numeric_value:Infinity},drag},
   {...src,source_sha256:"invalid",flow,drag}
 ])assert.throws(()=>rolesReview(bad),/INVALID_SECOND_CYCLE_COEFFICIENT_ROLES/);
});

test("caller-declared translated coefficient pair preserves distinct roles without source equivalence",()=>{
 const src={source_ref:"synthetic:original",source_revision:"r1",source_sha256:"b".repeat(64)};
 const flow={formula_id:"FM-001",sheet_ref:"07_Flow_Mist_Model",
  parameter_cell_ref:"B5",role:"flow_coefficient",symbol:"Cd",
  numeric_value:0.4,unit:"ratio",evidence_class:"simulated"};
 const drag={formula_id:"FM-004",sheet_ref:"11_Anchor_Mooring",
  parameter_cell_ref:"B4",role:"drag_coefficient",symbol:"Cd",
  numeric_value:1.3,unit:"ratio",evidence_class:"simulated"};
 const tr={source_ref:"synthetic:translated",revision_ref:"r2",
  flow:{...flow,sheet_ref:"SECON0E3E_07_Flow_Mist_Model"},
  drag:{...drag,sheet_ref:"SECON0E3E_11_Anchor_Mooring"}};
 const ok=rolesReview({...src,flow,drag,translation:tr});
 assert.equal(ok.translation_crosswalk.state,
  "R1_CALLER_DECLARED_COEFFICIENT_PAIR_MATCH_NOT_EQUIVALENCE");
 assert.equal(ok.translation_crosswalk.original_and_translation_equivalent,false);
 assert.equal(ok.translation_crosswalk.provider_cells_fetched_by_module,false);
 assert.equal(ok.translation_crosswalk.source_and_translation_revisions_authenticated_by_module,false);
 assert.equal(ok.native_admitted,false);
 const swap=rolesReview({...src,flow,drag,translation:{...tr,
  flow:{...tr.flow,numeric_value:drag.numeric_value},
  drag:{...tr.drag,numeric_value:flow.numeric_value}}});
 assert.equal(swap.translation_crosswalk.state,"R1_COEFFICIENT_TRANSLATION_DELTA_HOLD");
 assert.equal(swap.translation_crosswalk.suspected_cross_role_baseline_swap,true);
 assert.equal(swap.translation_crosswalk.coefficient_interchange_allowed,false);
 assert.equal(JSON.stringify(swap).includes("1.3"),false);
 const drift=rolesReview({...src,flow,drag,translation:{...tr,
  drag:{...tr.drag,numeric_value:1.4}}});
 assert.equal(drift.translation_crosswalk.drag_role_and_baseline_match,false);
 assert.equal(drift.translation_crosswalk.suspected_cross_role_baseline_swap,false);
 for(const bad of [
  {...tr,source_ref:src.source_ref},
  {...tr,revision_ref:""},
  {...tr,flow:{...tr.flow,sheet_ref:"07_Flow_Mist_Model"}},
  {...tr,drag:{...tr.drag,role:"flow_coefficient"}},
  {...tr,flow:{...tr.flow,evidence_class:"observed"}},
  {...tr,flow:{...tr.flow,unit:"m/s"}},
  {...tr,drag:{...tr.drag,numeric_value:Infinity}},
  {...tr,extra:"not allowed"}
 ])assert.throws(()=>rolesReview({...src,flow,drag,translation:bad}),
  /INVALID_SECOND_CYCLE_TRANSLATION/);
});
