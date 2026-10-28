/** Synthetic byte fixtures only. No owner files, host, DBR, upload, Vite build or HTTP. */
import {test} from "node:test";
import assert from "node:assert/strict";
import {webcrypto} from "node:crypto";
import {planPrivateR3Card} from "./cgxUniSpacePrivateR3Card.mjs";
import {preflightPrivateObjectDrop} from "./cgxUniSpacePrivateDropPreflight.mjs";

if (!globalThis.crypto) globalThis.crypto = webcrypto;
const HELLO_SHA256 = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824";
function fixture() {
  const selection = {
    parent_filespace:"Cognigrex.cgx", object_id:"WT-001", filespace:"Romer.cgx",
    identity_status:"SOURCE_CANDIDATE_NOT_NATIVE_ACCEPTED"
  };
  const source = {
    object_id:"WT-001", filespace:"Romer.cgx", mapping_id:"FF-WATCHTOWER-FCSTD-001",
    mapping_blob_sha:"15ac42e257220e0efd30c8521fe2c319b9a25013",
    r0_source_sha256:"c476f9f2f9946ab8e99e58dd399aa7b02bac630c5d9336b80ef66f5f2a397321",
    evidence_class:"scientific", rights:"UNRESOLVED", mapping_stage:"R0_R1_R2_REFERENCE",
    private_source_locator:"DO_NOT_LEAK_PRIVATE_LOCATOR"
  };
  const client = {mode:"review_only",revoked:false,allowed_object_ids:["WT-001"],allowed_filespaces:["Romer.cgx"]};
  const card = planPrivateR3Card({selection,source,client,request:{view:"document",requested_hydration:"H0"}});
  const bytes = new TextEncoder().encode("hello");
  return {selection,source,client,card,drop:{files:[{
    name:"watchtower_note.txt",mime:"text/plain",size:bytes.byteLength,bytes
  }]}};
}
const run = x => preflightPrivateObjectDrop(x);

test("exact candidate gets a computed byte SHA-256, but no intake", async () => {
  const r=await run(fixture());
  assert.equal(r.state,"R0_HASHED_PREFLIGHT_HOLD");
  assert.equal(r.candidate_r0_sha256,HELLO_SHA256);
  assert.equal(r.candidate_object_id,"WT-001");
  assert.equal(r.child_filespace,"Romer.cgx");
  assert.equal(r.recommended_route,"CGX_NATIVE_INTAKE_PRECHECK_ONLY");
});
test("rights unresolved and R0 source reference not confused with dropped bytes", async () => {
  const r=await run(fixture());
  assert.equal(r.rights_status,"UNVERIFIED");
  assert.equal(r.source_reference_hash_verified,false);
  assert.equal(r.identity_collision_checked,false);
  assert.equal(r.format_parsed,false);
});
test("no private locator, filename or raw source bytes in output", async () => {
  const r=await run(fixture());
  const out=JSON.stringify(r);
  assert.doesNotMatch(out,/DO_NOT_LEAK_PRIVATE_LOCATOR|watchtower_note|68656c6c6f/);
  assert.equal(r.source_bytes_embedded,false);
  assert.equal(r.public_vite_asset,false);
});
test("no effectful or live claims", async () => {
  const r=await run(fixture());
  for(const k of ["native_admitted","host_verified","release_accepted","canonical_mutation","upload_performed","bytes_persisted","network_fetch","r1_typed","r2_modelled","r3_live"]) assert.equal(r[k],false,k);
  assert.equal(r.display_hydration,"H0_REFERENCE_ONLY");
});
test("revoked review client denied", async () => {
  const x=fixture();x.client.revoked=true;assert.equal((await run(x)).hold_code,"CLIENT_SCOPE_MISMATCH");
});
test("cross-FileSpace client denied", async () => {
  const x=fixture();x.client.allowed_filespaces=["Eco.cgx"];assert.equal((await run(x)).state,"HOLD");
});
test("cross-object selection denied", async () => {
  const x=fixture();x.selection.object_id="WT-002";assert.equal((await run(x)).state,"HOLD");
});
test("forged host-verified card denied", async () => {
  const x=fixture();x.card={...x.card,host_verified:true};assert.equal((await run(x)).hold_code,"UNTRUSTED_CARD");
});
test("source mapping blob swap denied", async () => {
  const x=fixture();x.source.mapping_blob_sha="f".repeat(40);assert.equal((await run(x)).hold_code,"SOURCE_PROVENANCE_MISMATCH");
});
test("multiple files denied", async () => {
  const x=fixture();x.drop.files.push({...x.drop.files[0]});assert.equal((await run(x)).hold_code,"EXACTLY_ONE_FILE_REQUIRED");
});
test("path traversal and disguised filename denied", async () => {
  for(const name of ["../note.txt","folder/note.txt","folder\\note.txt",".hidden.txt","note..txt"]){
    const x=fixture();x.drop.files[0].name=name;assert.equal((await run(x)).hold_code,"UNSAFE_FILE_NAME",name);
  }
});
test("active script and mismatched MIME denied", async () => {
  for(const [name,mime] of [["payload.html","text/html"],["payload.svg","image/svg+xml"],["note.txt","text/html"]]){
    const x=fixture();x.drop.files[0].name=name;x.drop.files[0].mime=mime;
    assert.equal((await run(x)).hold_code,"UNSUPPORTED_TYPE_OR_MIME",name);
  }
});
test("declared size mismatch denied", async () => {
  const x=fixture();x.drop.files[0].size=6;assert.equal((await run(x)).hold_code,"BYTE_LENGTH_OR_LIMIT_MISMATCH");
});
test("invalid or over-limit transfer denied", async () => {
  const x=fixture();x.max_bytes=4;assert.equal((await run(x)).hold_code,"BYTE_LENGTH_OR_LIMIT_MISMATCH");
  x.max_bytes=60*1024*1024+1;assert.equal((await run(x)).hold_code,"INVALID_TRANSFER_LIMIT");
});
test("incorrect declared hash denied", async () => {
  const x=fixture();x.drop.files[0].claimed_sha256="0".repeat(64);assert.equal((await run(x)).hold_code,"HASH_MISMATCH");
});
test("correct declared hash accepted only for R0 preflight", async () => {
  const x=fixture();x.drop.files[0].claimed_sha256=HELLO_SHA256;
  const r=await run(x);assert.equal(r.state,"R0_HASHED_PREFLIGHT_HOLD");assert.equal(r.native_admitted,false);
});
test("a claimed PRIVATE_SCOPED right cannot grant release", async () => {
  const x=fixture();x.source.rights="PRIVATE_SCOPED";
  const r=await run(x);assert.equal(r.rights_status,"UNVERIFIED");assert.equal(r.release_accepted,false);
});

test("source mapping stage drift denied before hashing", async () => {
  const x=fixture();x.source.mapping_stage="R0_R1_REFERENCE";
  const r=await run(x);
  assert.equal(r.hold_code,"SOURCE_PROVENANCE_MISMATCH");
  assert.equal(r.network_fetch,false);
  assert.equal(r.native_admitted,false);
});
test("unsupported source mapping stage denied", async () => {
  const x=fixture();x.source.mapping_stage="R3_ADMITTED";
  assert.equal((await run(x)).hold_code,"SOURCE_PROVENANCE_MISMATCH");
});
