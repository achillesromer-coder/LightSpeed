import test from "node:test";
import assert from "node:assert/strict";
import {reviewEcoObservationShowcase as review} from "./eco_digital_mint_boundary.mjs";
// Every record here is synthetic; none is a field observation or original Mint class payload.
const base={kind:"EcoObservation",synthetic:true,measured:false,evidence_class:"simulated",
 taxon:"synthetic:taxon",place:"synthetic:site",method:"synthetic:survey",
 source_provenance:"synthetic:gallery",source_revision_ref:"synthetic:v1",
 source_owner_ref:"synthetic:owner"};
const run=(record=base,extra={})=>review({record,authorised_source_refs:["synthetic:gallery"],...extra});
test("synthetic unmeasured example is source-only and never native",()=>{
 const x=run();assert.equal(x.state,"SCHEMA_BRIDGE_CANDIDATE_ONLY");
 assert.equal(x.accepted_native_identity,false);assert.equal(x.db_readback,false);
 assert.equal(x.field_observation_verified,false);assert.equal(x.public_release_authorised,false);
});
test("observed evidence cannot be asserted by a synthetic gallery fixture",()=>{
 const x=run({...base,evidence_class:"observed"});
 assert.ok(x.checks.includes("SYNTHETIC_FIXTURE_CANNOT_ASSERT_OBSERVED_EVIDENCE"));
 assert.ok(x.checks.includes("FIELD_EVIDENCE_INDEPENDENT_REVIEW_REQUIRED"));
});
test("measured flag alone does not create a measurement",()=>{
 assert.ok(run({...base,measured:true}).checks.includes("MEASURED_FLAG_REQUIRES_QUANTITY_AND_UNIT"));
});
test("unmeasured flag and numeric value are contradictory",()=>{
 assert.ok(run({...base,measurement:{value:1,unit:"mg/L"}}).checks.includes("UNMEASURED_FLAG_CONFLICTS_WITH_NUMERIC_MEASUREMENT"));
});
test("measured synthetic quantity remains simulated rather than observed",()=>{
 const x=run({...base,measured:true,measurement:{value:1,unit:"mg/L"}});
 assert.equal(x.state,"SCHEMA_BRIDGE_CANDIDATE_ONLY");
 assert.equal(x.field_observation_verified,false);
});
test("unscoped source is not admitted even with a matching display label",()=>{
 const x=run({...base,source_provenance:"private:source"});
 assert.ok(x.checks.includes("SOURCE_NOT_IN_AUTHORISED_SCOPE"));
 assert.deepEqual(x.permitted_source_refs,[]);
});
test("specimen identity remains distinct from taxon",()=>{
 assert.ok(run({...base,subject_kind:"specimen"}).checks.includes("SPECIMEN_IDENTITY_REQUIRED"));
});
test("public requests require owner, rights, ACL and spatial review",()=>{
 const x=run(base,{public_release_requested:true});
 for(const flag of ["PUBLIC_RELEASE_OWNER_APPROVAL_REQUIRED","PUBLIC_RIGHTS_REVIEW_REQUIRED",
  "PUBLIC_ACL_REVIEW_REQUIRED","SPATIAL_SENSITIVITY_REVIEW_REQUIRED",
  "NO_AUTOMATIC_SPECIMEN_OR_SITE_GEOMETRY_RELEASE"])assert.ok(x.checks.includes(flag));
 assert.equal(x.geometry_emitted,false);
});
test("even declared rights and sensitivity references cannot self-authorise release",()=>{
 const x=run({...base,rights_review_ref:"synthetic:rights",acl_review_ref:"synthetic:acl",
  spatial_sensitivity_review_ref:"synthetic:sensitivity"},{public_release_requested:true});
 assert.ok(x.checks.includes("PUBLIC_RELEASE_OWNER_APPROVAL_REQUIRED"));
 assert.equal(x.public_release_authorised,false);
});
test("observed non-synthetic record needs field receipt, zoned time and original hash",()=>{
 const x=run({...base,synthetic:false,evidence_class:"observed"});
 for(const flag of ["ORIGINAL_FIELD_RECEIPT_REQUIRED","ZONED_OBSERVATION_TIMESTAMP_REQUIRED",
  "SEASONAL_CONTEXT_REQUIRED","ORIGINAL_EVIDENCE_HASH_REQUIRED"])
  assert.ok(x.checks.includes(flag));
});
test("a complete-looking field record still requires independent field review",()=>{
 const x=run({...base,synthetic:false,evidence_class:"observed",field_record_ref:"synthetic:receipt",
  observed_at:"2026-10-29T10:00:00Z",seasonal_frame_ref:"synthetic:season",
  source_hash_sha256:"a".repeat(64)});
 assert.ok(x.checks.includes("FIELD_EVIDENCE_INDEPENDENT_REVIEW_REQUIRED"));
 assert.equal(x.field_observation_verified,false);
});
test("invalid measurement cannot enter bridge",()=>{
 assert.throws(()=>run({...base,measured:true,measurement:{value:Infinity,unit:"mg/L"}}),/INVALID_ECO_MINT_MEASUREMENT/);
});

test("impossible calendar date is rejected even when the timestamp is ISO-shaped",()=>{
 const x=run({...base,synthetic:false,evidence_class:"observed",field_record_ref:"synthetic:receipt",
  observed_at:"2026-02-29T10:00:00Z",seasonal_frame_ref:"synthetic:season",
  source_hash_sha256:"a".repeat(64)});
 assert.ok(x.checks.includes("ZONED_OBSERVATION_TIMESTAMP_REQUIRED"));
});

test("raw numeric coordinates cannot silently pass the source-only bridge",()=>{
 const x=run({...base,latitude:-27.5,longitude:153.1});
 assert.equal(x.state,"REVIEW_REQUIRED");
 assert.ok(x.checks.includes("RAW_SPATIAL_COORDINATES_NOT_ACCEPTED_IN_SOURCE_ONLY_BRIDGE"));
 assert.equal(x.geometry_emitted,false);
 assert.equal(x.public_release_authorised,false);
});
test("GeoJSON-like geometry is not accepted as a synthetic observation",()=>{
 const x=run({...base,geometry:{type:"Point",coordinates:[153.1,-27.5]}});
 assert.ok(x.checks.includes("RAW_SPATIAL_COORDINATES_NOT_ACCEPTED_IN_SOURCE_ONLY_BRIDGE"));
 assert.equal(x.native_object_id,null);
});
test("case-varied raw geometry keys are also review-gated",()=>{
 const x=run({...base,GeoJSON:{type:"Point",coordinates:[153.1,-27.5]}});
 assert.ok(x.checks.includes("RAW_SPATIAL_COORDINATES_NOT_ACCEPTED_IN_SOURCE_ONLY_BRIDGE"));
});
