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


import {CONTRACT_SCHEMA,CONFIGURATIONS,packContract,unpackContract,projectContract,prepareContractSignature,verifyContractSignature} from "./contractShorthand.mjs";
const contractFixture=(extra={})=>({
 contract_ref:"candidate:root",revision:1,previous_payload_sha256:null,source_ref:"fixture:root",source_sha256:"a".repeat(64),
 residual_ref:sample.residual_ref,configuration:"exchange",
 parties:[["buyer","identity:buyer","customer"],["seller","identity:seller","supplier"]],
 variables:[["price","quantity",["12.50".replace(/0$/,""),"AUD"]],["ready","bool",true],["count","integer","2"],["due","utc","2026-12-01T00:00:00.000Z"]],
 commitments:[["pay","oblige","buyer","seller","action:pay",["price","ready"],[["ready","eq",true]],["receipt:payment"],["deliver"]],
 ["deliver","oblige","seller","buyer","action:deliver",["count"],[["count","ge","1"]],["receipt:delivery"],[]]],
 signature_policy:["cgx-ed25519-bytes/1",["buyer","seller"],2],
 valid_from:"2026-11-27T00:00:00.000Z",valid_until:"2026-12-02T00:00:00.000Z",native_adapter:null,...extra});
test("commitment shorthand retains exact ordered typed constituents and residual",()=>{
 const d=contractFixture(),t=packContract(d);
 assert.equal(t[0],CONTRACT_SCHEMA);assert.deepEqual(unpackContract(t),d);assert.deepEqual(packContract(unpackContract(t)),t);
 const p=projectContract(t);assert.deepEqual(p.machine_bottom_up.commitment_order,["deliver","pay"]);
 const paths=p.human_top_down.children.flatMap(g=>g.children.map(c=>c.path.join("")));
 assert.equal(new Set(paths).size,paths.length);assert.ok(paths.every(s=>/^[012]{7}$/.test(s)));
 assert.deepEqual(p.machine_bottom_up.tuple,t);assert.equal(p.physical_geometry_verified,false);
});
test("same primitives compose multiple configurations without silently deleting clauses",()=>{
 for(const configuration of Object.keys(CONFIGURATIONS)){
  const d=contractFixture({configuration});assert.deepEqual(unpackContract(packContract(d)),d);
 }
 assert.throws(()=>packContract(contractFixture({configuration:"constructor"})),/UNKNOWN_CONFIGURATION/);
});
test("typed values reject rounding, ambiguous timestamps and malformed quantities",()=>{
 for(const variables of [[["price","decimal",12.5]],[["price","decimal","12.50"]],[["price","integer","02"]],[["due","utc","2026-02-30T00:00:00.000Z"]],[["price","quantity",["1",""]]]]){
  assert.throws(()=>packContract(contractFixture({variables})),/VARIABLES_INVALID/);
 }
});
test("amendments must link previous exact payload; omissions are not defaults",()=>{
 assert.throws(()=>packContract(contractFixture({revision:2})),/AMENDMENT_LINK_REQUIRED/);
 const d=contractFixture({revision:2,previous_payload_sha256:"b".repeat(64)});assert.deepEqual(unpackContract(packContract(d)),d);
 const missing=contractFixture();delete missing.residual_ref;assert.throws(()=>packContract(missing),/CONTRACT_FIELD_SET/);
});
test("invalid parties, scope, dependency cycles and typed conditions fail closed",()=>{
 const d=contractFixture();d.commitments[1][8]=["pay"];assert.throws(()=>packContract(d),/COMMITMENT_CYCLE/);
 const e=contractFixture();e.commitments[0][2]="stranger";assert.throws(()=>packContract(e),/COMMITMENT_SCOPE/);
 const f=contractFixture();f.commitments[0][6]=[["ready","gt",true]];assert.throws(()=>packContract(f),/CONDITION_INVALID/);
 const g=contractFixture();g.parties[1][1]=g.parties[0][1];assert.throws(()=>packContract(g),/SIGNATURE_POLICY_INVALID/);
});
test("signature intent binds exact revision, party, key, challenge and context but never signs",()=>{
 const t=packContract(contractFixture()),r={party_id:"buyer",key_ref:"key:buyer",challenge:"c".repeat(64),context_ref:"review:agreement"};
 const a=prepareContractSignature(t,r);assert.equal(a.state,"UNSIGNED_PREIMAGE_ONLY");assert.equal(a.signature_verified,false);assert.equal(a.threshold_satisfied,false);
 assert.equal(a.preimage_utf8,JSON.stringify(a.intent_binding));
 for(const change of [{party_id:"seller"},{key_ref:"key:replacement"},{challenge:"d".repeat(64)},{context_ref:"review:other"}])assert.notEqual(prepareContractSignature(t,{...r,...change}).preimage_utf8,a.preimage_utf8);
 assert.notEqual(prepareContractSignature(packContract(contractFixture({revision:2,previous_payload_sha256:"b".repeat(64)})),r).preimage_utf8,a.preimage_utf8);
 assert.throws(()=>prepareContractSignature(t,{...r,party_id:"stranger"}),/SIGN_REQUEST_INVALID/);
});
test("external signatures retain native payload boundary and do not impersonate EIP712 or PAdES",()=>{
 for(const profile of ["external-eip712","external-pades","external-cades","external-jades","external-provider"]){
  const t=packContract(contractFixture({signature_policy:[profile,["buyer","seller"],2]}));
  const r=prepareContractSignature(t,{party_id:"buyer",key_ref:"key:buyer",challenge:"a".repeat(64),context_ref:"review:agreement"});
  assert.equal(r.state,"HOLD_NATIVE_SIGNING_PAYLOAD_ADAPTER");assert.equal(r.preimage_utf8,null);assert.equal(r.execution_authorized,false);
 }
});
test("nested contract facet binds R0 identity, original source and residual, with selective projection",()=>{
 const t=packContract(contractFixture()),g=[facet("root",[],"contract",{standard:"cgx-commitments/1",payload:t})];
 const r=nested(g);assert.equal(r.state,"NESTED_REFERENCE_PLAN_ONLY");assert.deepEqual(r.machine_bottom_up[0].binding.payload,t);
 assert.equal(r.machine_bottom_up[0].contract_review.state,"UNSIGNED_COMMITMENT_REFERENCE_ONLY");
 for(const level of [0,1])assert.ok(!JSON.stringify(nested(g,{level})).includes("identity:buyer"));
 for(const change of [{contract_ref:"candidate:other"},{source_ref:"fixture:wrong"},{source_sha256:"b".repeat(64)},{residual_ref:null}]){
  assert.equal(nested([facet("root",[],"contract",{standard:"cgx-commitments/1",payload:packContract(contractFixture(change))})]).reason,"COMMITMENT_BINDING_INVALID");
 }
});

test("sparse and extended arrays cannot become different serialised contract fields",()=>{
 const d=contractFixture();d.variables.length++;assert.throws(()=>packContract(d),/VARIABLES_INVALID/);
 const e=contractFixture();e.parties.note="extra";assert.throws(()=>packContract(e),/PARTIES_INVALID/);
});
test("ephemeral Ed25519 verifies exact bytes but never establishes trust or authority",async()=>{
 const {generateKeyPairSync,sign}=await import("node:crypto");
 const {publicKey,privateKey}=generateKeyPairSync("ed25519");
 const raw=publicKey.export({format:"der",type:"spki"}).subarray(-32).toString("hex");
 const t=packContract(contractFixture()),intent={party_id:"buyer",key_ref:"key:buyer",challenge:"a".repeat(64),context_ref:"review:contract"};
 const preimage=prepareContractSignature(t,intent).preimage_utf8;
 const sig=sign(null,Buffer.from(preimage,"utf8"),privateKey).toString("hex");
 const r=await verifyContractSignature(t,intent,raw,sig);
 assert.equal(r.state,"MATHEMATICAL_SIGNATURE_VALID_ONLY");assert.equal(r.mathematical_signature_valid,true);
 for(const k of ["signer_identity_verified","key_binding_verified","challenge_freshness_verified","threshold_satisfied","consent_verified","legal_validity_verified","execution_authorized","native_admission"])assert.equal(r[k],false,k);
 for(const changed of [{party_id:"seller"},{challenge:"b".repeat(64)},{context_ref:"review:other"}]){
  assert.equal((await verifyContractSignature(t,{...intent,...changed},raw,sig)).mathematical_signature_valid,false);
 }
 const changed=contractFixture();changed.variables[0][2][0]="13";
 assert.equal((await verifyContractSignature(packContract(changed),intent,raw,sig)).mathematical_signature_valid,false);
 const other=generateKeyPairSync("ed25519").publicKey.export({format:"der",type:"spki"}).subarray(-32).toString("hex");
 assert.equal((await verifyContractSignature(t,intent,other,sig)).mathematical_signature_valid,false);
 assert.equal((await verifyContractSignature(t,intent,raw,"bad")).state,"INVALID_SIGNATURE_ENCODING");
 const external=packContract(contractFixture({signature_policy:["external-eip712",["buyer","seller"],2]}));
 assert.equal((await verifyContractSignature(external,intent,raw,sig)).state,"HOLD_NATIVE_VERIFICATION_ADAPTER");
});


import {indexContractComposition,contractPayloadDigest,verifyContractLineage,prepareEip712Commitment,bindNativeSignaturePayload} from "./contractShorthand.mjs";
test("composition mask exhausts 15 nonempty class sets without manufacturing legal equivalence",()=>{
 const classes=["oblige","permit","prohibit","declare"],seen=new Set();
 for(let mask=1;mask<16;mask++){
  const d=contractFixture({configuration:"custom"});
  d.commitments=classes.filter((_,i)=>mask&(1<<i)).map((kind,i)=>["clause"+i,kind,"buyer","seller","action:fixture",[],[],[],[]]);
  const p=indexContractComposition(packContract(d));
  assert.equal(p.mask,mask);assert.equal(parseInt(p.trits.join(""),3),mask);seen.add(p.trits.join(""));
  assert.equal(p.legal_equivalence_verified,false);assert.equal(p.execution_authorized,false);
 }
 assert.equal(seen.size,15);
 const a=contractFixture(),b=contractFixture();b.variables[0][2][0]="99";
 assert.equal(indexContractComposition(packContract(a)).mask,indexContractComposition(packContract(b)).mask);
 assert.notDeepEqual(packContract(a),packContract(b));
});
test("exact revision chain rejects changed, skipped, foreign or unbound amendments",async()=>{
 const a=packContract(contractFixture()),h=await contractPayloadDigest(a);
 const b=packContract(contractFixture({revision:2,previous_payload_sha256:h}));
 const c=packContract(contractFixture({revision:3,previous_payload_sha256:await contractPayloadDigest(b)}));
 const r=await verifyContractLineage([a,b,c]);
 assert.equal(r.state,"SUPPLIED_LINEAGE_HASH_LINKS_MATCH_ONLY");assert.equal(r.links.length,3);
 assert.equal(r.amendment_authority_verified,false);assert.equal(r.complete_global_history_verified,false);
 const changed=contractFixture();changed.variables[0][2][0]="13";
 const wrong=packContract(contractFixture({revision:2,previous_payload_sha256:h,contract_ref:"candidate:other"}));
 for(const chain of [[packContract(changed),b],[a,c],[b],[a,wrong],[a,b,b]])assert.equal((await verifyContractLineage(chain)).state,"LINEAGE_LINK_MISMATCH");
 assert.equal((await verifyContractLineage([])).state,"LINEAGE_INPUT_INVALID");
});
const nativeIntent={party_id:"buyer",key_ref:"key:buyer",challenge:"c".repeat(64),context_ref:"review:contract"};
const nativeFixture=(profile)=>packContract(contractFixture({signature_policy:[profile,["buyer","seller"],2],native_adapter:[profile==="external-eip712"?"evm-abi":"document-signature","adapter:review","1","f".repeat(64)]}));
test("EIP712 typed data explicitly binds chain, contract, revision, digest, party and challenge",async()=>{
 const t=nativeFixture("external-eip712"),domain={chain_id:"11155111",verifying_contract:"0x"+"1".repeat(40)};
 const a=await prepareEip712Commitment(t,nativeIntent,domain);
 assert.equal(a.typed_data.primaryType,"CGXCommitment");assert.equal(a.typed_data.domain.chainId,domain.chain_id);
 assert.equal(a.typed_data.message.payloadSha256,"0x"+await contractPayloadDigest(t));
 assert.equal(a.typed_data.message.challenge,"0x"+nativeIntent.challenge);
 assert.equal(a.execution_authorized,false);assert.equal(a.replay_protection_verified,false);assert.equal(a.wallet_invoked,false);
 const b=await prepareEip712Commitment(t,{...nativeIntent,context_ref:"review:other"},domain);
 assert.notEqual(a.typed_data.message.intentSha256,b.typed_data.message.intentSha256);
 const c=await prepareEip712Commitment(t,nativeIntent,{...domain,chain_id:"1"});assert.notDeepEqual(a.typed_data.domain,c.typed_data.domain);
 for(const change of [{chain_id:"0"},{chain_id:(1n<<256n).toString()},{chain_id:1},{verifying_contract:"0x"+"0".repeat(40)}]){
  await assert.rejects(prepareEip712Commitment(t,nativeIntent,{...domain,...change}),/EIP712_DOMAIN_INVALID/);
 }
 await assert.rejects(prepareEip712Commitment(nativeFixture("external-jws"),nativeIntent,domain),/SIGNATURE_PROFILE_MISMATCH/);
});
test("native JWS, COSE and document envelopes bind exact supplied bytes, not native verification",async()=>{
 const {createHash}=await import("node:crypto"),hash=x=>createHash("sha256").update(x).digest("hex");
 const bytes=Uint8Array.from([0,255,13,10,65]);
 for(const profile of ["external-jws","external-cose","external-pades","external-cades","external-jades","external-eip712"]){
  const t=nativeFixture(profile),intent=prepareContractSignature(t,nativeIntent);
  const m={profile,payload_ref:"fixture:native",payload_sha256:hash(bytes),
   intent_sha256:hash(JSON.stringify(intent.intent_binding)),domain_ref:"fixture:domain",adapter_sha256:"f".repeat(64)};
  const r=await bindNativeSignaturePayload(t,nativeIntent,bytes,m);
  assert.equal(r.payload_hash_verified,true);assert.equal(r.native_semantics_verified,false);assert.equal(r.signature_verified,false);assert.equal(r.execution_authorized,false);
  await assert.rejects(bindNativeSignaturePayload(t,nativeIntent,Uint8Array.from([1,2]),m),/NATIVE_BINDING_DIGEST_MISMATCH/);
  await assert.rejects(bindNativeSignaturePayload(t,{...nativeIntent,challenge:"d".repeat(64)},bytes,m),/NATIVE_BINDING_DIGEST_MISMATCH/);
  await assert.rejects(bindNativeSignaturePayload(t,nativeIntent,bytes,{...m,adapter_sha256:"a".repeat(64)}),/NATIVE_BINDING_INVALID/);
  await assert.rejects(bindNativeSignaturePayload(t,nativeIntent,bytes,{...m,private_key:"never"}),/NATIVE_BINDING_INVALID/);
 }
});


import {commitmentReviewEventDigest,reviewCommitmentJournal} from "./contractShorthand.mjs";
const reviewTime="2026-11-28T00:00:00.000Z";
async function reviewEvent(t,events,change={}){
 const d=unpackContract(t);
 return {contract_ref:d.contract_ref,revision:d.revision,payload_sha256:await contractPayloadDigest(t),
 sequence:events.length+1,previous_event_sha256:events.length?await commitmentReviewEventDigest(t,events.at(-1)):null,
 commitment_id:"deliver",kind:"report",reported_at:reviewTime,reporter_id:"seller",
 evidence_refs:["receipt:delivery"],observations:[["count","2"]],...change};
}
test("review journal separates reported criteria from legal fulfilment and replays dependency order",async()=>{
 const t=packContract(contractFixture()),events=[];
 events.push(await reviewEvent(t,events));
 events.push(await reviewEvent(t,events,{commitment_id:"pay",reporter_id:"buyer",evidence_refs:["receipt:payment"],observations:[["ready",true]]}));
 const r=await reviewCommitmentJournal(t,events,reviewTime);
 assert.equal(r.state,"SUPPLIED_REVIEW_JOURNAL_REPLAY_ONLY");
 assert.deepEqual(r.machine_bottom_up.map(x=>x.commitment_ref),["deliver","pay"]);
 assert.deepEqual(r.human_top_down.map(x=>x.commitment_ref),["pay","deliver"]);
 assert.ok(r.machine_bottom_up.every(x=>x.status==="REPORTED_CRITERIA_MATCH"));
 for(const k of ["legal_fulfilment_verified","reported_facts_independently_verified","reporter_identity_verified","signature_verified","execution_authorized","effects_performed"])assert.equal(r[k],false);
 assert.equal(r.head_event_sha256,await commitmentReviewEventDigest(t,events[1]));
});
test("dispute invalidates downstream readiness; reopen requires new report and cannot bypass dispute",async()=>{
 const t=packContract(contractFixture()),events=[];
 events.push(await reviewEvent(t,events));
 events.push(await reviewEvent(t,events,{commitment_id:"pay",reporter_id:"buyer",evidence_refs:["receipt:payment"],observations:[["ready",true]]}));
 events.push(await reviewEvent(t,events,{kind:"dispute",evidence_refs:["receipt:dispute"],observations:[]}));
 let r=await reviewCommitmentJournal(t,events,reviewTime);
 assert.deepEqual(r.machine_bottom_up.map(x=>x.status),["DISPUTED","REPORTED_DEPENDENCY_HOLD"]);
 assert.equal((await reviewCommitmentJournal(t,[...events,await reviewEvent(t,events)],reviewTime)).state,"REVIEW_TRANSITION_INVALID");
 events.push(await reviewEvent(t,events,{kind:"reopen",evidence_refs:["receipt:review"],observations:[]}));
 r=await reviewCommitmentJournal(t,events,reviewTime);
 assert.deepEqual(r.machine_bottom_up.map(x=>x.status),["REOPENED","REPORTED_DEPENDENCY_HOLD"]);
 events.push(await reviewEvent(t,events));r=await reviewCommitmentJournal(t,events,reviewTime);
 assert.deepEqual(r.machine_bottom_up.map(x=>x.status),["REPORTED_CRITERIA_MATCH","REPORTED_CRITERIA_MATCH"]);
});
test("journal does not default missing observations to contract variables or silently infer evidence",async()=>{
 const t=packContract(contractFixture());
 for(const [change,expected] of [[{observations:[]},"REPORTED_CONDITION_UNKNOWN"],[{observations:[["count","0"]]},"REPORTED_CONDITION_MISMATCH"],[{evidence_refs:[]},"REPORTED_EVIDENCE_MISSING"]]){
  const r=await reviewCommitmentJournal(t,[await reviewEvent(t,[],change)],reviewTime);
  assert.equal(r.machine_bottom_up[0].status,expected);
 }
 const r=await reviewCommitmentJournal(t,[],"2026-12-03T00:00:00.000Z");
 assert.equal(r.declared_interval,"AFTER_INTERVAL");assert.ok(r.machine_bottom_up.every(x=>x.status==="NO_REPORT"));
});
test("condition ordering is exact for large decimal and integer values",async()=>{
 const d=contractFixture();d.variables.push(["precise","decimal","9007199254740993.0000000001"]);
 d.commitments[1][5].push("precise");d.commitments[1][6].push(["precise","gt","9007199254740993"]);
 const t=packContract(d);
 const r=await reviewCommitmentJournal(t,[await reviewEvent(t,[],{observations:[["count","2"],["precise","9007199254740993.0000000001"]]})],reviewTime);
 assert.equal(r.machine_bottom_up[0].status,"REPORTED_CRITERIA_MATCH");
 const s=await reviewCommitmentJournal(t,[await reviewEvent(t,[],{observations:[["count","2"],["precise","9007199254740992.9999999999"]]})],reviewTime);
 assert.equal(s.machine_bottom_up[0].status,"REPORTED_CONDITION_MISMATCH");
});
test("journal rejects tampered links, stale revision, future reports and invalid parties",async()=>{
 const t=packContract(contractFixture()),a=await reviewEvent(t,[]),b=await reviewEvent(t,[a],{kind:"dispute",evidence_refs:["receipt:dispute"],observations:[]});
 assert.equal((await reviewCommitmentJournal(t,[{...a,evidence_refs:["other"]},b],reviewTime)).state,"REVIEW_EVENT_CHAIN_MISMATCH");
 assert.equal((await reviewCommitmentJournal(t,[b],reviewTime)).state,"REVIEW_EVENT_CHAIN_MISMATCH");
 assert.equal((await reviewCommitmentJournal(t,[{...a,reported_at:"2026-11-29T00:00:00.000Z"}],reviewTime)).state,"REVIEW_TIME_ORDER");
 assert.equal((await reviewCommitmentJournal(t,[{...a,reporter_id:"unknown"}],reviewTime)).state,"REVIEW_EVENT_SCOPE");
 assert.equal((await reviewCommitmentJournal(t,[{...a,observations:[["ready",true]]}],reviewTime)).state,"REVIEW_OBSERVATIONS_INVALID");
 const next=packContract(contractFixture({revision:2,previous_payload_sha256:await contractPayloadDigest(t)}));
 assert.equal((await reviewCommitmentJournal(next,[a],reviewTime)).state,"REVIEW_REVISION_MISMATCH");
 assert.equal((await reviewCommitmentJournal(t,[{...a,signature_verified:true}],reviewTime)).state,"REVIEW_EVENT_FIELDS");
});


test("review replay is stable if original caller objects change during hashing",async()=>{
 const t=packContract(contractFixture()),e=await reviewEvent(t,[]),events=[e];
 const original=await reviewCommitmentJournal(t,events,reviewTime);
 const pending=reviewCommitmentJournal(t,events,reviewTime);
 t[1]="candidate:changed";e.observations[0][1]="0";events.length=0;
 assert.deepEqual(await pending,original);
});
