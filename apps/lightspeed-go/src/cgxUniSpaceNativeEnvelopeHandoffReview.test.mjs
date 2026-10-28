/** Synthetic-only, no owner bytes, GitHub data, host, DBR, upload, or Vite public paths. */
import {test} from "node:test";
import assert from "node:assert/strict";
import {webcrypto} from "node:crypto";
import {planPrivateR3Card} from "./cgxUniSpacePrivateR3Card.mjs";
import {preflightPrivateObjectDrop} from "./cgxUniSpacePrivateDropPreflight.mjs";
import {reviewNativeEnvelopeHandoff} from "./cgxUniSpaceNativeEnvelopeHandoffReview.mjs";

if (!globalThis.crypto) globalThis.crypto = webcrypto;
const HELLO_SHA = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824";
async function fixture() {
  const selection = {
    parent_filespace:"Cognigrex.cgx",object_id:"WT-001",filespace:"Romer.cgx",
    identity_status:"SOURCE_CANDIDATE_NOT_NATIVE_ACCEPTED"
  };
  const source = {
    object_id:"WT-001",filespace:"Romer.cgx",mapping_id:"FF-WATCHTOWER-FCSTD-001",
    mapping_blob_sha:"15ac42e257220e0efd30c8521fe2c319b9a25013",
    r0_source_sha256:"c476f9f2f9946ab8e99e58dd399aa7b02bac630c5d9336b80ef66f5f2a397321",
    mapping_stage:"R0_R1_R2_REFERENCE",evidence_class:"scientific",
    rights:"UNRESOLVED",private_source_locator:"DO_NOT_ECHO_MAPPING_LOCATOR"
  };
  const client = {
    mode:"review_only",revoked:false,allowed_object_ids:["WT-001"],
    allowed_filespaces:["Romer.cgx"]
  };
  const card = planPrivateR3Card({
    selection,source,client,request:{view:"document",requested_hydration:"H0"}
  });
  const bytes = new TextEncoder().encode("hello");
  const preflight = await preflightPrivateObjectDrop({
    selection,source,client,card,
    drop:{files:[{name:"note.txt",mime:"text/plain",size:bytes.length,bytes}]}
  });
  assert.equal(preflight.state,"R0_HASHED_PREFLIGHT_HOLD");
  const envelope = {
    schema:"CGX-SOURCE-ENVELOPE/0.1",source_id:"src:"+HELLO_SHA,
    sha256:HELLO_SHA,byte_length:5,source_name:"DO_NOT_ECHO_FILENAME.txt",
    media_type:"text/plain",extension:".txt",adapter_id:"text-stdlib-v0.1",
    authority:"source",evidence_state:"OBSERVED",release_class:"Internal",
    envelope_sha256:"a".repeat(64),warnings:[],unresolved:[],
    native_preservation:{
      source_ref:"DO_NOT_ECHO_PRIVATE_PATH",source_sha256:HELLO_SHA,
      source_byte_length:5,adapter_version:"0.1",
      round_trip_claim:"SEMANTIC_PROJECTION_ONLY"
    },
    lineage:{parent_source_id:null,canonical_mutation:false,projection_only:true},
    projections:[{kind:"text",text:"DO_NOT_ECHO_PRIVATE_CONTENT"}]
  };
  return {selection,source,client,preflight,envelope};
}
const run = x => reviewNativeEnvelopeHandoff(x);

test("matches exact one-object R0 digest and native envelope schema, remains held",async()=>{
  const r=run(await fixture());
  assert.equal(r.state,"NATIVE_ENVELOPE_SHAPE_MATCH_REVIEW_HOLD");
  assert.equal(r.candidate_object_id,"WT-001");
  assert.equal(r.child_filespace,"Romer.cgx");
  assert.equal(r.candidate_source_id,"src:"+HELLO_SHA);
  assert.equal(r.envelope_shape_matched,true);
  assert.equal(r.registered_original_hash_string_match_only,false);
});
test("all effectful or authoritative states remain false",async()=>{
  const r=run(await fixture());
  for(const key of [
    "native_admitted","host_verified","owner_session_verified",
    "root_acl_verified","dbr_readback_verified","conversion_plan_verified",
    "source_rights_verified","registered_original_bytes_verified",
    "source_bytes_independently_verified","r1_typed","r2_modelled","r3_live",
    "upload_performed","network_fetch","canonical_mutation",
    "public_vite_asset","release_accepted"
  ]) assert.equal(r[key],false,key);
  assert.equal(r.hydration,"H0_REFERENCE_ONLY");
});
test("does not leak native source locator, projections, or owner mapping path",async()=>{
  const r=JSON.stringify(run(await fixture()));
  assert.doesNotMatch(r,/DO_NOT_ECHO|private_source_locator|source_name|source_ref|projections/);
});
test("forged R1 admission inside envelope is rejected",async()=>{
  const x=await fixture();x.envelope.admission_state="R1_ADMITTED";
  assert.equal(run(x).hold_code,"ENVELOPE_SOURCE_SHAPE_OR_DIGEST_MISMATCH");
});
test("cross-object preflight substitution denied",async()=>{
  const x=await fixture();x.preflight={...x.preflight,candidate_object_id:"WT-002"};
  assert.equal(run(x).hold_code,"UNTRUSTED_PREFLIGHT");
});
test("cross-domain FileSpace substitution denied",async()=>{
  const x=await fixture();x.selection.filespace="Eco.cgx";
  assert.equal(run(x).state,"HOLD");
});
test("revoked and cross-object clients denied",async()=>{
  const x=await fixture();x.client.revoked=true;
  assert.equal(run(x).hold_code,"CLIENT_SCOPE_MISMATCH");
  x.client.revoked=false;x.client.allowed_object_ids=["WT-002"];
  assert.equal(run(x).hold_code,"CLIENT_SCOPE_MISMATCH");
});
test("source mapping stage and rights drift denied",async()=>{
  const x=await fixture();x.source.mapping_stage="R3_ADMITTED";
  assert.equal(run(x).hold_code,"UNQUALIFIED_SOURCE_MAPPING");
  x.source.mapping_stage="R0_R1_R2_REFERENCE";x.source.rights="OWNER_APPROVED";
  assert.equal(run(x).hold_code,"UNQUALIFIED_SOURCE_MAPPING");
});
test("envelope source id must equal its SHA-256",async()=>{
  const x=await fixture();x.envelope.source_id="src:"+"f".repeat(64);
  assert.equal(run(x).hold_code,"ENVELOPE_SOURCE_SHAPE_OR_DIGEST_MISMATCH");
});
test("envelope digest, size, extension and native preservation must agree",async()=>{
  for(const mutate of [
    x=>x.envelope.sha256="f".repeat(64),
    x=>x.envelope.byte_length=6,
    x=>x.envelope.extension=".glb",
    x=>x.envelope.native_preservation.source_sha256="f".repeat(64),
    x=>x.envelope.native_preservation.source_byte_length=6
  ]) {
    const x=await fixture();mutate(x);
    assert.equal(run(x).hold_code,"ENVELOPE_SOURCE_SHAPE_OR_DIGEST_MISMATCH");
  }
});
test("canonical mutation or non-projection lineage denied",async()=>{
  for(const mutate of [
    x=>x.envelope.lineage.canonical_mutation=true,
    x=>x.envelope.lineage.projection_only=false,
    x=>x.envelope.lineage.parent_source_id="src:parent"
  ]) {
    const x=await fixture();mutate(x);
    assert.equal(run(x).hold_code,"ENVELOPE_SOURCE_SHAPE_OR_DIGEST_MISMATCH");
  }
});
test("claimed host admission in preflight is rejected",async()=>{
  const x=await fixture();x.preflight={...x.preflight,host_verified:true};
  assert.equal(run(x).hold_code,"UNTRUSTED_PREFLIGHT");
});
test("registered source hash equality is string comparison, not original verification",async()=>{
  const x=await fixture();x.source.r0_source_sha256=HELLO_SHA;
  const r=run(x);
  assert.equal(r.registered_original_hash_string_match_only,true);
  assert.equal(r.registered_original_bytes_verified,false);
  assert.equal(r.native_admitted,false);
});
test("missing source ref is held without echoing private values",async()=>{
  const x=await fixture();x.envelope.native_preservation.source_ref="";
  assert.equal(run(x).hold_code,"ENVELOPE_SOURCE_SHAPE_OR_DIGEST_MISMATCH");
});

// Contract-shape tests against native source_envelope_contract.json and
// desktop/LightSpeed_Runtime/lightspeed_runtime/source_intake.py.
test("native required envelope fields must exist before review shape match",async()=>{
  for (const key of ["source_name","media_type","adapter_id","authority",
    "evidence_state","release_class","projections","warnings","unresolved",
    "envelope_sha256"]) {
    const x=await fixture();delete x.envelope[key];
    assert.equal(run(x).hold_code,"ENVELOPE_SOURCE_SHAPE_OR_DIGEST_MISMATCH",key);
  }
});
test("native adapter version and round-trip claims must match current contract",async()=>{
  for (const mutate of [
    x=>delete x.envelope.native_preservation.adapter_version,
    x=>x.envelope.native_preservation.adapter_version="0.2",
    x=>x.envelope.native_preservation.round_trip_claim="SOURCE_BYTES_PRESERVED",
    x=>x.envelope.native_preservation.round_trip_claim="PARTIAL_PROJECTION_ONLY"
  ]) {
    const x=await fixture();mutate(x);
    assert.equal(run(x).hold_code,"ENVELOPE_SOURCE_SHAPE_OR_DIGEST_MISMATCH");
  }
});
test("native source_ref null is a valid no-path reference, never authenticated",async()=>{
  const x=await fixture();x.envelope.native_preservation.source_ref=null;
  const r=run(x);
  assert.equal(r.state,"NATIVE_ENVELOPE_SHAPE_MATCH_REVIEW_HOLD");
  assert.equal(r.owner_session_verified,false);
  assert.equal(r.dbr_readback_verified,false);
});


test("native adapter mapping is extension-specific and rejects cross-format substitutions",async()=>{
  const x=await fixture();
  x.envelope.adapter_id="json-stdlib-v0.1"; // .txt source cannot claim JSON adapter
  assert.equal(run(x).hold_code,"ENVELOPE_SOURCE_SHAPE_OR_DIGEST_MISMATCH");
  x.envelope.adapter_id="text-stdlib-v0.1";
  x.envelope.extension=".json"; // extension drift must also fail
  assert.equal(run(x).hold_code,"ENVELOPE_SOURCE_SHAPE_OR_DIGEST_MISMATCH");
});

test("native source_intake adapter mapping matches all supported private preflight extensions",async()=>{
  // Synthetic envelope shape only; no actual format parsing or native execution.
  const pairs=[
    ["txt","text-stdlib-v0.1"],["md","text-stdlib-v0.1"],
    ["csv","csv-stdlib-v0.1"],["json","json-stdlib-v0.1"],
    ["pdf","pdf-pypdf-v0.1"],["png","image-metadata-stdlib-v0.1"],
    ["jpg","image-metadata-stdlib-v0.1"],["jpeg","image-metadata-stdlib-v0.1"],
    ["webp","image-reference-v0.1"],["obj","obj-mesh-stdlib-v0.1"],
    ["stl","stl-mesh-stdlib-v0.1"],["glb","gltf-stdlib-v0.1"],
    ["gltf","gltf-stdlib-v0.1"]
  ];
  for(const [ext,adapter] of pairs){
    const x=await fixture();
    x.preflight={...x.preflight,file_type:ext};
    x.envelope.extension="."+ext;
    x.envelope.adapter_id=adapter;
    assert.equal(run(x).state,"NATIVE_ENVELOPE_SHAPE_MATCH_REVIEW_HOLD",ext);
    x.envelope.adapter_id=adapter==="text-stdlib-v0.1"?"json-stdlib-v0.1":"text-stdlib-v0.1";
    assert.equal(run(x).hold_code,"ENVELOPE_SOURCE_SHAPE_OR_DIGEST_MISMATCH",ext);
  }
});

test("untrusted identity and digest primitive-type coercion fails closed",async()=>{
  const cases=[
    [x=>{x.selection.object_id=42;}, "UNQUALIFIED_OBJECT"],
    [x=>{x.selection.object_id=Object("WT-001");}, "UNQUALIFIED_OBJECT"],
    [x=>{x.source.r0_source_sha256=[x.source.r0_source_sha256];}, "UNQUALIFIED_SOURCE_MAPPING"],
    [x=>{x.source.mapping_blob_sha=[x.source.mapping_blob_sha];}, "UNQUALIFIED_SOURCE_MAPPING"],
    [x=>{x.preflight.candidate_r0_sha256=[HELLO_SHA];}, "UNTRUSTED_PREFLIGHT"],
    [x=>{x.preflight.file_type=["txt"];}, "UNTRUSTED_PREFLIGHT"],
    [x=>{x.envelope.sha256=[HELLO_SHA];}, "ENVELOPE_SOURCE_SHAPE_OR_DIGEST_MISMATCH"],
    [x=>{x.envelope.envelope_sha256=["a".repeat(64)];}, "ENVELOPE_SOURCE_SHAPE_OR_DIGEST_MISMATCH"]
  ];
  for(const [mutate,code] of cases){
    const x=await fixture();mutate(x);
    const r=assert.doesNotThrow(()=>run(x));
    // doesNotThrow returns undefined in Node; inspect a separate deterministic call.
    assert.equal(run(x).hold_code,code);
  }
});
