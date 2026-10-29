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
