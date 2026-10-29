import test from "node:test";
import assert from "node:assert/strict";
import {reviewBioBlockMonitoringRecord as review, reviewBioBlockMonitoringSeries as series} from "./eco_bioblock_monitoring_review.mjs";
const base={source_ref:"synthetic-source",seed_count:220,germinated_count:12,
 surviving_count:8,monitoring_phase:"monthly"};
test("arithmetic count ratios are not verified field survival",()=>{
 const r=review(base);
 assert.equal(r.arithmetic_only_rates.germinated_per_seed,12/220);
 assert.equal(r.arithmetic_only_rates.surviving_per_germinated,8/12);
 assert.equal(r.field_observation_verified,false);
 assert.ok(r.flags.includes("NONOBSERVED_COUNTS_CANNOT_ESTABLISH_FIELD_SURVIVAL"));
});
test("observed label cannot substitute for date, denominator, controls or receipt",()=>{
 const r=review({evidence_class:"observed",monitoring_phase:"monthly"});
 for(const f of ["ZONED_OBSERVATION_TIMESTAMP_REQUIRED","SEED_DENOMINATOR_REQUIRED",
  "MONITORING_COUNTS_REQUIRED","MISSING_COHORT_REF","MISSING_REPLICATE_REF",
  "MISSING_CONTROL_REF","MISSING_RAW_DATA_REF","MISSING_SPATIAL_REVIEW_REF"])
  assert.ok(r.flags.includes(f));
});
test("complete-looking references never self-verify observations",()=>{
 const r=review({...base,evidence_class:"observed",observed_at:"2026-10-30T05:00:00+10:00",
  run_ref:"r",block_ref:"b",recipe_ref:"p",site_ref:"s",taxon_ref:"t",cohort_ref:"c",
  replicate_ref:"rep",method_ref:"m",baseline_ref:"base",control_ref:"ctrl",
  raw_data_ref:"raw",photo_ref:"photo",rights_review_ref:"rights",
  spatial_review_ref:"spatial"});
 assert.equal(r.field_observation_verified,false);
 assert.ok(r.flags.includes("INDEPENDENT_FIELD_RECEIPT_AND_QA_REQUIRED"));
});
test("invalid counts and percent bounds fail closed",()=>{
 for(const bad of [{seed_count:5},{germinated_count:4},{surviving_count:13},
  {weed_cover_pct:101},{soil_moisture:1.1,soil_moisture_unit:"m3/m3"},
  {soil_moisture:101,soil_moisture_unit:"percent"}])
  assert.throws(()=>review({...base,...bad}),/INVALID_BIOBLOCK_MONITORING_INPUT/);
});
test("untyped raw geometry and arbitrary metadata fail closed",()=>{
 for(const bad of [{gps:"-27.5,153.0"},{coordinates:[1,2]},{notes:{location:"x"}}])
  assert.throws(()=>review({...base,...bad}),/INVALID_BIOBLOCK_MONITORING_FIELDS/);
 assert.ok(review({...base,field_geometry_present:true}).flags.includes(
  "PRIVATE_GEOMETRY_OUTSIDE_REVIEW_BOUNDARY"));
});
test("moisture measurements require method, unit and calibration",()=>{
 const r=review({...base,soil_moisture:0.23,soil_moisture_unit:"m3/m3"});
 assert.ok(r.flags.includes("SOIL_MOISTURE_METHOD_AND_UNIT_REQUIRED"));
 assert.ok(r.flags.includes("SOIL_MOISTURE_CALIBRATION_REVIEW_REQUIRED"));
});
test("invalid dates and absent field receipts do not self-certify",()=>{
 const r=review({...base,evidence_class:"observed",observed_at:"2026-02-29T12:00:00Z"});
 assert.ok(r.flags.includes("ZONED_OBSERVATION_TIMESTAMP_REQUIRED"));
});
test("predeployment baseline does not demand postdeployment counts",()=>{
 const r=review({evidence_class:"observed",monitoring_phase:"pre_deployment",
  observed_at:"2026-10-30T05:00:00+10:00"});
 assert.ok(!r.flags.includes("MONITORING_COUNTS_REQUIRED"));
 assert.equal(r.field_observation_verified,false);
});

const longitudinalBase={...base,observed_at:"2026-10-01T00:00:00+10:00",
 run_ref:"run",block_ref:"block",recipe_ref:"recipe",site_ref:"site",taxon_ref:"taxon",
 cohort_ref:"cohort",replicate_ref:"rep",method_ref:"method",control_ref:"control",
 baseline_ref:"baseline"};
const later={...longitudinalBase,observed_at:"2026-10-30T00:00:00+10:00"};
test("matched synthetic series remains unverified, with no invented ecological effect",()=>{
 const r=series([longitudinalBase,later]);
 assert.equal(r.record_count,2);
 assert.equal(r.longitudinal_field_evidence_verified,false);
 assert.equal(r.biodiversity_gain_verified,false);
 assert.ok(!r.flags.includes("LONGITUDINAL_COUNTS_NOT_COMPARABLE"));
});
test("changed cohort cannot be silently pooled",()=>{
 const r=series([longitudinalBase,{...later,cohort_ref:"other"}]);
 assert.ok(r.flags.includes("SERIES_COHORT_REF_MISMATCH"));
 assert.ok(r.flags.includes("LONGITUDINAL_COUNTS_NOT_COMPARABLE"));
});
test("timepoint order must be strictly increasing in absolute time",()=>{
 const r=series([later,longitudinalBase]);
 assert.ok(r.flags.includes("NONINCREASING_LONGITUDINAL_TIME"));
});
test("changed seed denominator requires independent review",()=>{
 const r=series([longitudinalBase,{...later,seed_count:221}]);
 assert.ok(r.flags.includes("SEED_DENOMINATOR_CHANGED_REVIEW_REQUIRED"));
 assert.ok(r.flags.includes("LONGITUDINAL_COUNTS_NOT_COMPARABLE"));
});
test("increasing survivor count is reviewable, not automatically impossible",()=>{
 const r=series([longitudinalBase,{...later,surviving_count:9}]);
 assert.ok(r.flags.includes("SURVIVAL_INCREASE_REQUIRES_RECRUITMENT_OR_METHOD_REVIEW"));
 assert.equal(r.longitudinal_field_evidence_verified,false);
});
test("declining germination count requires cumulative versus interval metric clarification",()=>{
 const r=series([longitudinalBase,{...later,germinated_count:11}]);
 assert.ok(r.flags.includes("GERMINATION_DECREASE_REQUIRES_METRIC_SCOPE_REVIEW"));
});
test("missing timestamp prevents longitudinal comparison",()=>{
 const r=series([longitudinalBase,{...later,observed_at:null}]);
 assert.ok(r.flags.includes("LONGITUDINAL_ZONED_TIMESTAMPS_REQUIRED"));
});
test("mixed simulated and observed labels cannot establish a common measured series",()=>{
 const r=series([longitudinalBase,{...later,evidence_class:"observed"}]);
 assert.ok(r.flags.includes("MIXED_EVIDENCE_CLASSES_NOT_COMPARABLE"));
 assert.ok(r.flags.includes("LONGITUDINAL_COUNTS_NOT_COMPARABLE"));
});
test("raw spatial fields and unbounded series fail closed",()=>{
 assert.throws(()=>series([longitudinalBase,{...later,coordinates:[1,2]}]),
  /INVALID_BIOBLOCK_MONITORING_FIELDS/);
 assert.throws(()=>series([longitudinalBase]),/INVALID_BIOBLOCK_SERIES_LENGTH/);
 assert.throws(()=>series(Array(101).fill(longitudinalBase)),/INVALID_BIOBLOCK_SERIES_LENGTH/);
});
