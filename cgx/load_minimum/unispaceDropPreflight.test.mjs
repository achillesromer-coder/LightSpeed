import test from 'node:test';
import assert from 'node:assert/strict';
import {planUniSpaceDropPreflight as plan,planUniSpacePrivateObjectDrop as handoff} from './unispaceDropPreflight.mjs';
const target={object_id:'fixture:eco:existing',file_space:'Eco.cgx',domain:'eco',owner:'Eco-Grex'};
const file={name:'observation.json',type:'application/json',size:123};
const source={source_id:'fixture:eco:source-v2',version:'2',owner:'fixture-owner',sha256:'a'.repeat(64),rights:'OWNER_PRIVATE',proof_class:'scientific',rights_state:'ACTIVE'};
const access={authorized_object_ids:[target.object_id],authorized_file_spaces:[target.file_space]};
const args={target,file,source,access};
const noEffects=x=>{
 for(const k of ['bytes_read','uploaded','network_fetch','hash_verified','acl_verified','object_id_minted','native_admitted','public_release','canonical_mutation'])
  assert.equal(x[k],k==='bytes_read'?0:false,k+' must be inert');
};
test('single exact child and source metadata yields review candidate, never admission',()=>{
 const x=plan(args);assert.equal(x.status,'REVIEW_CANDIDATE');assert.equal(x.target.object_id,target.object_id);
 assert.equal(x.target.file_space,'Eco.cgx');assert.equal(x.proposed_source.hash_status,'DECLARED_UNVERIFIED');noEffects(x);
});
test('cross-Grex FileSpace impersonation and missing scope deny without source disclosure',()=>{
 for(const a of [{...args,target:{...target,domain:'romer'}},{...args,access:{...access,authorized_object_ids:[]}},
  {...args,target:{...target,file_space:'Romer.cgx'}}]){
  const x=plan(a);assert.equal(x.status,'HOLD');assert.ok(!JSON.stringify(x).includes(source.source_id));noEffects(x);
 }
});
test('public source alone cannot promote a private or unqualified target Object_ID',()=>{
 const x=plan({...args,surface:'public'});assert.equal(x.reason,'PRIVATE_SOURCE_PUBLIC_BOUNDARY');noEffects(x);
 for(const targetRights of [undefined,'OWNER_PRIVATE','UNKNOWN','LICENSE_RESTRICTED']){
  const y=plan({...args,surface:'public',target:{...target,rights:targetRights},source:{...source,rights:'PUBLIC_SAFE'}});
  assert.equal(y.status,'HOLD');assert.equal(y.reason,'TARGET_PUBLIC_RIGHTS_UNVERIFIED');
  assert.ok(!JSON.stringify(y).includes(source.source_id));noEffects(y);
 }
 // Even both PUBLIC_SAFE declarations cannot bypass native ACL/rights verification.
 const declared=plan({...args,surface:'public',target:{...target,rights:'PUBLIC_SAFE'},source:{...source,rights:'PUBLIC_SAFE'}});
 assert.equal(declared.status,'HOLD');
 assert.equal(declared.reason,'PUBLIC_ROUTE_REQUIRES_VERIFIED_NATIVE_ACL');
 assert.ok(!JSON.stringify(declared).includes(source.source_id));
 assert.ok(!JSON.stringify(declared).includes(target.object_id));
 assert.equal(declared.acl_verified,false);
 assert.equal(declared.public_release,false);noEffects(declared);
});
test('unknown or restricted rights hold; creative remains distinct from scientific',()=>{
 for(const r of ['UNKNOWN','LICENSE_RESTRICTED'])assert.equal(plan({...args,source:{...source,rights:r}}).status,'HOLD');
 const x=plan({...args,source:{...source,proof_class:'creative'}});
 assert.equal(x.proposed_source.proof_class,'creative');noEffects(x);
});
test('filename traversal, MIME mismatch, oversized, zero or fractional size hold',()=>{
 for(const f of [{...file,name:'../private.json'},{...file,name:'a\\b.json'},{...file,type:'application/x-msdownload'},
  {...file,size:60*1024*1024+1},{...file,size:0},{...file,size:1.5}]){
  const x=plan({...args,file:f});assert.equal(x.status,'HOLD');noEffects(x);
 }
});
test('source collision holds; exact same source identity is a no-op',()=>{
 const exact=[{source_id:source.source_id,sha256:source.sha256,version:source.version,
  owner:source.owner,rights:source.rights,proof_class:source.proof_class,
  object_id:target.object_id,file_space:target.file_space,rights_state:source.rights_state}];
 assert.equal(plan({...args,existing_sources:exact}).status,'NOOP_REVIEW');
 const conflict=[{source_id:source.source_id,sha256:'b'.repeat(64)}];
 assert.equal(plan({...args,existing_sources:conflict}).reason,'SOURCE_IDENTITY_COLLISION');
 assert.equal(plan({...args,existing_sources:[...exact,...exact]}).status,'HOLD');
});
test('invalid source hash, missing owner/version and malformed existing refs fail closed',()=>{
 for(const s of [{...source,sha256:'not-verified'},{...source,owner:''},{...source,version:''}])
  assert.equal(plan({...args,source:s}).status,'HOLD');
 assert.equal(plan({...args,existing_sources:[{source_id:source.source_id,sha256:'bad'}]}).status,'HOLD');
});
test('offline preflight retains metadata-only hold and no network hydration',()=>{
 const x=plan({...args,offline:true});assert.equal(x.reason,'OFFLINE_METADATA_ONLY');noEffects(x);
});

// A same-byte digest is insufficient to collapse distinct R0 versions or grants.
test('same hash requires full version owner rights and proof-class equality before NOOP',()=>{
 const exact={source_id:source.source_id,sha256:source.sha256,version:source.version,
  owner:source.owner,rights:source.rights,proof_class:source.proof_class,
  object_id:target.object_id,file_space:target.file_space,rights_state:source.rights_state};
 const partial=plan({...args,existing_sources:[{source_id:source.source_id,sha256:source.sha256}]});
 assert.equal(partial.status,'HOLD');
 assert.equal(partial.reason,'EXISTING_SOURCE_IDENTITY_UNQUALIFIED');noEffects(partial);
 for(const [field,value] of [['version','1'],['owner','different-owner'],
  ['rights','PUBLIC_SAFE'],['proof_class','creative']]){
  const x=plan({...args,existing_sources:[{...exact,[field]:value}]});
  assert.equal(x.status,'HOLD',field);
  assert.equal(x.reason,'SOURCE_IDENTITY_COLLISION',field);noEffects(x);
  assert.ok(!JSON.stringify(x).includes(source.source_id));
 }
 const matched=plan({...args,existing_sources:[exact]});
 assert.equal(matched.status,'NOOP_REVIEW');noEffects(matched);
});

test('same source identity in another child or Object_ID cannot silently NOOP',()=>{
 const exact={source_id:source.source_id,sha256:source.sha256,version:source.version,
  owner:source.owner,rights:source.rights,proof_class:source.proof_class,
  object_id:target.object_id,file_space:target.file_space,rights_state:source.rights_state};
 for(const prior of [
  {...exact,file_space:'Romer.cgx'},
  {...exact,object_id:'fixture:eco:another-object'}
 ]){
  const x=plan({...args,existing_sources:[prior]});
  assert.equal(x.status,'HOLD');
  assert.equal(x.reason,'EXISTING_REFERENCE_SCOPE_COLLISION');
  assert.ok(!JSON.stringify(x).includes(source.source_id));
  noEffects(x);
 }
 const legacy={...exact};delete legacy.object_id;delete legacy.file_space;
 const x=plan({...args,existing_sources:[legacy]});
 assert.equal(x.status,'HOLD');
 assert.equal(x.reason,'EXISTING_REFERENCE_SCOPE_UNQUALIFIED');
 noEffects(x);
 assert.equal(plan({...args,existing_sources:[exact]}).status,'NOOP_REVIEW');
});

test('Unicode bidi and invisible filename controls cannot spoof a FileSpace drop',()=>{
 for(const name of ['report\u202ejson.exe','note\u200b.json','doc\u2066.json','draft\ufeff.json']){
  const x=plan({...args,file:{...file,name}});
  assert.equal(x.status,'HOLD',JSON.stringify(name));
  assert.equal(x.reason,'FILE_METADATA_OR_SIZE_UNSUPPORTED');
  assert.ok(!JSON.stringify(x).includes(source.source_id));
  noEffects(x);
 }
});


test('bidi and invisible controls in source authority identities fail closed',()=>{
 const cases=[
  [{...args,target:{...target,object_id:target.object_id+'\u202e'}},'EXACT_CHILD_FILESPACE_UNRESOLVED'],
  [{...args,target:{...target,owner:'Romer\u200b'}},'EXACT_CHILD_FILESPACE_UNRESOLVED'],
  [{...args,source:{...source,source_id:source.source_id+'\u202e'}},'SOURCE_QUALIFICATION_INCOMPLETE'],
  [{...args,source:{...source,owner:'owner\u2066'}},'SOURCE_QUALIFICATION_INCOMPLETE'],
  [{...args,source:{...source,version:'2\u200b'}},'SOURCE_QUALIFICATION_INCOMPLETE'],
  [{...args,existing_sources:[{source_id:'alias\u202e',sha256:source.sha256}]},'EXISTING_SOURCE_REGISTRY_UNQUALIFIED']
 ];
 for(const [input,reason] of cases){
  const x=plan(input);
  assert.equal(x.status,'HOLD',reason);
  assert.equal(x.reason,reason);
  noEffects(x);
 }
 const exact={source_id:source.source_id,sha256:source.sha256,version:source.version,
  owner:source.owner,rights:source.rights,proof_class:source.proof_class,
  object_id:target.object_id,file_space:target.file_space,rights_state:source.rights_state};
 for(const [field,value,reason] of [
  ['owner','owner\u200b','EXISTING_SOURCE_IDENTITY_UNQUALIFIED'],
  ['object_id','fixture:eco:existing\u202e','EXISTING_REFERENCE_SCOPE_UNQUALIFIED']
 ]){
  const x=plan({...args,existing_sources:[{...exact,[field]:value}]});
  assert.equal(x.status,'HOLD',field);
  assert.equal(x.reason,reason,field);
  noEffects(x);
 }
 // Accented visible Unicode remains permitted in legitimate display metadata.
 const visible=plan({...args,file:{...file,name:'café.json'},
  source:{...source,owner:'José'},target:{...target,owner:'Römer'}});
 assert.equal(visible.status,'REVIEW_CANDIDATE');
 noEffects(visible);
});


test('C33 revocation supersession and unqualified rights state fail closed before NOOP',()=>{
 const exact={source_id:source.source_id,sha256:source.sha256,version:source.version,
  owner:source.owner,rights:source.rights,proof_class:source.proof_class,
  object_id:target.object_id,file_space:target.file_space,rights_state:'ACTIVE'};
 assert.equal(plan({...args,existing_sources:[exact]}).status,'NOOP_REVIEW');
 for(const state of ['REVOKED','SUPERSEDED','UNRESOLVED']){
  const incoming=plan({...args,source:{...source,rights_state:state},existing_sources:[exact]});
  assert.equal(incoming.reason,'SOURCE_RIGHTS_NOT_ACTIVE',state);noEffects(incoming);
  const prior=plan({...args,existing_sources:[{...exact,rights_state:state}]});
  assert.equal(prior.reason,'EXISTING_RIGHTS_NOT_ACTIVE',state);noEffects(prior);
 }
 for(const signal of [{revoked:true},{rights_revoked:true},{revoked_at:'2026-10-30'},
  {superseded_by:'grant-next'}]){
  const incoming=plan({...args,source:{...source,...signal},existing_sources:[exact]});
  assert.equal(incoming.reason,'SOURCE_RIGHTS_NOT_ACTIVE');noEffects(incoming);
  const prior=plan({...args,existing_sources:[{...exact,...signal}]});
  assert.equal(prior.reason,'EXISTING_RIGHTS_NOT_ACTIVE');noEffects(prior);
 }
 const old={...exact};delete old.rights_state;
 const oldSource={...source};delete oldSource.rights_state;
 for(const x of [plan({...args,existing_sources:[old]}),
  plan({...args,source:oldSource,existing_sources:[exact]})]){
  assert.equal(x.reason,'RIGHTS_STATE_UNQUALIFIED');noEffects(x);
 }
 const malformed=plan({...args,existing_sources:[{...exact,rights_state:'VALID'}]});
 assert.equal(malformed.reason,'EXISTING_RIGHTS_STATE_UNQUALIFIED');noEffects(malformed);
 // No matching source may remain a review candidate; never grants authority.
 const candidate=plan({...args,source:oldSource});
 assert.equal(candidate.status,'REVIEW_CANDIDATE');noEffects(candidate);
});


// Private UniSpace source-inspector → R0 drop preflight integration. Fixtures
// are synthetic, not canonical object identities, signed roots or host receipts.
const inspectorInput={
 surface:'private',file_space:target.file_space,focus_id:target.object_id,
 nodes:[{object_id:target.object_id,file_space:target.file_space,
  domain:target.domain,owner:target.owner,kind:'observation',
  source_refs:[],edges:[],evidence_ceiling:'synthetic'}],
 access:{authorized_object_ids:[target.object_id],authorized_source_ids:[]},
 source_envelopes:[]
};
const scopedDrop={surface:'private',inspectorInput,
 dropInput:{target,file,source,existing_sources:[]}};
const handoffInert=x=>{
 for(const k of ['uploaded','hash_verified','acl_verified','host_authenticated',
  'provider_readback','native_admitted','public_release','canonical_mutation'])
  assert.equal(x[k],false,k);
 assert.equal(x.bytes_read,0);
};

test('private inspector to R0 intake handoff never promotes caller proof or mints an ID',()=>{
 const x=handoff(scopedDrop);
 assert.equal(x.state,'SOURCE_REVIEW_ONLY');
 assert.equal(x.selected_object_id,target.object_id);
 assert.equal(x.selected_file_space,'Eco.cgx');
 assert.equal(x.family,'Cognigrex.cgx');
 assert.equal(x.source_view_state,'FRONTIER');
 assert.equal(x.intake_preflight,'REVIEW_CANDIDATE');
 assert.equal(x.source.source_id,source.source_id);
 assert.equal(x.source.hash_status,'DECLARED_UNVERIFIED');
 assert.ok(x.blockers.includes('SIGNED_NATIVE_OBJECT_ID_ROOT_LEASE_DBR_NOT_VERIFIED'));
 handoffInert(x);
});

test('public surface, inconsistent context and a second ACL cannot bypass private scope',()=>{
 for(const patch of [
  {...scopedDrop,surface:'public'},
  {...scopedDrop,surface:undefined},
  {...scopedDrop,inspectorInput:{...inspectorInput,surface:'public'}},
  {...scopedDrop,dropInput:{...scopedDrop.dropInput,surface:'public'}},
  {...scopedDrop,dropInput:{...scopedDrop.dropInput,access:{
   authorized_object_ids:['fixture:other'],authorized_file_spaces:['Romer.cgx']}}
  }
 ]){
  const x=handoff(patch);
  assert.equal(x.state,'DENIED');
  assert.ok(!JSON.stringify(x).includes(source.source_id));
  assert.ok(!JSON.stringify(x).includes(target.object_id));
  handoffInert(x);
 }
});

test('changed Object_ID, child or owner between inspector and intake fails closed',()=>{
 for(const t of [
  {...target,object_id:'fixture:eco:other'},
  {...target,file_space:'Romer.cgx'},
  {...target,domain:'romer'},
  {...target,owner:'competing-owner'}
 ]){
  const x=handoff({...scopedDrop,dropInput:{...scopedDrop.dropInput,target:t}});
  assert.equal(x.state,'DENIED');
  assert.ok(!JSON.stringify(x).includes(source.source_id));
  handoffInert(x);
 }
 const spoofed={...inspectorInput,nodes:[{
  ...inspectorInput.nodes[0],domain:'romer'
 }]};
 assert.equal(handoff({...scopedDrop,inspectorInput:spoofed}).state,'DENIED');
});

test('offline intake, revoked source and missing rights state cannot become a proposal',()=>{
 const cases=[
  {...scopedDrop,offline:true},
  {...scopedDrop,inspectorInput:{...inspectorInput,offline:true}},
  {...scopedDrop,dropInput:{...scopedDrop.dropInput,source:{...source,rights_state:'REVOKED'}}},
  {...scopedDrop,dropInput:{...scopedDrop.dropInput,source:{...source,revoked:true}}},
  {...scopedDrop,dropInput:{...scopedDrop.dropInput,source:{...source,rights_state:undefined}}}
 ];
 for(const input of cases){
  const x=handoff(input);
  assert.equal(x.state,'DENIED');
  assert.ok(!JSON.stringify(x).includes(source.source_id));
  handoffInert(x);
 }
});

test('source collisions remain holds; exact scoped duplicate is only a NOOP review',()=>{
 const prior={source_id:source.source_id,sha256:source.sha256,
  version:source.version,owner:source.owner,rights:source.rights,
  proof_class:source.proof_class,object_id:target.object_id,
  file_space:target.file_space,rights_state:'ACTIVE'};
 const conflict=handoff({...scopedDrop,dropInput:{...scopedDrop.dropInput,
  existing_sources:[{...prior,file_space:'Romer.cgx'}]}});
 assert.equal(conflict.state,'DENIED');
 handoffInert(conflict);
 const noop=handoff({...scopedDrop,dropInput:{...scopedDrop.dropInput,
  existing_sources:[prior]}});
 assert.equal(noop.state,'SOURCE_REVIEW_ONLY');
 assert.equal(noop.intake_preflight,'NOOP_REVIEW');
 assert.equal(noop.source,null);
 assert.equal(noop.provider_readback,false);
 handoffInert(noop);
});

test('forged host/science proof cannot elevate private handoff into execution',()=>{
 const x=handoff({...scopedDrop,host_authenticated:true,provider_readback:true,
  native_admitted:true,dropInput:{...scopedDrop.dropInput,
   signedRootVerified:true,source:{...source,scientificVerified:true,
    hashVerified:true,rightsVerified:true},hostToken:'PRIVATE_DO_NOT_ECHO'}});
 assert.equal(x.state,'SOURCE_REVIEW_ONLY');
 assert.equal(x.source_proof,'CALLER_DECLARATION_NOT_PROVIDER_VERIFIED');
 assert.equal(x.installed,false);
 assert.ok(!JSON.stringify(x).includes('PRIVATE_DO_NOT_ECHO'));
 handoffInert(x);
});


test('selected R0 source identity cannot be silently reintroduced by drop',()=>{
 const selectedSource=source.source_id;
 const inspected={
  ...inspectorInput,
  nodes:[{...inspectorInput.nodes[0],source_refs:[selectedSource]}],
  access:{...inspectorInput.access,authorized_source_ids:[selectedSource]},
  source_envelopes:[{...source,sha256:'b'.repeat(64)}]
 };
 // Matching and changed R0 bytes are both native-resolution questions,
 // never a browser duplicate decision or a novel source proposal.
 for(const incoming of [
  {...source,sha256:'b'.repeat(64)},
  {...source,sha256:'c'.repeat(64),version:'3'},
  source
 ]){
  const x=handoff({...scopedDrop,inspectorInput:inspected,
   dropInput:{...scopedDrop.dropInput,source:incoming}});
  assert.equal(x.state,'DENIED');
  assert.equal(x.reason,'SELECTED_R0_SOURCE_ID_REQUIRES_NATIVE_RESOLUTION');
  assert.ok(!JSON.stringify(x).includes(selectedSource));
  handoffInert(x);
 }
 // A distinct source identity can still be proposed for independent review.
 const novel=handoff({...scopedDrop,inspectorInput:inspected,
  dropInput:{...scopedDrop.dropInput,
   source:{...source,source_id:'fixture:eco:novel-r0'}}});
 assert.equal(novel.state,'SOURCE_REVIEW_ONLY');
 assert.equal(novel.intake_preflight,'REVIEW_CANDIDATE');
 assert.equal(novel.native_admitted,false);
 handoffInert(novel);
});


test('NFC and default-ignorable Unicode cannot create competing source identities',()=>{
 const cases=[
  [{...args,target:{...target,owner:'Cafe\u0301'}},'EXACT_CHILD_FILESPACE_UNRESOLVED'],
  [{...args,source:{...source,source_id:'fixture:eco:cafe\u0301'}},'SOURCE_QUALIFICATION_INCOMPLETE'],
  [{...args,source:{...source,source_id:source.source_id+'\u034f'}},'SOURCE_QUALIFICATION_INCOMPLETE'],
  [{...args,source:{...source,version:'2\uFE0F'}},'SOURCE_QUALIFICATION_INCOMPLETE'],
  [{...args,existing_sources:[{source_id:source.source_id+'\u034f',sha256:source.sha256}]},'EXISTING_SOURCE_REGISTRY_UNQUALIFIED']
 ];
 for(const [input,reason] of cases){
  const x=plan(input);
  assert.equal(x.status,'HOLD',reason);
  assert.equal(x.reason,reason);
  assert.ok(!JSON.stringify(x).includes(source.source_id));
  noEffects(x);
 }
 const prior={source_id:source.source_id,sha256:source.sha256,
  version:source.version,owner:'Cafe\u0301',rights:source.rights,
  proof_class:source.proof_class,object_id:target.object_id,
  file_space:target.file_space,rights_state:'ACTIVE'};
 const y=plan({...args,existing_sources:[prior]});
 assert.equal(y.reason,'EXISTING_SOURCE_IDENTITY_UNQUALIFIED');
 noEffects(y);
 // NFC accented identifiers remain legal; they are not transliterated.
 const allowed=plan({...args,source:{...source,source_id:'fixture:eco:café',owner:'José'},
  target:{...target,owner:'Römer'}});
 assert.equal(allowed.status,'REVIEW_CANDIDATE');
 noEffects(allowed);
});


test('public route cannot elevate caller-supplied host or DBR receipts into source disclosure',()=>{
 const x=plan({...args,surface:'public',target:{...target,rights:'PUBLIC_SAFE'},
  source:{...source,rights:'PUBLIC_SAFE'},access:{...access,
   host_authenticated:true,acl_verified:true,root_signed:true,dbr_readback:true},
  hostReceipt:{verified:true,issuer:'caller-only'}});
 assert.equal(x.status,'HOLD');
 assert.equal(x.reason,'PUBLIC_ROUTE_REQUIRES_VERIFIED_NATIVE_ACL');
 assert.ok(!JSON.stringify(x).includes(source.source_id));
 assert.ok(!JSON.stringify(x).includes(target.object_id));
 noEffects(x);
});
