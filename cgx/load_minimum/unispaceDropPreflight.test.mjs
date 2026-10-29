import test from 'node:test';
import assert from 'node:assert/strict';
import {planUniSpaceDropPreflight as plan} from './unispaceDropPreflight.mjs';
const target={object_id:'fixture:eco:existing',file_space:'Eco.cgx',domain:'eco',owner:'Eco-Grex'};
const file={name:'observation.json',type:'application/json',size:123};
const source={source_id:'fixture:eco:source-v2',version:'2',owner:'fixture-owner',sha256:'a'.repeat(64),rights:'OWNER_PRIVATE',proof_class:'scientific'};
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
test('private source never enters public static even with caller ACL list',()=>{
 const x=plan({...args,surface:'public'});assert.equal(x.reason,'PRIVATE_SOURCE_PUBLIC_BOUNDARY');noEffects(x);
 const y=plan({...args,surface:'public',source:{...source,rights:'PUBLIC_SAFE'}});
 assert.equal(y.status,'REVIEW_CANDIDATE');assert.equal(y.public_release,false);
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
  object_id:target.object_id,file_space:target.file_space}];
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
  object_id:target.object_id,file_space:target.file_space};
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
  object_id:target.object_id,file_space:target.file_space};
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
