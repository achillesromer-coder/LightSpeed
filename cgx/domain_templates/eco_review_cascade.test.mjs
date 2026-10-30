import test from "node:test";
import assert from "node:assert/strict";
import {runEcoReviewCascade} from "./eco_review_cascade.mjs";

// Synthetic review fixtures; real source material is never embedded here.
const source={provider:"drive",id:"synthetic-drive-id",revision:"synthetic-revision",
  source_ref:"synthetic-source-ref"};
const scope={authorised_source_ids:[source.source_ref]};
const novel={semantic_type:"ecological_state_estimate",source_refs:[source.source_ref],
  evidence_class:"source_asserted"};
const claim={claim_kind:"passive_flow",evidence_class:"source_asserted",
  source_ref:source.source_ref,numeric_value:6,unit:"L/s"};
const wrap=(domain,record,n=novel,s=source,sc=scope)=>
  runEcoReviewCascade({source:s,scope:sc,novel:n,domain,record});

test("actual Eco alignment and Second Cycle validator execute in one review cascade",()=>{
 const r=wrap("second_cycle_claim",claim);
 assert.equal(r.step_receipts.scoped_alignment.executed,true);
 assert.equal(r.step_receipts.ecological_review.executed,true);
 assert.equal(r.step_receipts.ecological_review.evidence_class,"source_asserted");
 assert.ok(r.step_receipts.ecological_review.flags.includes("HYDRODYNAMIC_BENCH_CALIBRATION_REQUIRED"));
 assert.equal(r.stage,"R1_REVIEW_ONLY");
 assert.equal(r.release_gates.native_admitted,false);
 assert.equal(r.release_gates.public_release_authorised,false);
 assert.equal(r.source_reference.hash_verified_this_execution,false);
});
test("actual BioBlocks monitoring validator executes under same scoped source",()=>{
 const n={...novel,semantic_type:"ecological_observation",evidence_class:"simulated"};
 const rec={evidence_class:"simulated",source_ref:source.source_ref,
  seed_count:100,germinated_count:45,surviving_count:20};
 const r=wrap("bioblock_monitoring",rec,n);
 assert.equal(r.step_receipts.ecological_review.executed,true);
 assert.ok(r.step_receipts.ecological_review.flags.includes("NONOBSERVED_COUNTS_CANNOT_ESTABLISH_FIELD_SURVIVAL"));
 assert.equal(r.release_gates.independent_science_validated,false);
});
test("unknown or unauthorised provider source cannot silently enter the cascade",()=>{
 assert.throws(()=>wrap("second_cycle_claim",claim,novel,source,{authorised_source_ids:[]}),
  /UNAUTHORISED_OR_INVALID/);
 assert.throws(()=>wrap("second_cycle_claim",claim,novel,{...source,provider:"local"}),
  /INVALID_ECO_SOURCE_IDENTITY/);
});
test("source-lineage mismatch and conflicting evidence class fail closed",()=>{
 assert.throws(()=>wrap("second_cycle_claim",{...claim,source_ref:"different-source"}),
  /ECO_DOMAIN_EVIDENCE_OR_SOURCE_CONFLICT/);
 assert.throws(()=>wrap("second_cycle_claim",{...claim,evidence_class:"observed"}),
  /ECO_DOMAIN_EVIDENCE_OR_SOURCE_CONFLICT/);
});
test("raw coordinates are excluded from review cascade",()=>{
 assert.throws(()=>wrap("second_cycle_claim",claim,{...novel,
   geometry:{type:"Point",coordinates:[153,-27],crs:"EPSG:4326"}}),
  /ECO_SOURCE_LINEAGE_OR_PRIVATE_GEOMETRY_HOLD/);
});
test("no identity or DBR admission from apparently complete source references",()=>{
 const r=wrap("second_cycle_claim",{...claim,source_sha256:"a".repeat(64),
  rights_review_ref:"synthetic-rights",stewardship_review_ref:"synthetic-stewardship"});
 assert.deepEqual(r.release_gates,{
  object_id_minted:false,native_admitted:false,db_readback:false,
  runtime_verified:false,independent_science_validated:false,
  owner_accepted:false,public_release_authorised:false
 });
 assert.equal(r.source_reference.bytes_read_this_execution,false);
});
