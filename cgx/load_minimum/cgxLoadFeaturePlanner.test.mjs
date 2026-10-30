import assert from 'node:assert/strict';
import test from 'node:test';
import { ACTIONS, menuForTarget, planFeature, planSourceDropPreflight } from './cgxLoadFeaturePlanner.mjs';
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


test('metadata-only FileSpace drop is source-review preflight, not native intake',()=>{
 const file={name:'field-observation.json',size:2048,type:'application/json',
  sha256:'a'.repeat(64),sourceId:'source:existing:one',revision:'rev:one',
  owner:'Römer-Grex',rights:'OWNER_PRIVATE',proofClass:'historical'};
 const x=planSourceDropPreflight({surface:'private',target,file,readable:true});
 assert.equal(x.state,'REVIEW_ONLY');
 assert.equal(x.admissionStage,'R0_METADATA_PREFLIGHT');
 assert.equal(x.target.fileSpace,'Romer.cgx');
 assert.equal(x.target.objectId,'cgx:accepted:example');
 assert.equal(x.source.byteCount,2048);
 assert.equal(x.source.digestClaimPresent,true);
 assert.ok(x.blockers.includes('SOURCE_HASH_NOT_PROVIDER_VERIFIED'));
 assert.ok(x.blockers.includes('CURRENT_HOST_ACL_UNVERIFIED'));
 assert.ok(x.blockers.includes('PUBLIC_STATIC_ASSET_ROUTE_FORBIDDEN'));
 for(const k of ['sourceBytesRead','hashVerified','hostAuthenticated','providerReadback',
  'nativeAdmitted','canonicalMutation','networkFetch','install','execute','publicRelease','rendered'])
  assert.equal(x[k],false,k);
 assert.equal(x.transferBudgetBytes,0);
 assert.ok(!JSON.stringify(x).includes('a'.repeat(64)));
 assert.ok(!JSON.stringify(x).includes('source:existing:one'));
});

test('drop rejects unsafe names, hidden assets, Unicode ambiguity, MIME and unbounded sizes',()=>{
 const file={name:'source.txt',size:1,type:'text/plain'};
 const bad=[
  [{...file,name:'../private'},'INVALID_SOURCE_METADATA'],
  [{...file,name:'.env'},'INVALID_SOURCE_METADATA'],
  [{...file,name:'CON.txt'},'INVALID_SOURCE_METADATA'],
  [{...file,name:'a<script>.txt'},'INVALID_SOURCE_METADATA'],
  [{...file,name:'spoof\u202e.txt'},'INVALID_SOURCE_METADATA'],
  [{...file,name:'cafe\u0301.txt'},'INVALID_SOURCE_METADATA'],
  [{...file,type:'text/html;evil'},'INVALID_SOURCE_METADATA'],
  [{...file,size:60*1024*1024+1},'BOUNDED_SOURCE_EXCEEDED'],
  [{...file,size:NaN},'BOUNDED_SOURCE_EXCEEDED'],
  [{...file,sha256:'not-a-digest'},'INVALID_UNVERIFIED_DIGEST_CLAIM'],
  [{...file,sourceId:'source\u200b'},'AMBIGUOUS_SOURCE_METADATA'],
  [{...file,rights:'GRANTED'},'UNKNOWN_RIGHTS_DECLARATION'],
  [{...file,proofClass:'scientifically_validated'},'UNKNOWN_PROOF_CLASS']
 ];
 for(const [input,reason] of bad){
  const x=planSourceDropPreflight({surface:'private',target,file:input,readable:true});
  assert.equal(x.state,'DENIED',reason);
  assert.equal(x.reason,reason);
  assert.equal(x.publicRelease,false);
  assert.equal(x.canonicalMutation,false);
  assert.ok(!Object.hasOwn(x,'source'));
 }
});

test('offline drop cannot claim hash, rights, native admission or source qualification',()=>{
 const x=planSourceDropPreflight({surface:'private',target:{...target,objectId:null},
  file:{name:'archive.txt',size:0,type:'',rights:'LICENSE_RESTRICTED',proofClass:'unknown'},
  offline:true,readable:true});
 assert.equal(x.state,'REVIEW_ONLY');
 for(const reason of ['EXACT_OBJECT_ID_UNRESOLVED','SOURCE_DIGEST_NOT_SUPPLIED',
  'SOURCE_ID_OR_REVISION_UNRESOLVED','SOURCE_OWNER_UNRESOLVED',
  'LICENSE_TERMS_UNRESOLVED','PROOF_CLASS_UNRESOLVED','MIME_UNVERIFIED',
  'EMPTY_SOURCE_REVIEW_REQUIRED','OFFLINE_AUTHORITY_AND_REVOCATION_UNVERIFIED'])
  assert.ok(x.blockers.includes(reason),reason);
 assert.equal(x.source.rightsClaim,'LICENSE_RESTRICTED');
 assert.equal(x.source.digestClaimPresent,false);
 assert.equal(x.nativeAdmitted,false);
 assert.equal(x.publicRelease,false);
});

test('drop must remain in selected child and cannot be used as a public or file-target intake',()=>{
 const file={name:'public-safe.png',size:1024,type:'image/png',rights:'PUBLIC_SAFE'};
 const wrong=planSourceDropPreflight({surface:'private',target:{...target,domain:'eco'},file,readable:true});
 assert.equal(wrong.state,'DENIED');
 assert.equal(wrong.reason,'CHILD_FILESPACE_SCOPE_CONFLICT');
 const competing=planSourceDropPreflight({surface:'private',target:{...target,parentFileSpace:'Second.cgx'},file,readable:true});
 assert.equal(competing.reason,'COMPETING_PARENT_ROOT');
 const fileTarget=planSourceDropPreflight({surface:'private',target:{...target,kind:'file'},file});
 assert.equal(fileTarget.reason,'DROP_REQUIRES_CHILD_FILESPACE');
 const x=planSourceDropPreflight({surface:'private',target,file,readable:true});
 assert.equal(x.state,'REVIEW_ONLY');
 assert.equal(x.source.rightsClaim,'PUBLIC_SAFE');
 assert.equal(x.publicRelease,false);
 assert.ok(x.blockers.includes('SOURCE_RIGHTS_NOT_PROVIDER_VERIFIED'));
 assert.ok(x.blockers.includes('PUBLIC_STATIC_ASSET_ROUTE_FORBIDDEN'));
});

test('drop preflight fails closed outside explicit private surface without leaking source or Object_ID',()=>{
 const file={name:'owner-secret-candidate.json',size:1024,type:'application/json',
  rights:'OWNER_PRIVATE',sourceId:'private:source',sha256:'b'.repeat(64)};
 for(const surface of [undefined,null,'public','static','private-preview','PRIVATE',true]){
  const x=planSourceDropPreflight({target,file,readable:true,surface});
  assert.equal(x.state,'DENIED');
  assert.equal(x.reason,'PRIVATE_DROP_SURFACE_REQUIRED');
  assert.equal(x.canonicalMutation,false);
  assert.equal(x.sourceBytesRead,false);
  assert.equal(x.hashVerified,false);
  assert.equal(x.publicRelease,false);
  assert.ok(!Object.hasOwn(x,'source'));
  assert.ok(!Object.hasOwn(x,'target'));
  assert.ok(!JSON.stringify(x).includes('owner-secret-candidate'));
  assert.ok(!JSON.stringify(x).includes('cgx:accepted:example'));
 }
 const privatePlan=planSourceDropPreflight({target,file,readable:true,surface:'private'});
 assert.equal(privatePlan.state,'REVIEW_ONLY');
 assert.equal(privatePlan.hostAuthenticated,false);
 assert.equal(privatePlan.providerReadback,false);
 assert.equal(privatePlan.publicRelease,false);
});

test('unreadable private drop refuses metadata and Object_ID disclosure before scope planning',()=>{
 const file={name:'owner-private-report.json',size:300,type:'application/json',
  sourceId:'private:original:one',sha256:'f'.repeat(64),rights:'OWNER_PRIVATE'};
 for(const readable of [undefined,false]){
  const x=planSourceDropPreflight({surface:'private',target,file,readable});
  assert.equal(x.state,'DENIED');
  assert.equal(x.reason,'PRIVATE_READ_SCOPE_REQUIRED');
  assert.equal(x.canonicalMutation,false);
  assert.equal(x.sourceBytesRead,false);
  assert.equal(x.hashVerified,false);
  assert.equal(x.publicRelease,false);
  assert.ok(!Object.hasOwn(x,'source'));
  assert.ok(!Object.hasOwn(x,'target'));
  for(const secret of [file.name,file.sourceId,target.objectId,file.sha256])
   assert.ok(!JSON.stringify(x).includes(secret));
 }
 const review=planSourceDropPreflight({surface:'private',target,file,readable:true});
 assert.equal(review.state,'REVIEW_ONLY');
 assert.equal(review.hostAuthenticated,false);
 assert.equal(review.providerReadback,false);
 assert.equal(review.nativeAdmitted,false);
 assert.equal(review.publicRelease,false);
});
