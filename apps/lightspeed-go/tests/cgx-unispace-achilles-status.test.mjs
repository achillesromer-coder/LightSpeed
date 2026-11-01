import {test} from 'vitest';
import assert from 'node:assert/strict';
import {projectAchillesStatusReview as review,ACHILLES_PROFILE_BLOB,ACHILLES_TASK} from '../src/cgxUniSpaceAchillesStatusReview.mjs';
const sample=()=>({
 selection:{parent_filespace:'Cognigrex.cgx',filespace:'EMASSC.cgx',task_id:ACHILLES_TASK,profile_blob_sha:ACHILLES_PROFILE_BLOB,identity_stage:'SOURCE_ONLY_UNMINTED'},
 bridge:{status_code:200,observation:'CALLER_REPORTED_LOCAL_HTTP'},
 consumer:{heartbeat:'STALE',pid_binding:'REUSED'}
});
test('HTTP 200 and reused PID are distinct and never execute-ready',()=>{
 const x=review(sample());
 assert.equal(x.bridge_state,'BRIDGE_REACHABLE_REPORTED');
 assert.equal(x.consumer_state,'CONSUMER_HELD_STALE_OR_PID_REUSED');
 assert.equal(x.dispatch_ready,false);
 assert.equal(x.owner_r3_verified,false);
 assert.equal(x.native_admitted,false);
});
test('fresh matching consumer still cannot grant native/owner authority',()=>{
 const a=sample();a.consumer={heartbeat:'FRESH',pid_binding:'MATCHED'};
 const x=review(a);assert.equal(x.consumer_state,'CONSUMER_CANDIDATE_UNVERIFIED');
 assert.equal(x.dispatch_ready,false);assert.equal(x.host_verified,false);
});
test('wrong child and forged profile SHA fail closed',()=>{
 const a=sample();a.selection.filespace='Romer.cgx';
 assert.equal(review(a).hold_code,'PROFILE_OR_CHILD_MISMATCH');
 const b=sample();b.selection.profile_blob_sha='0'.repeat(40);
 assert.equal(review(b).hold_code,'PROFILE_OR_CHILD_MISMATCH');
});
test('private source, credentials, ACL and execution flags are not accepted',()=>{
 for(const field of ['source_path','raw_text','token','owner_acl_verified','dispatch_ready']){
  const a=sample();a[field]='private';assert.equal(review(a).state,'HOLD');
 }
 const b=sample();b.bridge.session='forged';
 assert.equal(review(b).hold_code,'INVALID_BRIDGE_OBSERVATION');
});
test('invalid consumer observations cannot masquerade as health',()=>{
 const a=sample();a.consumer.pid_binding='VERIFIED';
 assert.equal(review(a).hold_code,'INVALID_CONSUMER_OBSERVATION');
 const b=sample();b.bridge.status_code=401;
 assert.equal(review(b).bridge_state,'BRIDGE_UNVERIFIED');
});
test('read-only projection preserves input and excludes raw private data',()=>{
 const a=sample(),before=JSON.stringify(a),out=review(a);
 assert.equal(JSON.stringify(a),before);
 assert.equal(out.private_source_exposed,false);
 assert.equal(out.identity_stage,'SOURCE_ONLY_UNMINTED');
 assert.equal(JSON.stringify(out).includes('source_path'),false);
});
