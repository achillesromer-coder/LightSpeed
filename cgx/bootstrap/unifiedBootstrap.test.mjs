import test from 'node:test';
import assert from 'node:assert/strict';
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
test('no missing returned receipts from invalid mode',()=>{
 assert.equal(planCGXSetup({family,mode:'panic'}).reason,'UNKNOWN_SETUP_MODE');
});
