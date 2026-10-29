import test from "node:test";
import assert from "node:assert/strict";
import {qualifySecondCycleProxy} from "./second_cycle_proxy_review.mjs";
const source={id:"source:synthetic",revision:"rev:synthetic",sha256:"a".repeat(64)};
const inputs={
 current_speed:{value:1,unit:"m/s"},intake_area:{value:0.01,unit:"m2"},
 flow_coefficient:{value:0.5,unit:"1"},mist_fraction:{value:0.1,unit:"1"},
 water_density:{value:1000,unit:"kg/m3"}
};
const run=(patch={})=>qualifySecondCycleProxy({source,inputs,...patch});
test("dimensional flow, mist, pressure and hydraulic-power proxies are consistent",()=>{
 const r=run();assert.equal(r.calculated.volumetric_flow_lps,5);
 assert.equal(r.calculated.mist_output_lps,0.5);
 assert.equal(r.calculated.dynamic_pressure_pa,500);
 assert.equal(r.calculated.hydraulic_power_w,2.5);
 assert.equal(r.native_admitted,false);assert.equal(r.ecological_effect_verified,false);
});
test("unit mismatch is rejected",()=>assert.throws(()=>run({inputs:{...inputs,current_speed:{value:1,unit:"km/h"}}}),/INVALID_PHYSICAL_QUANTITY/));
test("fraction outside physical range is rejected",()=>assert.throws(()=>run({inputs:{...inputs,mist_fraction:{value:1.2,unit:"1"}}}),/PHYSICAL_PROXY_DOMAIN_ERROR/));
test("reported output discrepancy remains visible",()=>{
 const r=run({reported:{mist_output_lps:{value:2,unit:"L/s"}}});
 assert.ok(r.review_flags.includes("REPORTED_PROXY_MISMATCH_MIST_OUTPUT_LPS"));
});
test("observed mist cannot be inferred from proxy",()=>{
 const r=run({claimed_observed_mist:true});
 assert.ok(r.review_flags.includes("OBSERVED_MIST_CLAIM_REQUIRES_INDEPENDENT_VALIDATION"));
 assert.equal(r.observed_mist_verified,false);
});
test("even references cannot self-certify ecological benefit",()=>{
 const r=run({source:{...source,rights_review_ref:"rights:synthetic"},
 evidence:{flume_calibration_ref:"flume:synthetic",nozzle_characterisation_ref:"nozzle:synthetic",mist_measurement_ref:"mist:synthetic"},
 claimed_ecological_benefit:true});
 assert.ok(r.review_flags.includes("ECOLOGICAL_BENEFIT_CLAIM_BLOCKED"));
 assert.equal(r.ecological_effect_verified,false);
});
test("claimed atomisation demand beyond idealised hydraulic proxy is flagged",()=>{
 const r=run({required_atomisation_power_w:3});
 assert.ok(r.review_flags.includes("ATOMISATION_ENERGY_EXCEEDS_IDEALISED_PROXY"));
});
test("synthetic residence index cannot be relabelled as physical residence time",()=>{
 assert.ok(run({residence_index_claimed_as_time:true}).review_flags.includes("RESIDENCE_INDEX_NOT_A_VALIDATED_TIME"));
});
test("source revision and raw hash are preserved without Object_ID minting",()=>{
 const r=run();assert.deepEqual(r.source,source);
 assert.equal(r.stage,"R2_REVIEW_CANDIDATE");assert.equal(r.live_installed,false);
});
test("malformed reported units and source hashes are rejected",()=>{
 assert.throws(()=>run({reported:{volumetric_flow_lps:{value:5,unit:"m/s"}}}),/INVALID_REPORTED_UNIT/);
 assert.throws(()=>run({source:{...source,sha256:"not-a-hash"}}),/SOURCE_ID_REVISION_HASH_REQUIRED/);
});

test("original-concept rainfall and weather claims remain unverified",()=>{
 const a=run({claimed_rainfall_induction:true,claimed_weather_modification:true});
 assert.ok(a.review_flags.includes("RAINFALL_INDUCTION_UNVERIFIED"));
 assert.ok(a.review_flags.includes("WEATHER_MODIFICATION_UNVERIFIED"));
 assert.equal(a.ecological_effect_verified,false);
});
test("coral recovery is not inferred from passive-flow proxy",()=>{
 const a=run({claimed_coral_recovery:true});
 assert.ok(a.review_flags.includes("CORAL_RECOVERY_UNVERIFIED"));
 assert.equal(a.native_admitted,false);
});
test("carbon sequestration needs independent measurement and baseline",()=>{
 const a=run({claimed_carbon_sequestration:true});
 assert.ok(a.review_flags.includes("CARBON_SEQUESTRATION_UNVERIFIED"));
 assert.equal(a.ecological_effect_verified,false);
});
test("pump-free is not energy-free: moving water supplies kinetic energy",()=>{
 const a=run({claimed_pump_free_as_energy_free:true});
 assert.ok(a.review_flags.includes("AMBIENT_CURRENT_IS_AN_ENERGY_SOURCE"));
 assert.equal(a.live_installed,false);
});
test("absent source claims do not silently appear as measured outcomes",()=>{
 const a=run();
 for(const k of ["RAINFALL_INDUCTION_UNVERIFIED","WEATHER_MODIFICATION_UNVERIFIED",
  "CORAL_RECOVERY_UNVERIFIED","CARBON_SEQUESTRATION_UNVERIFIED"])
  assert.equal(a.review_flags.includes(k),false);
 assert.equal(a.observed_mist_verified,false);
});


test("source-backed baseline current yields only 3.26 cm ideal current-only stagnation head",()=>{
 const b={...inputs,current_speed:{value:0.8,unit:"m/s"},intake_area:{value:0.02,unit:"m2"},
  flow_coefficient:{value:0.6,unit:"1"},mist_fraction:{value:0.08,unit:"1"},
  water_density:{value:1025,unit:"kg/m3"}};
 const a=run({inputs:b});
 assert.ok(Math.abs(a.calculated.ideal_current_only_head_m-0.03263)<0.00001);
 assert.ok(a.review_flags.includes("IDEAL_CURRENT_ONLY_HEAD_NOT_OBSERVED"));
 assert.equal(a.observed_mist_verified,false);
});
test("claimed current-only spout exceeding ideal stagnation head is flagged",()=>{
 const a=run({claimed_current_only_spout_height_m:1});
 assert.ok(a.review_flags.includes("SPOUT_HEIGHT_EXCEEDS_IDEAL_CURRENT_ONLY_HEAD"));
});
test("passing ideal head check does not establish a real jet or mist",()=>{
 const a=run({claimed_current_only_spout_height_m:0.01});
 assert.equal(a.review_flags.includes("SPOUT_HEIGHT_EXCEEDS_IDEAL_CURRENT_ONLY_HEAD"),false);
 assert.equal(a.observed_mist_verified,false);
});
test("negative or nonnumeric current-only spout heights are rejected",()=>{
 assert.throws(()=>run({claimed_current_only_spout_height_m:-0.1}),/INVALID_CLAIMED_CURRENT_ONLY_SPOUT_HEIGHT_M/);
 assert.throws(()=>run({claimed_current_only_spout_height_m:"1"}),/INVALID_CLAIMED_CURRENT_ONLY_SPOUT_HEIGHT_M/);
});

test("unquantified valve and nozzle losses remain review-gated",()=>{
 const r=run();
 assert.ok(r.review_flags.includes("HYDRAULIC_PATH_LOSSES_UNQUANTIFIED"));
 assert.equal(r.hydraulic_path_review,null);
});
test("synthetic nozzle demand above ideal current dynamic pressure is flagged",()=>{
 const r=run({hydraulic_path_review:{
  valve_pressure_drop:{value:0,unit:"Pa"},nozzle_pressure_required:{value:1000,unit:"Pa"},
  other_pressure_drop:{value:0,unit:"Pa"},static_lift:{value:0,unit:"m"},
  flow_coefficient_scope:"geometry_only",evidence_ref:"synthetic:pressure-curve"}});
 assert.ok(r.review_flags.includes("PRESSURE_BUDGET_EXCEEDS_IDEAL_CURRENT_DYNAMIC_PRESSURE"));
 assert.equal(r.hydraulic_path_review.physically_validated,false);
});
test("valve loss already in workbook coefficient cannot be subtracted twice without review",()=>{
 const r=run({hydraulic_path_review:{
  valve_pressure_drop:{value:20,unit:"Pa"},nozzle_pressure_required:{value:30,unit:"Pa"},
  other_pressure_drop:{value:0,unit:"Pa"},static_lift:{value:0,unit:"m"},
  flow_coefficient_scope:"includes_valve_losses"}});
 assert.ok(r.review_flags.includes("POTENTIAL_LOSS_DOUBLE_COUNT_REVIEW"));
 assert.ok(r.review_flags.includes("HYDRAULIC_PATH_EVIDENCE_REQUIRED"));
 assert.equal(r.observed_mist_verified,false);
});
test("hydraulic path units and negative static lift are rejected",()=>{
 const base={valve_pressure_drop:{value:0,unit:"Pa"},nozzle_pressure_required:{value:20,unit:"Pa"},
  other_pressure_drop:{value:0,unit:"Pa"},static_lift:{value:0,unit:"m"},
  flow_coefficient_scope:"geometry_only"};
 assert.throws(()=>run({hydraulic_path_review:{...base,nozzle_pressure_required:{value:20,unit:"kPa"}}}),/INVALID_HYDRAULIC_QUANTITY/);
 assert.throws(()=>run({hydraulic_path_review:{...base,static_lift:{value:-1,unit:"m"}}}),/INVALID_HYDRAULIC_QUANTITY/);
});
