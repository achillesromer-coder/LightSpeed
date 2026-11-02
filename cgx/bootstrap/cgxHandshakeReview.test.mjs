import {readFileSync} from 'node:fs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {planCGXHandshake,reviewNativeLeaseHandshakeABI} from './cgxHandshakeReview.mjs';
const base={
 parent:{object_id:'fixture:root',state_root:'a'.repeat(64),dbr_root:'b'.repeat(64)},
 child:{object_id:'fixture:eco',parent_object_id:'fixture:root',filespace:'Eco.cgx'},
 lease:{lease_id:'fixture:lease',target_object_id:'fixture:eco',scope:'compute_only',
  signer_ref:{key_id:'fixture:key'},expires_utc:'2026-11-01T00:00:00Z'},
 now:'2026-10-28T00:00:00Z'
};
const exchange={transfer_id:'fixture:transfer',source_node_id:'fixture:sender',target_node_id:'fixture:receiver',
 source_ref:'fixture:r0',source_sha256:'c'.repeat(64),size_bytes:40,target_root_id:'fixture:root',
 target_relative_path:'staged/chunk1',created_utc:'2026-10-28T00:00:00Z',
 receiver_receipt:{sha256:'c'.repeat(64),size_bytes:40}};
test('fully described fields are not cryptographic attestation',()=>{
 const r=planCGXHandshake({...base,exchange});
 assert.equal(r.status,'UNVERIFIED_SHAPE_REVIEW');assert.equal(r.host_signature_verified,false);
 assert.equal(r.may_execute,false);assert.equal(r.ls_go_toggle_enabled,false);
});
test('child FileSpace names fail closed consistently with Windows basename safety',()=>{
 for(const filespace of [
  '../escape.cgx','..\\escape.cgx','C:stream.cgx','CON.cgx',
  'LPT1.cgx','CONIN$.cgx','CONOUT$.cgx','bad\u200b.cgx',
  'bad\n.cgx','e\u0301.cgx','a%2fb.cgx','Other-Science.CGX',
  'x'.repeat(129)+'.cgx','staged/Other-Science.cgx',
  'Ordinary .cgx','Ordinary.v2 .cgx','CON .cgx','LPT1 .cgx'
 ]){
  const result=planCGXHandshake({...base,child:{...base.child,filespace}});
  assert.equal(result.status,'DENIED',JSON.stringify(filespace));
  assert.equal(result.reason,'UNSAFE_CHILD_FILESPACE',JSON.stringify(filespace));
 }
 for(const filespace of ['Eco.cgx','Other-Science.cgx','café.cgx']){
  const result=planCGXHandshake({...base,child:{...base.child,filespace}});
  assert.equal(result.status,'UNVERIFIED_SHAPE_REVIEW',filespace);
  assert.equal(result.may_execute,false);
 }
});
test('foreign child parent rejected',()=>assert.equal(
 planCGXHandshake({...base,child:{...base.child,parent_object_id:'fixture:other'}}).reason,'CROSS_PARENT_CHILD'));
test('lease belongs to exact child',()=>assert.equal(
 planCGXHandshake({...base,lease:{...base.lease,target_object_id:'fixture:other'}}).reason,'LEASE_SUBJECT_MISMATCH'));
test('expired lease held',()=>assert.ok(
 planCGXHandshake({...base,now:'2026-12-01T00:00:00Z'}).holds.includes('LEASE_EXPIRED')));
test('unqualified root hash rejected',()=>assert.equal(
 planCGXHandshake({...base,parent:{...base.parent,dbr_root:'bad'}}).reason,'INVALID_ROOT_HASH'));
test('loopback is not an independent second node',()=>assert.ok(
 planCGXHandshake({...base,exchange:{...exchange,target_node_id:exchange.source_node_id}}).holds.includes('DISTINCT_SECOND_NODE_NOT_PROVEN')));
test('missing matching receiver sha/size cannot qualify transfer',()=>assert.ok(
 planCGXHandshake({...base,exchange:{...exchange,receiver_receipt:{sha256:'f'.repeat(64),size_bytes:40}}})
 .holds.includes('EXACT_RECEIVER_HASH_SIZE_READBACK_REQUIRED')));
test('source transfer path traversal rejected',()=>assert.equal(
 planCGXHandshake({...base,exchange:{...exchange,target_relative_path:'../unsafe'}}).reason,'UNSAFE_TRANSFER_TARGET'));
test('Windows alternate data streams and encoded traversal are unsafe transfer targets',()=>{
 for(const target_relative_path of ['staged/data.bin:shadow','staged/%2e%2e/secret',
  'staged/%2Froot','staged/%252e%252e/secret']){
  assert.equal(planCGXHandshake({...base,exchange:{...exchange,target_relative_path}}).reason,
   'UNSAFE_TRANSFER_TARGET');
 }
});
test('portable transfer path segments must fit both UTF-8 and UTF-16 limits',()=>{
 const unsafe=[
  'staged/'+ 'a'.repeat(256), // 256 ASCII bytes in one component
  'staged/'+ 'é'.repeat(128), // 128 UTF-16 units but 256 UTF-8 bytes
  'staged/'+ '😀'.repeat(64), // 128 UTF-16 units but 256 UTF-8 bytes
  'staged/'+ 'a'.repeat(4090), // exceeds total 4096 UTF-16 units
 ];
 for(const target_relative_path of unsafe){
  const result=planCGXHandshake({...base,exchange:{...exchange,target_relative_path}});
  assert.equal(result.status,'DENIED');
  assert.equal(result.reason,'UNSAFE_TRANSFER_TARGET');
 }
 for(const target_relative_path of ['staged/'+ 'a'.repeat(255),'staged/'+ 'é'.repeat(127)]){
  const result=planCGXHandshake({...base,exchange:{...exchange,target_relative_path}});
  assert.equal(result.status,'UNVERIFIED_SHAPE_REVIEW');
  assert.equal(result.may_execute,false);
 }
});

test('source segment above 60 MiB is held',()=>assert.ok(
 planCGXHandshake({...base,exchange:{...exchange,size_bytes:70*1024*1024}}).holds.includes('BOUNDED_TRANSFER_SEGMENT_REQUIRED')));
test('missing signer reference held',()=>assert.ok(
 planCGXHandshake({...base,lease:{...base.lease,signer_ref:null}}).holds.includes('SIGNED_LEASE_PROVIDER_REQUIRED')));
test('no operational or release authority granted by planner',()=>{
 const r=planCGXHandshake({...base,exchange});
 for (const prop of ['host_signature_verified','db_r_mutated','node_transfer_executed','may_execute','may_publish'])assert.equal(r[prop],false);
});

test('forged signer and request-looking fields never qualify issuer, scope or nonce consumption',()=>{
 const lease={...base.lease,signer_ref:{key_id:'fixture:untrusted-key'},
  request_nonce:'fixture:nonce',object_id:base.child.object_id,tool_id:'fixture:tool',
  resource_usage:{compute_ms:1},scope:'digital_write'};
 const result=planCGXHandshake({...base,lease});
 assert.equal(result.status,'UNVERIFIED_SHAPE_REVIEW');
 for(const gate of ['ISSUER_ROOT_AUTHORITY_NOT_VERIFIED',
   'REQUEST_BOUND_OBJECT_TOOL_RESOURCE_SCOPE_NOT_VERIFIED',
   'LEASE_NONCE_CONSUMPTION_NOT_VERIFIED']) assert.ok(result.holds.includes(gate));
 assert.equal(result.host_signature_verified,false);
 assert.equal(result.root_authority_verified,false);
 assert.equal(result.may_execute,false);
});
test('repeating a self-claimed nonce cannot turn a source plan into an execution receipt',()=>{
 const lease={...base.lease,request_nonce:'fixture:reused-nonce'};
 const first=planCGXHandshake({...base,lease});
 const second=planCGXHandshake({...base,lease});
 for(const result of [first,second]){
  assert.ok(result.holds.includes('LEASE_NONCE_CONSUMPTION_NOT_VERIFIED'));
  assert.equal(result.may_execute,false);
  assert.equal(result.db_r_mutated,false);
 }
});

test('malformed or timezone-free transfer timestamps are rejected before review',()=>{
 for(const created_utc of ['not-a-date','2026-10-28T00:00:00']){
  assert.equal(planCGXHandshake({...base,exchange:{...exchange,created_utc}}).reason,'INVALID_TRANSFER_TIMESTAMP');
 }
});
test('Windows drive-root transfer path is never treated as relative',()=>{
 assert.equal(planCGXHandshake({...base,exchange:{...exchange,target_relative_path:'C:/CGX/unsafe'}}).reason,'UNSAFE_TRANSFER_TARGET');
});

test('impossible calendar dates fail closed in transfer, lease expiry and supplied now',()=>{
 for(const stamp of ['2026-02-30T00:00:00Z','2026-04-31T00:00:00Z','2026-10-28T00:00:00+15:00']){
  assert.equal(planCGXHandshake({...base,exchange:{...exchange,created_utc:stamp}}).reason,'INVALID_TRANSFER_TIMESTAMP');
  assert.ok(planCGXHandshake({...base,lease:{...base.lease,expires_utc:stamp}}).holds.includes('INVALID_LEASE_EXPIRY'));
  assert.equal(planCGXHandshake({...base,now:stamp}).reason,'INVALID_NOW');
 }
});
test('valid leap-day and explicit offset remain source-review only',()=>{
 const r=planCGXHandshake({...base,now:'2028-02-29T12:00:00+10:00',
  lease:{...base.lease,expires_utc:'2028-03-01T00:00:00Z'},
  exchange:{...exchange,created_utc:'2028-02-29T12:00:00+10:00'}});
 assert.equal(r.status,'UNVERIFIED_SHAPE_REVIEW');
 assert.ok(!r.holds.includes('INVALID_LEASE_EXPIRY'));
 assert.equal(r.may_execute,false);
});

test('portable transfer targets reject aliasing, reserved devices and ambiguous segments',()=>{
 for(const target_relative_path of [
  'staged//chunk1','staged/./chunk1','staged/CON','staged/CON.txt',
  'staged/aux','staged/NUL.bin','staged/COM1.log','staged/LPT9',
  'staged/trailing.','staged/trailing ','staged/ leading',
  'staged/cafe\u0301.txt','staged/\u202ehidden'
 ]){
  assert.equal(planCGXHandshake({...base,exchange:{...exchange,target_relative_path}}).reason,
   'UNSAFE_TRANSFER_TARGET',target_relative_path);
 }
 for(const target_relative_path of ['staged/chunk1','staged/café.txt','staged/report_v2.json']){
  const result=planCGXHandshake({...base,exchange:{...exchange,target_relative_path}});
  assert.equal(result.status,'UNVERIFIED_SHAPE_REVIEW',target_relative_path);
  assert.equal(result.may_execute,false);
 }
});

test('Windows-illegal characters, C1 controls and superscript device aliases fail closed',()=>{
 for(const target_relative_path of [
  'staged/report?.json','staged/data*.bin','staged/a|b','staged/a<b',
  'staged/a>b','staged/"quoted".txt','staged/COM\u00b9.txt',
  'staged/LPT\u00b2.log','staged/COM\u00b3','staged/del\u007f',
  'staged/c1\u0085'
 ]){
  const result=planCGXHandshake({...base,exchange:{...exchange,target_relative_path}});
  assert.equal(result.reason,'UNSAFE_TRANSFER_TARGET',JSON.stringify(target_relative_path));
  assert.equal(result.status,'DENIED',JSON.stringify(target_relative_path));
 }
 for(const target_relative_path of ['staged/report_v2.json','staged/café.txt']){
  const result=planCGXHandshake({...base,exchange:{...exchange,target_relative_path}});
  assert.equal(result.status,'UNVERIFIED_SHAPE_REVIEW',target_relative_path);
  assert.equal(result.may_execute,false);
 }
});


test('Windows console device endpoints cannot masquerade as transfer files',()=>{
 for(const target_relative_path of [
  'staged/CONIN$', 'staged/CONOUT$', 'staged/conin$.txt',
  'staged/ConOut$.log', 'CONIN$/nested'
 ]){
  const result=planCGXHandshake({...base,exchange:{...exchange,target_relative_path}});
  assert.equal(result.reason,'UNSAFE_TRANSFER_TARGET',target_relative_path);
  assert.equal(result.status,'DENIED',target_relative_path);
 }
 const ordinary=planCGXHandshake({...base,exchange:{...exchange,target_relative_path:'staged/console-input$.txt'}});
 assert.equal(ordinary.status,'UNVERIFIED_SHAPE_REVIEW');
 assert.equal(ordinary.may_execute,false);
});

test('invisible Unicode format controls cannot spoof portable transfer targets',()=>{
 for(const target_relative_path of [
  'staged/a\u200bb.txt', // zero-width space
  'staged/a\u200cb.txt', // zero-width non-joiner
  'staged/a\u200db.txt', // zero-width joiner
  'staged/a\u200eb.txt', // left-to-right mark
  'staged/a\u200fb.txt', // right-to-left mark
  'staged/a\u061cb.txt', // Arabic letter mark
  'staged/a\u2060b.txt', // word joiner
  'staged/a\ufeffb.txt'  // zero-width no-break space
 ]){
  const result=planCGXHandshake({...base,exchange:{...exchange,target_relative_path}});
  assert.equal(result.status,'DENIED',JSON.stringify(target_relative_path));
  assert.equal(result.reason,'UNSAFE_TRANSFER_TARGET',JSON.stringify(target_relative_path));
  assert.equal(result.may_execute,undefined);
 }
 const ordinary=planCGXHandshake({...base,exchange:{...exchange,target_relative_path:'staged/café.txt'}});
 assert.equal(ordinary.status,'UNVERIFIED_SHAPE_REVIEW');
 assert.equal(ordinary.may_execute,false);
});

test('Unicode line separators and unpaired UTF-16 surrogates fail closed in transfer paths',()=>{
 for(const target_relative_path of [
  'staged/a\u2028b.txt', // Unicode line separator, can spoof logs
  'staged/a\u2029b.txt', // Unicode paragraph separator
  'staged/a\ud800b.txt', // unpaired high surrogate
  'staged/a\udc00b.txt'  // unpaired low surrogate
 ]){
  const result=planCGXHandshake({...base,exchange:{...exchange,target_relative_path}});
  assert.equal(result.status,'DENIED',JSON.stringify(target_relative_path));
  assert.equal(result.reason,'UNSAFE_TRANSFER_TARGET',JSON.stringify(target_relative_path));
 }
 const valid=planCGXHandshake({...base,exchange:{...exchange,target_relative_path:'staged/café-2026.txt'}});
 assert.equal(valid.status,'UNVERIFIED_SHAPE_REVIEW');
 assert.equal(valid.may_execute,false);
});

test('transfer chronology after lease expiry or observation time stays held, never executed',()=>{
 const afterExpiry=planCGXHandshake({...base,
  lease:{...base.lease,expires_utc:'2026-10-28T00:00:00Z'},exchange});
 assert.equal(afterExpiry.status,'UNVERIFIED_SHAPE_REVIEW');
 assert.ok(afterExpiry.holds.includes('TRANSFER_CREATED_AFTER_LEASE_EXPIRY'));
 assert.equal(afterExpiry.may_execute,false);
 const future=planCGXHandshake({...base,exchange:{...exchange,created_utc:'2026-10-29T00:00:00Z'}});
 assert.ok(future.holds.includes('FUTURE_TRANSFER_TIMESTAMP'));
 assert.equal(future.receiver_readback_independently_verified,false);
 assert.equal(future.may_execute,false);
});
test('malformed observation time is denied even if lease expiry is malformed',()=>{
 const result=planCGXHandshake({...base,now:'invalid',lease:{...base.lease,expires_utc:'invalid'}});
 assert.equal(result.status,'DENIED');
 assert.equal(result.reason,'INVALID_NOW');
});

test('native execution lease contract is not implicitly the bootstrap handshake lease ABI',()=>{
 const contract=JSON.parse(readFileSync(new URL('../domain_templates/execution_lease_contract.json',import.meta.url),'utf8'));
 assert.equal(contract.schema,'CGX-EXECUTION-LEASE-CONTRACT/0.1');
 for(const field of ['issued_by','subject_agent','valid_from','valid_until','scope','authority_phase_ref'])
  assert.ok(contract.required_fields.includes(field),field);
 const nativeLease={lease_id:'fixture:native',lease_class:'DIGITAL_WRITE',state:'ACTIVE',
  issued_by:'fixture:unverified-issuer',subject_agent:'Neo',
  valid_from:'2026-10-28T00:00:00Z',valid_until:'2026-11-01T00:00:00Z',
  domains:['lightspeed'],execution_depths:['execute'],max_cascade_class:'C1',
  allowed_floors:['Neo'],scope:{object_ids:[base.child.object_id],
   action_classes:['execute'],tool_scopes:['fixture:tool']},revocable:true,
  authority_phase:'PRE_LAUNCH',authority_phase_ref:'fixture:unverified-phase'};
 // The canonical runtime schema has a structured scope and valid_until,
 // whereas the shape planner expects a single scope and expires_utc.
 // Never silently reinterpret the two as an authenticated execution lease.
 const result=planCGXHandshake({...base,lease:nativeLease});
 assert.equal(result.status,'DENIED');
 assert.equal(result.reason,'INCOMPLETE_IDENTITY_OR_LEASE');
});
test('cosmetic lease ABI mapping cannot attest issuer, request scope or replay protection',()=>{
 const claimed={...base.lease,scope:'digital_write',
  signer_ref:{key_id:'fixture:claimed-issuer'},request_nonce:'fixture:replay',
  issued_by:'fixture:claimed-issuer',subject_agent:'Neo',
  valid_until:base.lease.expires_utc,
  tool_scope:'fixture:tool',resource_budget:{max_wall_seconds:1}};
 for(let i=0;i<2;i++){
  const result=planCGXHandshake({...base,lease:claimed});
  assert.equal(result.status,'UNVERIFIED_SHAPE_REVIEW');
  for(const hold of ['ISSUER_ROOT_AUTHORITY_NOT_VERIFIED',
    'REQUEST_BOUND_OBJECT_TOOL_RESOURCE_SCOPE_NOT_VERIFIED',
    'LEASE_NONCE_CONSUMPTION_NOT_VERIFIED'])assert.ok(result.holds.includes(hold));
  assert.equal(result.host_signature_verified,false);
  assert.equal(result.may_execute,false);
  assert.equal(result.db_r_mutated,false);
 }
});


const nativeABIBase={
 sourceSchema:'CGX-EXECUTION-LEASE-CONTRACT/0.1',
 parent:base.parent,child:base.child,now:base.now,
 nativeLease:{lease_id:'fixture:native',lease_class:'COMPUTE_ONLY',
  state:'ACTIVE',revocable:true,issued_by:'fixture:unverified-issuer',
  subject_agent:'Neo',valid_from:'2026-10-27T00:00:00Z',
  valid_until:'2026-11-01T00:00:00Z',domains:['lightspeed'],
  execution_depths:['simulate'],max_cascade_class:'C2',allowed_floors:['Neo','Athene'],
  authority_phase:'PRE_LAUNCH',authority_phase_ref:'fixture:unverified-phase',
  scope:{object_ids:[base.child.object_id],
   tool_scopes:['fixture:solver'],action_classes:['simulate'],
   resource_budgets:{compute_ms:100}}},
 request:{agent_id:'Neo',object_id:base.child.object_id,tool_scope:'fixture:solver',
  domain:'lightspeed',execution_depth:'simulate',action_class:'simulate',
  nonce:'fixture:unconsumed-nonce',cascade_class:'C1',planned_floors:['Neo'],resource_usage:{compute_ms:20}}
};
test('native lease ABI shape review also rejects unsafe child FileSpace names',()=>{
 for(const filespace of ['../escape.cgx','CON.cgx','bad\u200b.cgx']){
  const result=reviewNativeLeaseHandshakeABI({...nativeABIBase,
   child:{...nativeABIBase.child,filespace}});
  assert.equal(result.status,'DENIED',filespace);
  assert.equal(result.reason,'BOOTSTRAP_SHAPE_UNSAFE_CHILD_FILESPACE',filespace);
 }
});
test('native lease ABI adapter never confers operational authority',()=>{
 const r=reviewNativeLeaseHandshakeABI(nativeABIBase);
 assert.equal(r.status,'UNVERIFIED_SHAPE_REVIEW');
 assert.equal(r.schema,'CGX-NATIVE-LEASE-BOOTSTRAP-ABI-REVIEW/0.1');
 assert.equal(r.request_binding_reviewed,true);
 for(const hold of ['SIGNED_LEASE_PROVIDER_REQUIRED',
  'ISSUER_ROOT_AUTHORITY_NOT_VERIFIED','LEASE_NONCE_CONSUMPTION_NOT_VERIFIED',
  'HOST_CLOCK_NOT_ATTESTED','NATIVE_ISSUER_SIGNATURE_AND_REVOCATION_NOT_VERIFIED'])
  assert.ok(r.holds.includes(hold),hold);
 for(const field of ['may_execute','may_publish','host_signature_verified',
  'root_authority_verified','db_r_mutated'])assert.equal(r[field],false,field);
});
test('native lease ABI requires declared authority phase and phase reference',()=>{
 const lease=nativeABIBase.nativeLease;
 for(const changed of [
  {authority_phase:undefined},{authority_phase:'UNRECOGNISED'},
  {authority_phase_ref:undefined},{authority_phase_ref:''},
  {authority_phase_ref:'fixture:spoof'+String.fromCharCode(10)+'ref'}
 ]){
  const result=reviewNativeLeaseHandshakeABI({...nativeABIBase,
   nativeLease:{...lease,...changed}});
  assert.equal(result.status,'DENIED',JSON.stringify(changed));
  assert.equal(result.reason,'NATIVE_LEASE_AUTHORITY_PHASE_UNBOUND');
  assert.equal(result.may_execute,false);
 }
 const shape=reviewNativeLeaseHandshakeABI(nativeABIBase);
 assert.equal(shape.status,'UNVERIFIED_SHAPE_REVIEW');
 assert.ok(shape.holds.includes('NATIVE_ISSUER_SIGNATURE_AND_REVOCATION_NOT_VERIFIED'));
 assert.equal(shape.root_authority_verified,false);
 assert.equal(shape.may_execute,false);
});
test('native lease ABI version, revocation and time negatives fail closed',()=>{
 const check=x=>reviewNativeLeaseHandshakeABI(x).status;
 assert.equal(check({...nativeABIBase,sourceSchema:'CGX-EXECUTION-LEASE-CONTRACT/0.2'}),'DENIED');
 for(const state of ['REVOKED','SUSPENDED','CONSUMED','EXPIRED']){
  assert.equal(check({...nativeABIBase,nativeLease:{...nativeABIBase.nativeLease,state}}),'DENIED');
 }
 assert.equal(check({...nativeABIBase,nativeLease:{...nativeABIBase.nativeLease,revocable:false}}),'DENIED');
 assert.equal(check({...nativeABIBase,now:'2026-11-02T00:00:00Z'}),'DENIED');
 assert.equal(check({...nativeABIBase,now:'2026-10-26T00:00:00Z'}),'DENIED');
 assert.equal(check({...nativeABIBase,now:'2026-02-30T00:00:00Z'}),'DENIED');
});
test('native ABI request object, tool, agent, domain and resource must be explicit subsets',()=>{
 const req=nativeABIBase.request,lease=nativeABIBase.nativeLease;
 for(const changed of [
  {object_id:'fixture:other'}, {tool_scope:'fixture:other'},
  {agent_id:'fixture:other'}, {domain:'eco'},
  {execution_depth:'publish'}, {action_class:'external'},
  {resource_usage:{compute_ms:101}}, {resource_usage:{io_bytes:1}},
  {resource_usage:{}}
 ]){
  const r=reviewNativeLeaseHandshakeABI({...nativeABIBase,request:{...req,...changed}});
  assert.equal(r.status,'DENIED',JSON.stringify(changed));
  assert.equal(r.may_execute,false);
 }
 for(const scope of [{...lease.scope,object_ids:[]},
  {...lease.scope,tool_scopes:[]},{...lease.scope,resource_budgets:{}}]){
  assert.equal(reviewNativeLeaseHandshakeABI({...nativeABIBase,
   nativeLease:{...lease,scope}}).status,'DENIED');
 }
});
test('forged issuer claims and replayed nonce cannot become signed host proof',()=>{
 for(const issued_by of ['fixture:forged','fixture:other-key']){
  const payload={...nativeABIBase,nativeLease:{...nativeABIBase.nativeLease,issued_by}};
  const first=reviewNativeLeaseHandshakeABI(payload);
  const replay=reviewNativeLeaseHandshakeABI(payload);
  for(const r of [first,replay]){
   assert.equal(r.status,'UNVERIFIED_SHAPE_REVIEW');
   assert.equal(r.may_execute,false);
   assert.equal(r.root_authority_verified,false);
   assert.ok(r.holds.includes('REQUEST_NONCE_UNBOUND_TO_NATIVE_LEASE'));
   assert.ok(r.holds.includes('LEASE_NONCE_CONSUMPTION_NOT_VERIFIED'));
  }
 }
});
test('native ABI unsupported effectful class never silently maps to bootstrap',()=>{
 for(const lease_class of ['EXTERNAL_ACTION','PHYSICAL_ACTUATION','unknown']){
  const r=reviewNativeLeaseHandshakeABI({...nativeABIBase,
   nativeLease:{...nativeABIBase.nativeLease,lease_class}});
  assert.equal(r.status,'DENIED');
  assert.equal(r.reason,'NATIVE_LEASE_CLASS_UNSUPPORTED_BY_HANDSHAKE');
 }
});

test('native lease ABI binds explicitly scoped task, project and configuration',()=>{
 const scope={...nativeABIBase.nativeLease.scope,
  task_ids:['fixture:task'],project_ids:['fixture:project'],
  configuration_ids:['fixture:configuration']};
 const lease={...nativeABIBase.nativeLease,scope};
 const request={...nativeABIBase.request,task_id:'fixture:task',
  project_id:'fixture:project',configuration_id:'fixture:configuration'};
 const qualified=reviewNativeLeaseHandshakeABI({...nativeABIBase,nativeLease:lease,request});
 assert.equal(qualified.status,'UNVERIFIED_SHAPE_REVIEW');
 assert.equal(qualified.request_binding_reviewed,true);
 assert.equal(qualified.may_execute,false);
 for(const field of ['task_id','project_id','configuration_id']){
  for(const bad of [undefined,'fixture:other']){
   const altered={...request,[field]:bad};
   const result=reviewNativeLeaseHandshakeABI({...nativeABIBase,nativeLease:lease,request:altered});
   assert.equal(result.status,'DENIED',field+':'+String(bad));
   assert.equal(result.reason,'NATIVE_LEASE_CONTEXT_SCOPE_MISMATCH');
   assert.equal(result.may_execute,false);
  }
 }
});

test('malformed optional native context allowlists fail closed without host authority',()=>{
 for(const field of ['task_ids','project_ids','configuration_ids']){
  for(const invalid of [null,'fixture:task',[17],['fixture:bad\nspoof']]){
   const scope={...nativeABIBase.nativeLease.scope,[field]:invalid};
   const result=reviewNativeLeaseHandshakeABI({...nativeABIBase,
    nativeLease:{...nativeABIBase.nativeLease,scope}});
   assert.equal(result.status,'DENIED',field+':'+JSON.stringify(invalid));
   assert.equal(result.reason,'NATIVE_LEASE_CONTEXT_SCOPE_MISMATCH');
   assert.equal(result.may_execute,false);
  }
 }
});

test('unknown native lease scope axes cannot be silently ignored by the 0.1 ABI',()=>{
 const lease=nativeABIBase.nativeLease;
 for(const extra of [
  {destination_node_ids:['fixture:peer']},
  {rights_scope:'private'},
  {unknown_budget_ceiling:0},
  {['__proto__']:'fixture:spoofed-scope'}
 ]){
  const scope={...lease.scope,...extra};
  const r=reviewNativeLeaseHandshakeABI({...nativeABIBase,
   nativeLease:{...lease,scope}});
  assert.equal(r.status,'DENIED',JSON.stringify(extra));
  assert.equal(r.reason,'NATIVE_LEASE_SCOPE_AXIS_UNMAPPED');
  assert.equal(r.may_execute,false);
  assert.equal(r.host_signature_verified,false);
 }
 const baseline=reviewNativeLeaseHandshakeABI(nativeABIBase);
 assert.equal(baseline.status,'UNVERIFIED_SHAPE_REVIEW');
 assert.equal(baseline.may_execute,false);
});

test('unmapped native geographic or orbital lease scope fails closed',()=>{
 // The contract lists this axis but supplies no typed frame/units/containment
 // ABI. A synthetic matching label is not host spatial authority.
 const spatial=[null,{},'Earth', {frame:'ICRF',body:'Earth'},
  {frame:'J2000',origin:'500@10',region:'all'},[]];
 for(const declared of spatial){
  const scope={...nativeABIBase.nativeLease.scope,
   geographic_or_orbital_scope:declared};
  const result=reviewNativeLeaseHandshakeABI({...nativeABIBase,
   nativeLease:{...nativeABIBase.nativeLease,scope}});
  assert.equal(result.status,'DENIED',JSON.stringify(declared));
  assert.equal(result.reason,'NATIVE_LEASE_SPATIAL_SCOPE_UNMAPPED');
  assert.equal(result.may_execute,false);
 }
 for(const requested of [{frame:'ICRF',body:'Earth'},'Earth',null]){
  const result=reviewNativeLeaseHandshakeABI({...nativeABIBase,
   request:{...nativeABIBase.request,geographic_or_orbital_scope:requested}});
  assert.equal(result.status,'DENIED',JSON.stringify(requested));
  assert.equal(result.reason,'NATIVE_LEASE_SPATIAL_SCOPE_UNMAPPED');
  assert.equal(result.may_execute,false);
 }
 const baseline=reviewNativeLeaseHandshakeABI(nativeABIBase);
 assert.equal(baseline.status,'UNVERIFIED_SHAPE_REVIEW');
 assert.equal(baseline.may_execute,false);
});

test('native ABI rejects malformed or unsupported declared budget ceilings',()=>{
 const baseBudget=nativeABIBase.nativeLease.scope.resource_budgets;
 const make=resource_budgets=>reviewNativeLeaseHandshakeABI({...nativeABIBase,
  nativeLease:{...nativeABIBase.nativeLease,
   scope:{...nativeABIBase.nativeLease.scope,resource_budgets}}});
 for(const bad of [
  {},{...baseBudget,memory_bytes:-1},{...baseBudget,io_bytes:1.5},
  {...baseBudget,ops:'100'},{...baseBudget,unknown_cost:10},
  {...baseBudget,io_bytes:Number.POSITIVE_INFINITY}
 ]){
  const r=make(bad);
  assert.equal(r.status,'DENIED',JSON.stringify(bad));
  assert.equal(r.reason,'NATIVE_RESOURCE_BUDGET_EXCEEDED_OR_UNBOUND');
  assert.equal(r.may_execute,false);
 }
 const inherited=Object.create({compute_ms:100});
 const r=make(inherited);
 assert.equal(r.status,'DENIED');
 assert.equal(r.reason,'NATIVE_RESOURCE_BUDGET_EXCEEDED_OR_UNBOUND');
 const omittedZero=make({...baseBudget,io_bytes:0});
 assert.equal(omittedZero.status,'DENIED');
 assert.equal(omittedZero.reason,'NATIVE_RESOURCE_BUDGET_EXCEEDED_OR_UNBOUND');
 const omittedNonzero=make({...baseBudget,io_bytes:4096});
 assert.equal(omittedNonzero.status,'DENIED');
 assert.equal(omittedNonzero.reason,'NATIVE_RESOURCE_BUDGET_EXCEEDED_OR_UNBOUND');
 const explicit=reviewNativeLeaseHandshakeABI({...nativeABIBase,
  nativeLease:{...nativeABIBase.nativeLease,scope:{...nativeABIBase.nativeLease.scope,
   resource_budgets:{...baseBudget,io_bytes:0}}},
  request:{...nativeABIBase.request,resource_usage:{compute_ms:20,io_bytes:0}}});
 assert.equal(explicit.status,'UNVERIFIED_SHAPE_REVIEW');
 assert.equal(explicit.request_binding_reviewed,true);
 assert.equal(explicit.may_execute,false);
 const over=reviewNativeLeaseHandshakeABI({...nativeABIBase,
  nativeLease:{...nativeABIBase.nativeLease,scope:{...nativeABIBase.nativeLease.scope,
   resource_budgets:{...baseBudget,io_bytes:0}}},
  request:{...nativeABIBase.request,resource_usage:{compute_ms:20,io_bytes:1}}});
 assert.equal(over.status,'DENIED');
 assert.equal(over.reason,'NATIVE_RESOURCE_BUDGET_EXCEEDED_OR_UNBOUND');
});

test('native ABI binds cascade class and planned specialist floors',()=>{
 const valid=reviewNativeLeaseHandshakeABI(nativeABIBase);
 assert.equal(valid.status,'UNVERIFIED_SHAPE_REVIEW');
 assert.equal(valid.may_execute,false);
 const denied=[
  {request:{...nativeABIBase.request,cascade_class:'C3'}},
  {request:{...nativeABIBase.request,cascade_class:'C9'}},
  {request:{...nativeABIBase.request,cascade_class:undefined}},
  {request:{...nativeABIBase.request,planned_floors:['Neo','Other']}},
  {request:{...nativeABIBase.request,planned_floors:[]}},
  {request:{...nativeABIBase.request,planned_floors:undefined}},
  {nativeLease:{...nativeABIBase.nativeLease,max_cascade_class:'C9'}},
  {nativeLease:{...nativeABIBase.nativeLease,allowed_floors:[]}},
  {nativeLease:{...nativeABIBase.nativeLease,allowed_floors:['Neo',17]}},
  {nativeLease:{...nativeABIBase.nativeLease,allowed_floors:undefined}}
 ];
 for(const changed of denied){
  const result=reviewNativeLeaseHandshakeABI({...nativeABIBase,...changed});
  assert.equal(result.status,'DENIED',JSON.stringify(changed));
  assert.equal(result.reason,'NATIVE_LEASE_CASCADE_OR_FLOOR_SCOPE_MISMATCH');
  assert.equal(result.may_execute,false);
 }
 const subset=reviewNativeLeaseHandshakeABI({...nativeABIBase,
  request:{...nativeABIBase.request,cascade_class:'C2',planned_floors:['Neo','Athene']}});
 assert.equal(subset.status,'UNVERIFIED_SHAPE_REVIEW');
 assert.equal(subset.host_signature_verified,false);
 assert.equal(subset.may_execute,false);
});

test('C1 and Unicode identity spoofing fail closed across bootstrap and native lease ABI',()=>{
 const controls=['\\u007f','\\u0085','\\u202e','\\u2028','\\ud800'];
 for(const escaped of controls){
  const control=JSON.parse('"'+escaped+'"');
  const a=planCGXHandshake({...base,lease:{...base.lease,lease_id:'fixture:lease'+control}});
  assert.equal(a.status,'DENIED',escaped);
  assert.equal(a.reason,'INCOMPLETE_IDENTITY_OR_LEASE',escaped);
  const b=planCGXHandshake({...base,exchange:{...exchange,transfer_id:'fixture:transfer'+control}});
  assert.equal(b.status,'DENIED',escaped);
  assert.equal(b.reason,'INVALID_TRANSFER_ENVELOPE',escaped);
  const c=reviewNativeLeaseHandshakeABI({...nativeABIBase,
   request:{...nativeABIBase.request,nonce:'fixture:nonce'+control}});
  assert.equal(c.status,'DENIED',escaped);
  assert.equal(c.reason,'MISSING_REQUEST_BOUND_IDENTITY',escaped);
  const tool='fixture:solver'+control;
  const d=reviewNativeLeaseHandshakeABI({...nativeABIBase,
   nativeLease:{...nativeABIBase.nativeLease,
    scope:{...nativeABIBase.nativeLease.scope,tool_scopes:[tool]}},
   request:{...nativeABIBase.request,tool_scope:tool}});
  assert.equal(d.status,'DENIED',escaped);
  assert.equal(d.reason,'MISSING_REQUEST_BOUND_IDENTITY',escaped);
  assert.equal(d.may_execute,false);
 }
});

test('self-parented FileSpace identity is denied in bootstrap and native ABI review',()=>{
 const parent={...nativeABIBase.parent};
 const child={...nativeABIBase.child,
  object_id:parent.object_id,parent_object_id:parent.object_id};
 const lease={...base.lease,target_object_id:parent.object_id};
 const shape=planCGXHandshake({...base,parent,child,lease});
 assert.equal(shape.status,'DENIED');
 assert.equal(shape.reason,'SELF_PARENT_CHILD_IDENTITY');
 const native=reviewNativeLeaseHandshakeABI({...nativeABIBase,child,
  nativeLease:{...nativeABIBase.nativeLease,
   scope:{...nativeABIBase.nativeLease.scope,object_ids:[parent.object_id]}},
  request:{...nativeABIBase.request,object_id:parent.object_id}});
 assert.equal(native.status,'DENIED');
 assert.equal(native.reason,'BOOTSTRAP_SHAPE_SELF_PARENT_CHILD_IDENTITY');
 assert.equal(native.may_execute,false);
});

test('reject padded and blank identity aliases before non-authorising shape review',()=>{
 for(const invalid of ['',' ','\u00a0',' fixture:root','fixture:root ','\u00a0fixture:root']){
  const r=planCGXHandshake({...base,parent:{...base.parent,object_id:invalid}});
  assert.equal(r.status,'DENIED',JSON.stringify(invalid));
  assert.equal(r.reason,'INCOMPLETE_IDENTITY_OR_LEASE',JSON.stringify(invalid));
 }
 for(const invalid of [' ','fixture:lease ','\u00a0fixture:lease']){
  const r=planCGXHandshake({...base,lease:{...base.lease,lease_id:invalid}});
  assert.equal(r.reason,'INCOMPLETE_IDENTITY_OR_LEASE',JSON.stringify(invalid));
 }
 const valid=planCGXHandshake(base);
 assert.equal(valid.status,'UNVERIFIED_SHAPE_REVIEW');
 assert.equal(valid.may_execute,false);
});


test('unmapped native action verbs never become CCC request-bound by self-declaration',()=>{
 for(const action_class of [
  'deploy','network_send','physical-actuation','delete','mint','custom:plugin.action'
 ]){
  const r=reviewNativeLeaseHandshakeABI({...nativeABIBase,
   nativeLease:{...nativeABIBase.nativeLease,
    scope:{...nativeABIBase.nativeLease.scope,action_classes:[action_class]}},
   request:{...nativeABIBase.request,action_class}});
  assert.equal(r.status,'DENIED',action_class);
  assert.equal(r.reason,'NATIVE_LEASE_ACTION_CLASS_UNMAPPED',action_class);
  assert.equal(r.may_execute,false);
  assert.equal(r.host_signature_verified,false);
 }
 const known=reviewNativeLeaseHandshakeABI(nativeABIBase);
 assert.equal(known.status,'UNVERIFIED_SHAPE_REVIEW');
 assert.equal(known.may_execute,false);
});

test('native lease class/action contradictions are denied before request-bound shape review',()=>{
 for(const [lease_class,action_class] of [
  ['READ_ONLY','simulate'],['READ_ONLY','execute'],['READ_ONLY','digital_write'],
  ['READ_ONLY','publish'],['COMPUTE_ONLY','digital_write'],
  ['COMPUTE_ONLY','publication'],['DIGITAL_WRITE','external_action'],
  ['DIGITAL_WRITE','physical_actuation'],['DIGITAL_WRITE','PuBlIsH']
 ]){
  const r=reviewNativeLeaseHandshakeABI({...nativeABIBase,
   nativeLease:{...nativeABIBase.nativeLease,lease_class,
    scope:{...nativeABIBase.nativeLease.scope,action_classes:[action_class]}},
   request:{...nativeABIBase.request,action_class}});
  assert.equal(r.status,'DENIED',lease_class+':'+action_class);
  assert.equal(r.reason,'NATIVE_LEASE_CLASS_ACTION_MISMATCH');
  assert.equal(r.may_execute,false);
 }
 for(const [lease_class,action_class] of [
  ['READ_ONLY','review'],['COMPUTE_ONLY','simulate'],['DIGITAL_WRITE','digital_write']
 ]){
  const r=reviewNativeLeaseHandshakeABI({...nativeABIBase,
   nativeLease:{...nativeABIBase.nativeLease,lease_class,
    scope:{...nativeABIBase.nativeLease.scope,action_classes:[action_class]}},
   request:{...nativeABIBase.request,action_class}});
  assert.equal(r.status,'UNVERIFIED_SHAPE_REVIEW',lease_class+':'+action_class);
  assert.equal(r.may_execute,false);
 }
});
