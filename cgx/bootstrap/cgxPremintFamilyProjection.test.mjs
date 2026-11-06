import test from 'node:test';
import assert from 'node:assert/strict';
import {stageFamilyPacket,projectUniSpace} from './cgxPremintFamilyProjection.mjs';
import {verifyReconstruction,planHydration,verifyEnvelope} from './cgxLeafEnvelopeReview.mjs';
const source=()=>[Buffer.from('The source stays intact; '),Buffer.from('leaves remain verifiable.')];
const base=()=>({objectId:'cgx:load:source',version:'1',originalLeaves:source(),
 family:'Cognigrex.cgx',owner:'achilles',semanticKey:'load:source',
 rights:'internal_only',acl:'owner_only',rightsRef:'owner:rights',aclRef:'owner:acl',
 capabilities:[{capability_id:'cgx:load:reader',kind:'resolver'}]});
test('all five family scopes compose under the single canonical parent',()=>{
 for(const family of ['Cognigrex.cgx','Romer.cgx','Eco.cgx','EMASSC.cgx','LS.cgx']){
  const p=stageFamilyPacket({...base(),family});
  assert.equal(p.state,'PREMINT_REVIEW_ONLY',family);
  assert.equal(p.canonical_parent,'cgx:root:cognigrex');
  assert.equal(p.convergence.metrics.unique_source_ids,1);
  assert.equal(p.convergence.native_admitted,false);
  assert.equal(p.may_mint,false);
  assert.equal(verifyReconstruction(p.envelope,source()),true);
 }
});
test('UniSpace owner H0-H4 projection is metadata only and cannot activate tools',()=>{
 const p=stageFamilyPacket(base());const v=projectUniSpace(p,{requestedLeaves:[1]});
 assert.equal(v.state,'SOURCE_ONLY_PRIVATE_PROJECTION');
 assert.equal(v.h0.object_id,'cgx:load:source');
 assert.equal(v.h1.leaf_count,2);
 assert.equal(v.h2.source_qualified,false);
 assert.equal(v.h3.installed_capabilities_verified,false);
 assert.deepEqual(v.h3.candidate_capability_ids,['cgx:load:reader']);
 assert.equal(v.h4.execution,'DISABLED_AUTHORITY_HOLD');
 assert.equal(v.hydration.state,'HOLD');
 assert.equal(v.network_transfer,false);
 assert.equal(JSON.stringify(v).includes('The source stays intact'),false);
});
test('public projection denied even with public-clear source declarations',()=>{
 const p=stageFamilyPacket({...base(),rights:'public_clear',acl:'public'});
 assert.equal(projectUniSpace(p,{audience:'public'}).reason,'PUBLIC_RELEASE_NOT_AUTHORISED');
 assert.equal(projectUniSpace(p,{audience:'anonymous'}).may_publish,false);
});
test('declared rights and ACL conflict block convergence without erasing source',()=>{
 const p=stageFamilyPacket({...base(),rights:'restricted',acl:'public'});
 assert.equal(p.state,'REVIEW_WITH_HOLDS');
 assert.ok(p.convergence.blockers.some(x=>x.startsWith('RIGHTS_ACL_CONFLICT')));
 assert.equal(verifyReconstruction(p.envelope,source()),true);
});
test('proof claims do not authorize real hydration or remote transfer',()=>{
 const p=stageFamilyPacket(base());
 const v=projectUniSpace(p,{requestedLeaves:[0],proof:{rightsVerified:true,aclVerified:true,sourceHashCurrent:true}});
 assert.equal(v.hydration.state,'REQUEST_PLAN_ONLY');
 assert.equal(v.hydration.network_transfer,false);
 assert.equal(v.h4.native_admitted,false);
});
test('unqualified inputs denied before source review',()=>{
 for(const change of [{family:'UniSpace'},{version:'v1'},{objectId:'../../etc/passwd'},
  {semanticKey:'x\\y'},{owner:'not allowed'}]){
  const p=stageFamilyPacket({...base(),...change});
  assert.equal(p.state,'DENIED');
 }
});
test('capability IDs must be typed review selectors',()=>{
 assert.equal(stageFamilyPacket({...base(),capabilities:[{capability_id:'x',kind:'shell'}]}).reason,'CAPABILITY_REVIEW_INVALID');
});
test('tampered source or packet envelope never produces an owner view',()=>{
 const p=stageFamilyPacket(base());p.envelope.manifest.leaves[0].bytes+=1;
 assert.equal(projectUniSpace(p).state,'DENIED');
});
test('malformed envelope totals, dependencies and source metadata fail closed',()=>{
 for(const change of [
  m=>m.source.bytes=-1,
  m=>m.source.bytes=999,
  m=>m.dependencies=[{object_id:'../escape',version:'1',manifest_sha256:'0'.repeat(64)}],
  m=>m.leaves[0].index=4
 ]){
  const p=stageFamilyPacket(base());change(p.envelope.manifest);
  assert.equal(verifyEnvelope(p.envelope),false);
 }
});
test('null or missing proof results in permission hold, never exception',()=>{
 const p=stageFamilyPacket(base());
 for(const proof of [undefined,null,{},'true']){
  const q=planHydration(p.envelope,[0],proof);
  assert.equal(q.state,'HOLD');
 }
});
