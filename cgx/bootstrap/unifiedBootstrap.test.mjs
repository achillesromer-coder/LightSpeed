import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {planCGXSetup,planOngoingSetup} from './unifiedBootstrap.mjs';
const family='Romer.cgx';
const proof={hostReachable:true,acceptedParent:true,acceptedFamily:true,exactObjectId:true,ownerAcl:true,
 dbrReadback:true,signedLease:true,sourceRightsVerified:true,loadAliasVerified:true,
 privateAssetBoundaryVerified:true,familyUiBindingVerified:true};
test('all five existing Grex family paths have one bootstrap with no install by default',()=>{
 for(const name of ['Cognigrex.cgx','Romer.cgx','Eco.cgx','EMASSC.cgx','LS.cgx']){
  const p=planCGXSetup({family:name});
  assert.equal(p.family,name);assert.equal(p.steps.length,11);assert.equal(p.runtime_installed,false);
  assert.equal(p.source_ingested,false);assert.equal(p.canonical_accepted,false);
 }
});
test('UniSpace product cannot masquerade as Grex child',()=>{
 assert.equal(planCGXSetup({family:'UniSpace'}).reason,'UNKNOWN_FILESPACE');
});
test('offline-first minimal LOAD is reference-only until accepted ID',()=>{
 const p=planCGXSetup({family});assert.equal(p.offline_minimum,true);assert.equal(p.library.install,false);
 assert.ok(p.blockers.includes('LOAD_EXISTING_IDENTITY_NOT_VERIFIED'));
});
test('without host RootAuthority and DBR no LS GO',()=>{
 const p=planCGXSetup({family,lsGORequested:true});
 assert.equal(p.ls_go.enabled,false);assert.equal(p.ls_go.ready_for_authenticated_host_preflight,false);
 assert.ok(p.blockers.includes('PARENT_ROOT_UNVERIFIED'));
});
test('even observed proofs only qualify for authenticated host preflight, not real install',()=>{
 const p=planCGXSetup({family,observed:proof,lsGORequested:true});
 assert.equal(p.ls_go.ready_for_authenticated_host_preflight,true);
 assert.equal(p.ls_go.enabled,false);assert.equal(p.ls_go.actual_toggle_write,false);
 assert.equal(p.canonical_accepted,false);assert.equal(p.published,false);
});
test('legacy transcription of GOT cannot introduce a capability or startup blocker',()=>{
 const p=planCGXSetup({family,observed:proof,gotRequested:true});
 assert.equal(p.state,'REVIEW_ONLY');
 assert.equal(Object.hasOwn(p,'got'),false);
 assert.ok(p.blockers.every(s=>!s.includes('GOT')));
});
test('oversized source segment requires bounded intake',()=>{
 const p=planCGXSetup({family,sourceBytesPerChunk:64*1024*1024});
 assert.equal(p.reason,'SOURCE_SEGMENT_TOO_LARGE');
});
test('parent, role and lease are independently checked',()=>{
 const p=planCGXSetup({family,observed:{...proof,signedLease:false}});
 assert.ok(p.blockers.includes('SIGNED_LEASE_UNVERIFIED'));
});
test('private LS GO static release gate is independent',()=>{
 const p=planCGXSetup({family,lsGORequested:true,observed:{...proof,privateAssetBoundaryVerified:false}});
 assert.ok(p.blockers.includes('ISSUE_158_PRIVATE_ASSETS_HOLD'));
});
test('two-node DataSpace is gated separately',()=>{
 const p=planCGXSetup({family,observed:{...proof,nodeExchangeRequested:true,twoNodeProof:false}});
 assert.ok(p.blockers.includes('ISSUE_161_TWO_NODE_HOLD'));
});
test('valid old setup receipt is rechecked not automatically applied',()=>{
 const p=planCGXSetup({family,mode:'resume',receipt:{receipt_id:'fixture',family,completed_steps:['runtime','identity']},observed:proof});
 assert.equal(p.steps.find(x=>x.id==='runtime').status,'RECHECK_PRIOR_RECEIPT');
 assert.equal(p.steps.find(x=>x.id==='identity').auto_run,false);
});
test('changed source invalidates prior receipt reuse',()=>{
 const p=planCGXSetup({family,mode:'resume',receipt:{receipt_id:'fixture',family,completed_steps:['identity']},observed:{...proof,sourceChanged:true}});
 assert.equal(p.steps.find(x=>x.id==='identity').status,'PREFLIGHT_REQUIRED');
});
test('receipt from another family is rejected',()=>{
 const p=planCGXSetup({family,receipt:{receipt_id:'fixture',family:'Eco.cgx'}});
 assert.equal(p.reason,'RECEIPT_SCOPE_MISMATCH');
});
test('no arbitrary execution or publication through setup planner',()=>{
 assert.equal(planCGXSetup({family,intent:'execute'}).state,'DENIED');
 assert.equal(planCGXSetup({family,intent:'publish'}).state,'DENIED');
});
test('cosmetic changes lead to incremental check',()=>{
 const p=planOngoingSetup({family,current:{},changes:['theme','layout']});
 assert.equal(p.mode,'INCREMENTAL_CHECK');assert.equal(p.run_wizard_from_scratch,false);
});
test('root/authority/network changes require renewed proof, not wizard rewrite',()=>{
 const p=planOngoingSetup({family,current:{},changes:['root','network']});
 assert.equal(p.mode,'REVERIFY_AUTHORITY');assert.equal(p.mutation,false);
});
test('source, ACL, DBR, host and tool ABI changes invalidate incremental authority reuse',()=>{
 for(const changed of ['source','source_hash','acl','dbr','config','capability','tool_abi','host']){
  const p=planOngoingSetup({family,current:{},previous:{},changes:[changed]});
  assert.equal(p.mode,'REVERIFY_AUTHORITY',changed);
  assert.equal(p.mutation,false,changed);
  assert.equal(p.source_copy,false,changed);
  assert.equal(p.install,false,changed);
 }
});
test('unknown and future authority-affecting change types fail closed',()=>{
 for(const changed of ['plugin_route','licence','version','abi','source_revision','revocation','peer_identity','new_field']){
  const p=planOngoingSetup({family,current:{},changes:[changed]});
  assert.equal(p.mode,'REVERIFY_AUTHORITY',changed);
  assert.equal(p.mutation,false,changed);
  assert.equal(p.install,false,changed);
 }
 const mixed=planOngoingSetup({family,current:{},changes:['theme','plugin_route']});
 assert.equal(mixed.mode,'REVERIFY_AUTHORITY');
 assert.equal(planOngoingSetup({family,current:{},changes:[]}).mode,'INCREMENTAL_CHECK');
});
test('no missing returned receipts from invalid mode',()=>{
 assert.equal(planCGXSetup({family,mode:'panic'}).reason,'UNKNOWN_SETUP_MODE');
});

test('premint founder gates remain held despite design approval and dry-run readiness',()=>{
 const spec=JSON.parse(readFileSync(new URL('./cgxPhaseAcceptance_v01.json',import.meta.url),'utf8'));
 assert.equal(spec.state,'SOURCE_ONLY_REVIEW_NOT_CANONICAL');
 const p=spec.premint_integration_design_v01;
 assert.equal(p.status,'APPROVED_DESIGN_ONLY__NO_NATIVE_OR_PUBLIC_AUTHORITY');
 assert.equal(p.canonical_parent,'cgx:root:cognigrex');
 assert.equal(p.sole_resolver,'LOAD.cgx');
 assert.equal(p.review_decision_semantics.approve,'QUALIFY_PROPOSED_VERSION_ONLY');
 for(const [gate,status] of Object.entries(p.authority_gate_status))assert.equal(status,'HOLD',gate);
 for(const key of ['R0_byte_reconstruction_and_hash_roundtrip',
   'reject_duplicate_idempotency_intent_and_uncertain_ledger_retry',
   'negative_no_signing_no_issuer_no_network_no_publication'])
   assert.ok(p.deterministic_preflight_required.includes(key),key);
 assert.equal(spec.source_review_exception.native_mint,false);
 assert.equal(spec.source_review_exception.decentralized_launch,false);
 assert.notEqual(spec.evidence_stages.R2_QUALIFIED,spec.evidence_stages.NATIVE_ADMITTED);
});

test('LS GO host preflight holds LOAD rights and source identity independently',()=>{
 for(const field of ['sourceRightsVerified','loadAliasVerified']){
  const p=planCGXSetup({family,lsGORequested:true,observed:{...proof,[field]:false}});
  assert.equal(p.ls_go.ready_for_authenticated_host_preflight,false,field);
  assert.equal(p.ls_go.enabled,false);
  assert.equal(p.canonical_accepted,false);
 }
});
test('LS GO host preflight holds independently requested second-node evidence',()=>{
 const p=planCGXSetup({family,lsGORequested:true,observed:{...proof,nodeExchangeRequested:true,twoNodeProof:false}});
 assert.equal(p.ls_go.ready_for_authenticated_host_preflight,false);
 assert.ok(p.blockers.includes('ISSUE_161_TWO_NODE_HOLD'));
});

test('setup flags reject nonboolean truthy and falsey coercion',()=>{
 for(const flag of ['lsGORequested','offlinePreferred']){
  for(const value of ['false','true',0,1,null,[],{}]){
   const p=planCGXSetup({family,observed:proof,[flag]:value});
   assert.equal(p.state,'DENIED',`${flag}:${String(value)}`);
   assert.equal(p.reason,'INVALID_BOOLEAN_SETUP_FLAG');
  }
 }
 assert.equal(planCGXSetup({family,lsGORequested:false,offlinePreferred:true}).state,'REVIEW_ONLY');
});

test('resume receipt rejects unknown, duplicate and malformed completed steps',()=>{
 for(const completed_steps of [['identity','identity'],['identity','unapproved_dispatch'],['../identity'],[3], 'identity', null]){
  const p=planCGXSetup({family,mode:'resume',receipt:{receipt_id:'fixture',family,completed_steps}});
  assert.equal(p.state,'DENIED');
  assert.equal(p.reason,'INVALID_RECEIPT_STEPS');
 }
});

test('undeclared authority changes cannot be hidden by cosmetic-only change lists',()=>{
 const previous={theme:'dark',source_hash:'old',rights:{acl:'owner_only'},lease:{issuer:'owner'},dbr:'r1'};
 for(const changed of [
  {...previous,theme:'light',source_hash:'new'},
  {...previous,rights:{acl:'public'}},
  {...previous,lease:{issuer:'self'}},
  {...previous,dbr:'r2'},
  {...previous,future_capability:{runtime:'unreviewed'}}
 ]){
  const p=planOngoingSetup({family,current:changed,previous,changes:['theme']});
  assert.equal(p.mode,'REVERIFY_AUTHORITY');assert.equal(p.observed_authority_drift,true);
  assert.equal(p.mutation,false);assert.equal(p.install,false);
 }
});
test('state comparison preserves cosmetic-only and object key-order independence',()=>{
 const previous={root:{id:'cgx:root',revision:1},rights:{acl:'owner_only'},theme:'dark'};
 const current={rights:{acl:'owner_only'},root:{revision:1,id:'cgx:root'},theme:'light',layout:'graph'};
 const p=planOngoingSetup({family,current,previous,changes:['theme','layout']});
 assert.equal(p.mode,'INCREMENTAL_CHECK');assert.equal(p.observed_authority_drift,false);
 assert.equal(planOngoingSetup({family,current:{source_hash:'b'},previous:{source_hash:'a'},changes:[]}).mode,'REVERIFY_AUTHORITY');
});
test('malformed or opaque snapshots fail closed instead of reusing receipt',()=>{
 const cyc={};cyc.self=cyc;
 const sparse=Array(2);sparse[1]='x';
 for(const current of [cyc,{lease:undefined},{lease:NaN},{rights:()=>true},
   {lease:new Date('2026-11-18T00:00:00Z')},{rights:sparse}]){
  const p=planOngoingSetup({family,current,previous:{},changes:['theme']});
  assert.equal(p.state,'DENIED');assert.equal(p.reason,'INVALID_RESUME_STATE');
 }
});
