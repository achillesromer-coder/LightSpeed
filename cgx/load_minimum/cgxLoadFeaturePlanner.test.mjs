import assert from 'node:assert/strict';
import test from 'node:test';
import { ACTIONS, menuForTarget, planFeature } from './cgxLoadFeaturePlanner.mjs';
const target = {kind:'filespace',fileSpace:'Romer.cgx',domain:'romer',owner:'Römer-Grex',objectId:'cgx:accepted:example',parentFileSpace:'Cognigrex.cgx'};
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

test('menu cannot propose host preflight for a competing parent or wrong Grex child',()=>{
 const variants=[
  [{...target,parentFileSpace:'OtherRoot.cgx'},'COMPETING_PARENT_ROOT'],
  [{...target,domain:'eco'},'CHILD_FILESPACE_SCOPE_CONFLICT'],
  [{...target,domain:'unknown'},'CHILD_FILESPACE_SCOPE_CONFLICT'],
  [{...target,fileSpace:'Eco.cgx'},'CHILD_FILESPACE_SCOPE_CONFLICT'],
  [{...target,domain:'romer',fileSpace:'LS.cgx'},'CHILD_FILESPACE_SCOPE_CONFLICT']
 ];
 for(const [bad,reason] of variants){
  const x=planFeature({action:'load.attach',target:bad,...good});
  assert.equal(x.state,'DENIED');
  assert.equal(x.reason,reason);
  assert.ok(!Object.hasOwn(x,'install'));
 }
 const valid=planFeature({action:'load.attach',target,...good});
 assert.equal(valid.status,'READY_FOR_AUTHENTICATED_HOST_PREFLIGHT');
 assert.equal(valid.target.domain,'romer');
 assert.equal(valid.target.parentFileSpace,'Cognigrex.cgx');
 assert.equal(valid.install,false);
 assert.equal(valid.canonicalMutation,false);
});
test('missing child domain is a non-executable review HOLD rather than an accepted scope',()=>{
 const x=planFeature({action:'load.attach',target:{...target,domain:undefined},...good});
 assert.equal(x.status,'REVIEW_ONLY');
 assert.ok(x.blockers.includes('CHILD_DOMAIN_UNVERIFIED'));
 assert.equal(x.target.domain,null);
 assert.equal(x.canonicalMutation,false);
 assert.equal(x.install,false);
});
test('opaque menu identifiers reject bidi, default-ignorable and non-NFC ambiguity',()=>{
 for(const mark of ['\u202e','\u200b','\u034f']){
  for(const key of ['fileSpace','domain','owner','objectId']){
   const bad={...target,[key]:target[key]+mark};
   const x=planFeature({action:'alexandria.resolve',target:bad,...good});
   assert.equal(x.state,'DENIED',key);
   assert.equal(x.reason,'AMBIGUOUS_IDENTITY_OR_SCOPE',key);
  }
  const capability=planFeature({action:'ccc.install',target,capabilityId:'fixture:cap'+mark,...good});
  assert.equal(capability.reason,'AMBIGUOUS_IDENTITY_OR_SCOPE');
 }
 const decomposed=planFeature({action:'alexandria.resolve',target:{...target,objectId:'cafe\u0301'},...good});
 assert.equal(decomposed.reason,'AMBIGUOUS_IDENTITY_OR_SCOPE');
 const normal=planFeature({action:'alexandria.resolve',target:{...target,owner:'Römer-Grex'},...good});
 assert.equal(normal.status,'REVIEW_ONLY');
 assert.equal(normal.networkFetch,false);
});
