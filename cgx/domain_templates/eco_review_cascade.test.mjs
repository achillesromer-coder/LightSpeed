import test from "node:test";
import {createHash} from "node:crypto";
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

const originalBytes=Buffer.from("synthetic source fixture; not a Drive original","utf8");
const fixtureSha=createHash("sha256").update(originalBytes).digest("hex");
const metadata={id:source.id,revision:source.revision,
  modified_time:"2026-05-19T23:33:23.000Z",
  size:originalBytes.byteLength,
  mime_type:"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"};
const source_snapshot={metadata,original_bytes:originalBytes,
  expected_sha256:fixtureSha};
const integrated=(snapshot=source_snapshot)=>runEcoReviewCascade({
  source,scope,novel,domain:"second_cycle_claim",
  record:{...claim,source_sha256:fixtureSha,source_revision:source.revision},
  source_snapshot:snapshot
});

test("source-byte SHA256 and current revision bind into actual alignment and claim execution",()=>{
 const result=integrated();
 assert.equal(result.source_reference.bytes_read_this_execution,true);
 assert.equal(result.source_reference.hash_verified_this_execution,true);
 assert.equal(result.source_reference.caller_source_snapshot_attested,false);
 assert.equal(result.source_proof.sha256,fixtureSha);
 assert.equal(result.source_proof.original_byte_length,originalBytes.length);
 assert.equal(result.source_proof.metadata_revision_matched,true);
 assert.equal(result.source_proof.metadata_and_bytes_origin_authenticated_by_module,false);
 assert.ok(result.step_receipts.ecological_review.flags.includes(
  "HYDRODYNAMIC_BENCH_CALIBRATION_REQUIRED"));
 assert.equal(result.release_gates.native_admitted,false);
 assert.equal(result.release_gates.owner_accepted,false);
 assert.equal(JSON.stringify(result).includes("synthetic source fixture"),false);
});
test("byte tampering fails before qualified ecological review",()=>{
 assert.throws(()=>integrated({...source_snapshot,
  original_bytes:Buffer.from("synthetic source fixture; not a Drive originaL")}),
  /ECO_SOURCE_ORIGINAL_BYTES_HASH_MISMATCH|ECO_SOURCE_REVISION_SIZE_OR_BYTES_MISMATCH/);
});
test("revision, source ID and byte-count mismatches fail closed",()=>{
 for(const changed of [
  {...metadata,revision:"different-revision"},
  {...metadata,id:"other-drive-file"},
  {...metadata,size:metadata.size+1}
 ])assert.throws(()=>integrated({...source_snapshot,metadata:changed}),
  /ECO_SOURCE_REVISION_SIZE_OR_BYTES_MISMATCH/);
});
test("invalid checksum and unsupported file format fail closed",()=>{
 assert.throws(()=>integrated({...source_snapshot,expected_sha256:"not-hash"}),
  /ECO_SOURCE_REVISION_SIZE_OR_BYTES_MISMATCH/);
 assert.throws(()=>integrated({...source_snapshot,
  metadata:{...metadata,mime_type:"application/octet-stream"}}),
  /ECO_SOURCE_REVISION_SIZE_OR_BYTES_MISMATCH/);
});
test("oversized, absent and unzoned version metadata never qualify",()=>{
 for(const changed of [
  {...metadata,size:60*1024*1024+1},
  {...metadata,modified_time:"yesterday"},
  {...metadata,modified_time:"2026-05-19"}
 ])assert.throws(()=>integrated({...source_snapshot,metadata:changed}),
  /ECO_SOURCE_REVISION_SIZE_OR_BYTES_MISMATCH/);
});
test("only Drive source snapshots are accepted by this scoped adapter",()=>{
 assert.throws(()=>runEcoReviewCascade({source:{...source,provider:"github"},
  scope,novel,domain:"second_cycle_claim",record:claim,source_snapshot}),
  /INVALID_ECO_SOURCE_SNAPSHOT/);
});

test("a real source digest must match the exact claim's declared digest",()=>{
 assert.throws(()=>runEcoReviewCascade({
  source,scope,novel,domain:"second_cycle_claim",
  record:{...claim,source_revision:source.revision,
   source_sha256:"0".repeat(64)},source_snapshot}),
  /ECO_CLAIM_SNAPSHOT_BINDING_REQUIRED_OR_CONFLICT/);
});
test("a real source snapshot cannot be attached to an unbound claim",()=>{
 assert.throws(()=>runEcoReviewCascade({
  source,scope,novel,domain:"second_cycle_claim",
  record:claim,source_snapshot}),
  /ECO_CLAIM_SNAPSHOT_BINDING_REQUIRED_OR_CONFLICT/);
});
test("cross-revision claim lineage is rejected even without source bytes",()=>{
 assert.throws(()=>runEcoReviewCascade({
  source,scope,novel,domain:"second_cycle_claim",
  record:{...claim,source_revision:"different-revision"}}),
  /ECO_CLAIM_SOURCE_REVISION_CONFLICT/);
});
test("uppercase hexadecimal digest is equivalent to the exact verified digest",()=>{
 const r=runEcoReviewCascade({source,scope,novel,
  domain:"second_cycle_claim",
  record:{...claim,source_revision:source.revision,
   source_sha256:fixtureSha.toUpperCase()},
  source_snapshot});
 assert.equal(r.source_reference.hash_verified_this_execution,true);
 assert.equal(r.release_gates.native_admitted,false);
});
