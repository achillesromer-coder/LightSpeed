import assert from 'node:assert/strict';
import test from 'node:test';
import { ACTIONS, menuForTarget, planFeature } from './cgxLoadFeaturePlanner.mjs';
const target = {kind:'filespace',fileSpace:'Romer.cgx',owner:'Römer-Grex',objectId:'cgx:accepted:example',parentFileSpace:'Cognigrex.cgx'};
const good = { readable:true, acceptedParent:true, existingAliasChecked:true, ownerApproved:true, rightsVerified:true, signedLeaseVerified:true, providerReadbackReady:true, registeredCapabilityVerified:true };
test('right click on selected child offers LOAD and CCC without creating new masters',()=>{
 const menu=menuForTarget('filespace',{readable:true});assert.ok(menu.includes('load.attach'));assert.ok(menu.includes('ccc.install'));
 assert.equal(menuForTarget('filespace',{readable:false}).length,0);
 assert.ok(!menuForTarget('file',{readable:true}).includes('load.attach'));
});
test('missing identity holds and never guesses from name',()=>{
 const v=planFeature({action:'load.attach',target:{...target,objectId:null},...good});assert.equal(v.status,'REVIEW_ONLY');assert.ok(v.blockers.includes('EXACT_OBJECT_ID_UNRESOLVED'));
});
test('offline minimal inspect is read-only',()=>{
 const v=planFeature({action:'alexandria.open',target,...good,offline:true});assert.equal(v.status,'REVIEW_ONLY');assert.equal(v.offlineMode,'MINIMAL_LOCAL_REFERENCE');assert.equal(v.networkFetch,false);
});
test('missing owner authority holds install despite other validations',()=>{
 const v=planFeature({action:'load.attach',target,...good,ownerApproved:false});assert.ok(v.blockers.includes('OWNER_CONSENT_REQUIRED'));assert.equal(v.install,false);
});
test('fully declared context only qualifies for real host preflight, never execution',()=>{
 const v=planFeature({action:'load.attach',target,...good,mode:'EMBED'});
 assert.equal(v.status,'READY_FOR_AUTHENTICATED_HOST_PREFLIGHT');assert.equal(v.canonicalMutation,false);assert.equal(v.install,false);assert.equal(v.wizard.length,6);
});
test('CCC discover requires actual registration',()=>{
 const v=planFeature({action:'ccc.discover',target,readable:true});assert.ok(v.blockers.includes('CCC_CAPABILITY_REGISTRATION_UNVERIFIED'));
});
test('cross-target menu action denied',()=>{
 const v=planFeature({action:'load.attach',target:{...target,kind:'file'},...good});assert.equal(v.reason,'ACTION_NOT_APPLICABLE');
});
test('rejects unbounded source',()=>{
 const v=planFeature({action:'alexandria.resolve',target,...good,sourceByteCount:70*1024*1024});assert.equal(v.reason,'BOUNDED_SOURCE_EXCEEDED');
});
test('rejects path traversal in scope and control-character object identifiers',()=>{
 assert.equal(planFeature({action:'alexandria.open',target:{...target,fileSpace:'../private'},...good}).reason,'INVALID_TARGET');
 assert.equal(planFeature({action:'alexandria.open',target:{...target,objectId:'not\nvalid'},...good}).reason,'INVALID_OBJECT_ID');
});
test('hydration requires permission and cannot fetch remotely',()=>{
 const v=planFeature({action:'load.hydrate',target,...good,hydration:'on-demand'});assert.ok(v.blockers.includes('NETWORK_HYDRATION_NOT_AUTHORIZED'));assert.equal(v.networkFetch,false);
});
test('no action can mutate, install, execute, publish or transmit',()=>{
 for (const action of Object.keys(ACTIONS)) {
  const kind=action==='alexandria.sources'?'object':'filespace';
  const v=planFeature({action,target:{...target,kind},capabilityId:'cgx:cap:test',...good,networkPermission:true});
  assert.notEqual(v.state,'DENIED',action);
  for(const key of ['canonicalMutation','networkFetch','install','execute','publish'])assert.equal(v[key],false,action + ': ' + key);
 }
});
test('invalid request forms rejected',()=>{
 assert.equal(planFeature(null).reason,'INVALID_REQUEST');assert.equal(planFeature({action:'fake',target}).reason,'UNKNOWN_ACTION');
 assert.equal(planFeature({action:'load.attach',target,...good,mode:'MOVE'}).reason,'UNKNOWN_COMPOSITION_MODE');
});

test('CCC install requires named capability, not just a generic install flag',()=>{
 const v=planFeature({action:'ccc.install',target,...good});assert.equal(v.reason,'CAPABILITY_ID_REQUIRED');
});
