import test from "node:test";
import assert from "node:assert/strict";
import {SCHEMA,packR0Reference,unpackR0Reference,planR0ReferenceHydration,planR0LeafPacket,LEAF_PACKET_SCHEMA,planR0NestedFacets,NESTED_FACET_SCHEMA} from "./loadFractalReference.mjs";
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


const node=(key,children=[],more={})=>packR0Reference({...sample,candidate_key:"candidate:"+key,
 source_ref:"fixture:"+key,source_sha256:"a".repeat(64),children:children.map(k=>"candidate:"+k),...more});
const facet=(key,children=[],kind="assembly",binding=null,more={})=>({tuple:node(key,children,more),kind,binding});
const evm={standard:"evm-abi/1",chain_ref:"eip155:11155111",contract_address:"0x"+"1".repeat(40),
 interface_sha256:"a".repeat(64),runtime_code_sha256:"b".repeat(64),method_selector:"0x12345678",operation:"inspect"};
const graph=()=>[facet("root",["left","right"]),facet("left",["shared"],"simulation"),
 facet("right",["shared","contract"],"tool"),facet("shared",[],"geometry"),
 facet("contract",[],"smart_contract",evm)];
const nested=(facets=graph(),more={})=>{
 const ds=facets.map(f=>unpackR0Reference(f.tuple));
 return planR0NestedFacets({root_key:"candidate:root",facets,
  authorized_keys:ds.map(d=>d.candidate_key),authorized_source_refs:ds.map(d=>d.source_ref),
  expected_source_hashes:Object.fromEntries(ds.map(d=>[d.candidate_key,d.source_sha256])),...more});
};
test("nested human tree shares one machine identity, child before parent",()=>{
 const r=nested();assert.equal(r.schema,NESTED_FACET_SCHEMA);assert.equal(r.state,"NESTED_REFERENCE_PLAN_ONLY");
 assert.deepEqual(r.machine_bottom_up.map(n=>n.ref),["candidate:shared","candidate:left","candidate:contract","candidate:right","candidate:root"]);
 assert.equal(r.unique_facets,5);
 assert.deepEqual(r.human_top_down.children[1].children[0],{ref:"candidate:shared",occurrence:"SHARED_REFERENCE"});
 assert.equal(r.machine_bottom_up.filter(n=>n.ref==="candidate:shared").length,1);
 assert.deepEqual(nested(graph().reverse()),r);
});
test("machine ordering retains exact R0 tuples and contract binding across representation",()=>{
 const original=graph(),r=nested(original);
 const restored=r.machine_bottom_up.map(({tuple,kind,binding})=>({tuple,kind,binding}));
 assert.deepEqual(nested(restored),r);
 for(const f of original)assert.deepEqual(r.machine_bottom_up.find(n=>n.ref===unpackR0Reference(f.tuple).candidate_key).tuple,f.tuple);
 for(const k of ["native_admission","public_release","operator_executed","transaction_constructed","chain_transaction_submitted","semantic_equivalence_verified","scope_independently_verified"])assert.equal(r[k],false,k);
 assert.equal(r.payload_bytes_transferred,0);assert.equal(r.source_bytes_read,0);
});
test("root-only and H1 projections do not disclose source metadata or contract binding",()=>{
 const a=nested(graph(),{level:0}),b=nested(graph(),{level:1});
 assert.deepEqual(a.machine_bottom_up,[{ref:"candidate:root",kind:"assembly"}]);
 assert.ok(!JSON.stringify(a).includes("candidate:shared"));
 for(const r of [a,b]){const s=JSON.stringify(r);assert.ok(!s.includes("fixture:"));assert.ok(!s.includes(evm.contract_address));assert.ok(!s.includes("operator_ref"));}
 assert.equal(b.machine_bottom_up.length,5);
});
test("each leaf has its own digest and scope; errors do not reveal a private source",()=>{
 for(const [more,reason] of [
  [{authorized_keys:["candidate:root"]},"SOURCE_SCOPE_NOT_AUTHORIZED"],
  [{authorized_source_refs:["fixture:root"]},"SOURCE_SCOPE_NOT_AUTHORIZED"],
  [{expected_source_hashes:{"candidate:root":"a".repeat(64)}},"SOURCE_DIGEST_REQUIRED"],
  [{expected_source_hashes:Object.fromEntries(graph().map(f=>[f.tuple[1],"c".repeat(64)]))},"SOURCE_BYTES_IDENTITY_MISMATCH"]
 ]){const r=nested(graph(),more);assert.equal(r.reason,reason);assert.ok(!JSON.stringify(r).includes("fixture:"));assert.ok(!JSON.stringify(r).includes(evm.contract_address));}
});
test("duplicate identities, disconnected nodes, missing children and cycles fail closed",()=>{
 assert.equal(nested([...graph(),graph()[4]]).reason,"DUPLICATE_CANDIDATE_IDENTITY");
 assert.equal(nested([...graph(),facet("unrelated")]).reason,"UNREACHABLE_FACET");
 assert.equal(nested(graph().filter(f=>f.tuple[1]!=="candidate:shared")).reason,"CHILD_REFERENCE_MISSING");
 assert.equal(nested([facet("root",["a"]),facet("a",["root"])]).reason,"NESTED_CYCLE");
});
test("shared node cannot bypass depth check through a deeper second occurrence",()=>{
 const g=[facet("root",["leaf","a"]),facet("a",["b"]),facet("b",["leaf"]),facet("leaf")];
 assert.equal(nested(g,{max_depth:2}).reason,"NESTED_DEPTH_EXCEEDED");
 assert.equal(nested(g,{max_depth:3}).state,"NESTED_REFERENCE_PLAN_ONLY");
 assert.equal(nested(graph(),{max_nodes:4}).reason,"INVALID_NESTED_SCOPE");
 assert.equal(nested(graph(),{max_metadata_bytes:512}).reason,"NESTED_METADATA_BUDGET_EXCEEDED");
});
test("contract references bind source ABI digest and keep chain effects held",()=>{
 for(const operation of ["inspect","simulate","submit"]){
  const r=nested([facet("root",[],"smart_contract",{...evm,operation})]);
  assert.equal(r.state,"NESTED_REFERENCE_PLAN_ONLY");
  const x=r.machine_bottom_up[0].contract_review;
  assert.equal(x.state,operation==="submit"?"HOLD_SIGNED_LEASE_AND_TRANSACTION_CONSENT":operation==="simulate"?"HOLD_QUALIFIED_SIMULATION_PROVIDER":"REFERENCE_INSPECTION_ONLY");
  assert.equal(x.transaction_constructed,false);assert.equal(x.chain_identity_verified,false);
  assert.equal(x.proxy_resolution_verified,false);assert.equal(x.runtime_code_verified,false);
 }
 for(const binding of [{...evm,interface_sha256:"c".repeat(64)},{...evm,chain_ref:"eip155:0"},
  {...evm,contract_address:"0x"+"Z".repeat(40)},{...evm,method_selector:"0x123"},
  {...evm,contract_address:null},{...evm,rpc_url:"https://example.invalid"},
  {...evm,operation:"execute"}]){
  assert.equal(nested([facet("root",[],"smart_contract",binding)]).reason,"SMART_CONTRACT_BINDING_INVALID");
 }
 assert.equal(nested([facet("root",[],"geometry",evm)]).reason,"UNEXPECTED_ADAPTER_BINDING");
});
test("public nested metadata requires private review; private sources never appear on public root",()=>{
 assert.equal(nested(graph(),{surface:"public"}).reason,"PUBLIC_NESTED_METADATA_HOLD");
 assert.equal(nested(graph(),{surface:"public",level:0}).reason,"SOURCE_PUBLIC_RIGHTS_HOLD");
 const g=[facet("root",[], "smart_contract",evm,{rights:"PUBLIC_SAFE"})];
 const r=nested(g,{surface:"public",level:0});assert.equal(r.state,"NESTED_REFERENCE_PLAN_ONLY");
 assert.equal(r.public_release,false);assert.ok(!JSON.stringify(r).includes(evm.contract_address));
});
test("different candidate occurrences with same source digest are not semantically merged",()=>{
 const r=nested([facet("root",["a","b"]),facet("a"),facet("b")]);
 assert.equal(r.unique_facets,3);assert.equal(r.semantic_equivalence_verified,false);
 assert.equal(planR0NestedFacets(null).reason,"INVALID_NESTED_REQUEST");
 assert.equal(nested(graph(),{rpc_url:"secret"}).reason,"UNEXPECTED_NESTED_FIELD");
 assert.throws(()=>packR0Reference({...sample,owner_domain:"__proto__",file_space:undefined,parent_file_space:undefined}),/FAMILY_SCOPE_CONFLICT/);
});
