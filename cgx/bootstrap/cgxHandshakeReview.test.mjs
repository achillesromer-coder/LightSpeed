import test from 'node:test';
import assert from 'node:assert/strict';
import {planCGXHandshake} from './cgxHandshakeReview.mjs';
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
