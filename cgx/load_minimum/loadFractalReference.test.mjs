import test from "node:test";
import assert from "node:assert/strict";
import {SCHEMA,packR0Reference,unpackR0Reference,planR0ReferenceHydration} from "./loadFractalReference.mjs";
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
