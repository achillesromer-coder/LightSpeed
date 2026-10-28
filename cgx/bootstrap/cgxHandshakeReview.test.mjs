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
test('source segment above 60 MiB is held',()=>assert.ok(
 planCGXHandshake({...base,exchange:{...exchange,size_bytes:70*1024*1024}}).holds.includes('BOUNDED_TRANSFER_SEGMENT_REQUIRED')));
test('missing signer reference held',()=>assert.ok(
 planCGXHandshake({...base,lease:{...base.lease,signer_ref:null}}).holds.includes('SIGNED_LEASE_PROVIDER_REQUIRED')));
test('no operational or release authority granted by planner',()=>{
 const r=planCGXHandshake({...base,exchange});
 for (const prop of ['host_signature_verified','db_r_mutated','node_transfer_executed','may_execute','may_publish'])assert.equal(r[prop],false);
});
