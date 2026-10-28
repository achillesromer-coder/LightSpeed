import {test} from 'node:test';
import assert from 'node:assert/strict';
import {projectUniSpaceLoadLens as project} from './cgxLoadLibraryLensPlan.mjs';
const SHA='75d913822e4da42e64ab8a2274c84d6f853340b3';
const REG='c2e03b1137ba844209e6c80e94c9fc7532f0db11';
const make=()=>({
 load_contract:{schema:'LOAD-ALEXANDRIA-ACTIVATION/0.1',
  status:'SOURCE_REVIEW_NOT_ADMITTED',alias:'LOAD.cgx',
  parent_filespace:'Cognigrex.cgx',canonical_object_id:null,
  accepted_parent_object_id:null,canonical_mutation:false,
  network_fetch:'DENY_UNTIL_HOST_AUTHORIZED'},
 requested_object_id:'WT-001',destination_filespace:'Romer.cgx',
 context_plan:{schema:'UNISPACE-CGX-HOST-CONTEXT-GATE/0.1',
  state:'PLAN_ONLY_NOT_HYDRATED',object_id:'WT-001',filespace:'Romer.cgx',
  source_lineage_git_blob_sha:SHA,source_registry_git_blob_sha:REG,
  native_admitted:false,canonical_mutation:false,execution_performed:false,
  private_hydration_authorized:false,public_publish_authorized:false,
  host_context_readback_authenticated:false,source_registry_independently_verified:false},
 client_permissions:{mode:'review_only',revoked:false,
  allowed_object_ids:['WT-001'],allowed_filespaces:['Romer.cgx']},
 source_status:{collision:'no_conflict_reported',rights:'cleared_for_review',
  evidence_class:'scientific'},
 requested_layer:'R0',requested_hydration:'H0',offline:false
});
const reject=(p,code)=>assert.equal(project(p).hold_code,code);
test('H0 only plans one exact object, no hydration or authority',()=>{
 const x=project(make());assert.equal(x.state,'PLAN_ONLY_NOT_HYDRATED');
 assert.equal(x.object_id,'WT-001');assert.equal(x.filespace,'Romer.cgx');
 assert.deepEqual(x.display_sections,['identity_placeholder']);
 for(const k of ['native_admitted','hydrated','execution_performed','canonical_mutation',
  'private_data_included','public_publish_authorized','host_context_readback_authenticated',
  'source_rights_independently_verified','client_scope_independently_authenticated'])
  assert.equal(x[k],false,k);
});
test('H1-H3 are distinct placeholders not materialised evidence',()=>{
 for(const [h,n] of [['H1',2],['H2',3],['H3',4]]){
  const p=make();p.requested_hydration=h;const x=project(p);
  assert.equal(x.planned_hydration,h);assert.equal(x.display_sections.length,n);
  assert.equal(x.source_provenance_included,false);assert.equal(x.hydrated,false);
 }
});
test('offline H3 degrades to H0 and zero transfer',()=>{
 const p=make();p.offline=true;p.requested_hydration='H3';
 const x=project(p);assert.equal(x.planned_hydration,'H0');
 assert.equal(x.max_transfer_bytes,0);assert.equal(x.offline_degraded,true);
});
test('H4 execution always denied',()=>{const p=make();p.requested_hydration='H4';
 reject(p,'H4_REQUIRES_INDEPENDENT_HOST_LEASE_AND_DBR');});
test('LOAD cannot become new parent or canonical Object_ID',()=>{
 const p=make();p.load_contract.canonical_object_id='LOAD-001';
 reject(p,'LOAD_ALIAS_NOT_SOURCE_REVIEW');
 const q=make();q.load_contract.parent_filespace='LOAD.cgx';
 reject(q,'LOAD_ALIAS_NOT_SOURCE_REVIEW');
});
test('LOAD activation must remain source-review and no fetch',()=>{
 const p=make();p.load_contract.network_fetch='ALLOW';
 reject(p,'LOAD_ALIAS_NOT_SOURCE_REVIEW');
});
test('cross-family child mismatch rejected',()=>{
 const p=make();p.destination_filespace='Eco.cgx';
 reject(p,'EXACT_OBJECT_CHILD_CONTEXT_UNVERIFIED');
});
test('domain identity is not instance identity',()=>{
 const p=make();p.requested_object_id='cgx:domain:romer';
 reject(p,'EXACT_OBJECT_CHILD_CONTEXT_UNVERIFIED');
});
test('missing or mismatched source registry SHA rejected',()=>{
 const p=make();p.context_plan.source_registry_git_blob_sha='not-a-sha';
 reject(p,'EXACT_OBJECT_CHILD_CONTEXT_UNVERIFIED');
});
test('client revocation, empty or extra object scope denied',()=>{
 const p=make();p.client_permissions.revoked=true;reject(p,'CLIENT_SCOPE_DENIED');
 const q=make();q.client_permissions.allowed_object_ids.push('OTHER');
 reject(q,'CLIENT_SCOPE_DENIED');
});
test('rights unresolved and collisions hold',()=>{
 const p=make();p.source_status.rights='unknown';reject(p,'SOURCE_RIGHTS_HOLD');
 const q=make();q.source_status.collision='ambiguous';
 reject(q,'IDENTITY_COLLISION_OR_UNKNOWN');
});
test('unknown evidence class blocks H3 capability plan',()=>{
 const p=make();p.source_status.evidence_class='unknown';
 p.requested_hydration='H3';reject(p,'CAPABILITY_PROOF_CLASS_UNKNOWN');
});
test('R1-R3 are not granted by H-level labels',()=>{
 const p=make();p.requested_layer='R3';reject(p,'R1_R3_REQUIRE_NATIVE_RECEIPTS');
});
test('no private paths, tokens or source bytes in inputs or output',()=>{
 for(const k of ['token','source_locator','source_bytes','public_path','lease']){
  const p=make();p[k]='private-secret';reject(p,'INLINE_SECRET_OR_PRIVATE_ROUTE');
 }
 const p=make();p.source_status.private_path='private-secret';
 reject(p,'INLINE_SECRET_OR_PRIVATE_ROUTE');
 assert.equal(JSON.stringify(project(make())).includes('private-secret'),false);
});
test('transfer budget capped to 1 MiB, accessible outputs are descriptors only',()=>{
 const p=make();p.max_bytes=9000000;const x=project(p);
 assert.equal(x.max_transfer_bytes,1048576);
 assert.deepEqual(x.output_surfaces,['browser','phone','desktop']);
});
test('malformed request and non-boolean offline fail closed',()=>{
 reject(null,'INVALID_REQUEST');
 const p=make();p.offline='false';reject(p,'OFFLINE_MODE_REQUIRED');
});
