import test from "node:test";
import assert from "node:assert/strict";
import {SCHEMA,packR0Reference,unpackR0Reference,planR0ReferenceHydration,planR0LeafPacket,LEAF_PACKET_SCHEMA} from "./loadFractalReference.mjs";
const sample=Object.freeze({
 candidate_key:"candidate:emassc:wad-leaf",owner_domain:"emassc",
 file_space:"EMASSC.cgx",parent_file_space:"Cognigrex.cgx",
 source_ref:"fixture:creative-wad",source_sha256:"a".repeat(64),
 source_version:"v0-original",source_byte_length:109351151,rights:"OWNER_PRIVATE",
 operator_ref:"fixture:external-codec-not-executed",operator_version:"0.1",
 children:["candidate:emassc:textures"],residual_ref:"fixture:residual",
 geometry_profile:"fixture:grid-8-unverified"
});
const pack=()=>packR0Reference(sample);
const scope={authorized_keys:[sample.candidate_key,...sample.children],
 authorized_source_refs:[sample.source_ref],source_sha256:sample.source_sha256};
const plan=more=>planR0ReferenceHydration({tuple:pack(),...scope,...more});
test("reversible exact R0 metadata shorthand roundtrips without source-body copy",()=>{
 const tuple=pack();assert.equal(tuple[0],SCHEMA);
 assert.deepEqual(unpackR0Reference(tuple),sample);
 assert.deepEqual(packR0Reference(unpackR0Reference(tuple)),tuple);
 assert.equal(plan({level:2}).source_bytes_read,0);
});
test("private H0 shows no source ref or child information",()=>{
 const r=plan();assert.equal(r.state,"SOURCE_REFERENCE_ONLY");
 assert.equal(r.source_ref,null);assert.deepEqual(r.children,[]);
 assert.equal(r.source_sha256,null);assert.equal(r.native_admission,false);
});
test("H1 filters child references to explicit object scope",()=>{
 const r=plan({level:1,authorized_keys:[sample.candidate_key]});
 assert.deepEqual(r.children,[]);
 assert.ok(!JSON.stringify(r).includes("candidate:emassc:textures"));
});
test("H2 surfaces only source-bound metadata; never hydrates raw bytes",()=>{
 const r=plan({level:2});assert.equal(r.source_ref,sample.source_ref);
 assert.equal(r.operator_ref,sample.operator_ref);assert.equal(r.operator_executed,false);
 assert.equal(r.source_body_hydrated,false);assert.equal(r.object_id_minted,null);
});
test("authorization and wrong source hash fail closed without leaking private reference",()=>{
 const no=plan({authorized_source_refs:[]});assert.equal(no.state,"DENIED");
 assert.ok(!JSON.stringify(no).includes(sample.source_ref));
 const bad=plan({source_sha256:"b".repeat(64)});assert.equal(bad.reason,"SOURCE_BYTES_IDENTITY_MISMATCH");
});
test("private, restricted and unknown source material cannot project public",()=>{
 for(const rights of ["OWNER_PRIVATE","LICENSE_RESTRICTED","UNKNOWN"]){
  const tuple=packR0Reference({...sample,rights});
  const r=planR0ReferenceHydration({tuple,...scope,surface:"public"});
  assert.equal(r.reason,"SOURCE_PUBLIC_RIGHTS_HOLD");
 }
});
test("public-safe marker is still not native accepted or published",()=>{
 const r=planR0ReferenceHydration({tuple:packR0Reference({...sample,rights:"PUBLIC_SAFE"}),
  ...scope,surface:"public",level:2});
 assert.equal(r.state,"SOURCE_REFERENCE_ONLY");assert.equal(r.public_release,false);
});
test("structural aliases, extra fields and parent conflicts are denied",()=>{
 assert.throws(()=>packR0Reference({...sample,unaccounted_private:"secret"}),/LOSSLESS_FIELD_SET_REQUIRED/);
 assert.throws(()=>packR0Reference({...sample,parent_file_space:"Cognigrex.cgx",owner_domain:"ls"}),/FAMILY_SCOPE_CONFLICT/);
 assert.throws(()=>packR0Reference({...sample,candidate_key:"cgx:minted"}),/NATIVE_ID_NOT_MINTED/);
});
test("invalid or duplicated children and self-reference are denied",()=>{
 assert.throws(()=>packR0Reference({...sample,children:[sample.candidate_key]}),/INVALID_CHILD_REFS/);
 assert.throws(()=>packR0Reference({...sample,children:[...sample.children,...sample.children]}),/INVALID_CHILD_REFS/);
});
test("noncanonical/Unicode invisible identity and mismatched digest denied",()=>{
 const tuple=[...pack()];tuple[1]="candidate:emassc:\u202Efake";
 assert.equal(planR0ReferenceHydration({tuple,...scope}).state,"DENIED");
 assert.throws(()=>packR0Reference({...sample,source_sha256:"a".repeat(63)}),/UNQUALIFIED_SOURCE_SHA/);
});
test("request budget is per chunk; source may be larger than 60 MiB",()=>{
 assert.equal(plan({requested_work_bytes:1024}).state,"SOURCE_REFERENCE_ONLY");
 assert.equal(plan({requested_work_bytes:60*1024*1024+1}).reason,"INVALID_HYDRATION_SCOPE");
});

test("leaf transport is deterministic metadata only, not a compressed or issued source",()=>{
 const r=planR0LeafPacket({tuple:pack(),...scope,requested_leaf_keys:sample.children});
 assert.equal(r.schema,LEAF_PACKET_SCHEMA);
 assert.equal(r.state,"UNSIGNED_METADATA_PLAN_ONLY");
 assert.deepEqual(r.leaves,[{candidate_key:sample.children[0],stage:"REFERENCE_ONLY",source_hash:null,rights_verified:false}]);
 assert.equal(r.source_sha256,sample.source_sha256);
 assert.equal(r.raw_source_included,false);
 assert.equal(r.payload_bytes_transferred,0);
 assert.equal(r.source_bytes_read,0);
 assert.equal(r.codec_compression_verified,false);
 assert.equal(r.native_mint,false);
 assert.equal(r.public_release,false);
 assert.ok(r.metadata_utf8_bytes<=r.max_packet_bytes);
 assert.deepEqual(planR0LeafPacket({tuple:pack(),...scope,requested_leaf_keys:sample.children}),r);
});
test("skeletal packet can carry zero leaf references without treating source bytes as present",()=>{
 const r=planR0LeafPacket({tuple:pack(),...scope});
 assert.deepEqual(r.leaves,[]);
 assert.equal(r.source_byte_length,sample.source_byte_length);
 assert.equal(r.payload_bytes_transferred,0);
});
test("leaf-only scope, duplicate requests and sibling injection fail closed",()=>{
 const blocked=planR0LeafPacket({tuple:pack(),...scope,authorized_keys:[sample.candidate_key],requested_leaf_keys:sample.children});
 assert.equal(blocked.reason,"LEAF_NOT_AUTHORIZED");
 const sibling=planR0LeafPacket({tuple:pack(),...scope,authorized_keys:[...scope.authorized_keys,"candidate:other:sibling"],requested_leaf_keys:["candidate:other:sibling"]});
 assert.equal(sibling.reason,"LEAF_NOT_AUTHORIZED");
 const repeated=planR0LeafPacket({tuple:pack(),...scope,requested_leaf_keys:[sample.children[0],sample.children[0]]});
 assert.equal(repeated.reason,"INVALID_PACKET_REQUEST");
 for(const r of [blocked,sibling,repeated])assert.ok(!JSON.stringify(r).includes(sample.source_ref));
});
test("public rights, corrupted hash, packet budget and malformed leaves deny transport plans",()=>{
 const v=planR0LeafPacket({tuple:pack(),...scope,surface:"public"});
 assert.equal(v.reason,"SOURCE_PUBLIC_RIGHTS_HOLD");
 const bad=planR0LeafPacket({tuple:pack(),...scope,source_sha256:"b".repeat(64)});
 assert.equal(bad.reason,"SOURCE_BYTES_IDENTITY_MISMATCH");
 const tooSmall=planR0LeafPacket({tuple:pack(),...scope,max_packet_bytes:512});
 assert.equal(tooSmall.reason,"PACKET_BUDGET_EXCEEDED");
 for(const xs of [["../private"],["candidate:emassc:\\u202Efake"]]){
   const r=planR0LeafPacket({tuple:pack(),...scope,requested_leaf_keys:xs});
   assert.equal(r.reason,"INVALID_PACKET_REQUEST");
 }
});
