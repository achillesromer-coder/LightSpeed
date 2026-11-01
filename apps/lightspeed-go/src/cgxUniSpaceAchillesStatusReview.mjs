/** UniSpace private-operator status review adapter, SOURCE ONLY.
 * One unminted Achilles/EMASSC task from PR #217. Not a browser route,
 * session verifier, queue client, dispatcher, DBR resolver, or public asset.
 * The caller's HTTP observations are never elevated to issuer/ACL proof.
 */
export const ACHILLES_STATUS_SCHEMA='UNISPACE-ACHILLES-STATUS-REVIEW/0.1';
export const ACHILLES_PROFILE_BLOB='932742c2a9ba8e6c0caddc5819c44b8a759a2ea3';
export const ACHILLES_TASK='ACHILLES-UNISPACE-DELIVERY-REVIEW-001';
const obj=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const exact=(x,allowed)=>obj(x)&&Object.keys(x).every(k=>allowed.includes(k))&&allowed.every(k=>Object.hasOwn(x,k));
const deny=code=>Object.freeze({schema:ACHILLES_STATUS_SCHEMA,state:'HOLD',hold_code:code,bridge_state:'UNVERIFIED',consumer_state:'UNVERIFIED',dispatch_ready:false,owner_r3_verified:false,native_admitted:false,release_accepted:false,canonical_mutation:false});
export function projectAchillesStatusReview(input){
 if(!exact(input,['selection','bridge','consumer']))return deny('INVALID_ENVELOPE');
 const {selection:s,bridge:b,consumer:c}=input;
 if(!exact(s,['parent_filespace','filespace','task_id','profile_blob_sha','identity_stage'])||
 s.parent_filespace!=='Cognigrex.cgx'||s.filespace!=='EMASSC.cgx'||
 s.task_id!==ACHILLES_TASK||s.profile_blob_sha!==ACHILLES_PROFILE_BLOB||
 s.identity_stage!=='SOURCE_ONLY_UNMINTED')return deny('PROFILE_OR_CHILD_MISMATCH');
 if(!exact(b,['status_code','observation'])||!Number.isInteger(b.status_code)||
 b.status_code<0||b.status_code>599||b.observation!=='CALLER_REPORTED_LOCAL_HTTP')return deny('INVALID_BRIDGE_OBSERVATION');
 if(!exact(c,['heartbeat','pid_binding'])||
 !['STALE','FRESH','UNKNOWN'].includes(c.heartbeat)||
 !['REUSED','MATCHED','UNKNOWN'].includes(c.pid_binding))return deny('INVALID_CONSUMER_OBSERVATION');
 const bridge=b.status_code===200?'BRIDGE_REACHABLE_REPORTED':'BRIDGE_UNVERIFIED';
 const consumer=c.heartbeat==='STALE'||c.pid_binding==='REUSED'
   ?'CONSUMER_HELD_STALE_OR_PID_REUSED'
   :c.heartbeat==='FRESH'&&c.pid_binding==='MATCHED'
     ?'CONSUMER_CANDIDATE_UNVERIFIED':'CONSUMER_UNVERIFIED';
 // No caller-supplied booleans or hashes may grant a session, lease, DBR,
 // queue dispatch, private R3 hydration or scientific authority.
 return Object.freeze({
  schema:ACHILLES_STATUS_SCHEMA,state:'SOURCE_ONLY_REVIEW',
  parent_filespace:'Cognigrex.cgx',filespace:'EMASSC.cgx',
  candidate_task_id:ACHILLES_TASK,source_profile_blob_sha:ACHILLES_PROFILE_BLOB,
  identity_stage:'SOURCE_ONLY_UNMINTED',evidence_class:'SOURCE_ONLY',
  bridge_state:bridge,consumer_state:consumer,
  gate:'HOLD_154_158_161_S92_S97',
  next_step:'TRUSTED_HOST_ISSUER_ACL_REVOCATION_LEASE_AND_CONSUMER_RECEIPT_READBACK',
  hydration:'H0_PUBLIC_SAFE_PROFILE_METADATA_ONLY',private_source_exposed:false,
  dispatch_ready:false,owner_r3_verified:false,native_admitted:false,
  host_verified:false,release_accepted:false,canonical_mutation:false
 });
}
