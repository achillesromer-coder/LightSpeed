/** Synthetic Ed25519 test keys are generated in process only. No owner key or
 * actual source-rights, ACL or native DBR evidence is asserted by this suite. */
import {test} from 'vitest';
import {reviewPrintspaceR0Batch as batchReview, replayPrintspaceR0Batch as back, SCHEMA, MAX_CASES} from './printspaceR0BatchSweep.mjs';
import assert from 'node:assert/strict';
import {generateKeyPairSync,createHash,sign} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {reviewPrintspaceHostR0} from './printspaceCgxHostR0Bridge.mjs';
import {
  R0_SIGNED_STATEMENT_SCHEMA,R0_TRUST_PINS_SCHEMA,
  canonicalR0StatementBytes,verifyPrintspaceR0SignedEvidence as verify,
} from './printspaceR0SignedEvidence.mjs';

const SRC=`
import json
from cgx.manufacturing.printspace_cgx import build_bundle
from cgx.manufacturing.virtual_factory import load_catalogue
from cgx.manufacturing.printspace_host_preflight import prepare_r0_host_review
c=load_catalogue();b=build_bundle(c)
rows=[{'product_id':p,'candidate_object_id':'PS-'+p.upper()+'-CANDIDATE-001',
       'twin_id':p+'-candidate','lineage_git_blob_sha':'1'*40,
       'registry_git_blob_sha':'2'*40} for p in ('diode','board','phone')]
print(json.dumps(prepare_r0_host_review(b,c,rows),sort_keys=True))
`;
const plan=JSON.parse(execFileSync('python',['-c',SRC],{
  cwd:new URL('../../../',import.meta.url).pathname,encoding:'utf8',
}));
const roles=['host','registry','rights'];
const now=1800000000;
const freezeClone=x=>structuredClone(x);
function construct(product='diode'){
 const item=plan.r0_cases.find(x=>x.product_id===product);
 const id=item.candidate_object_id,twin=item.twin_id_candidate;
 const input={plan:freezeClone(plan),product_id:product,
  context_response:{execution_performed:false,external_action_performed:false,
   canonical_mutation:false,authority_transfer:false,
   object_context:{schema:'CGX-OBJECT-CONTEXT/0.1',automatic_execution:false,
    canonical_mutation:false,resolved_twin_id:twin,semantic_domain:'romer',
    domain_identity:{semantic_object_id:'cgx:domain:romer',filespace:'Romer.cgx'},
    semantic_resolution:{state:'exact_semantic_object',semantic_object_id:id}}},
  lineage_candidates:[{semantic_object_id:id,twin_id:twin}],
  load_contract:{schema:'LOAD-ALEXANDRIA-ACTIVATION/0.1',
   status:'SOURCE_REVIEW_NOT_ADMITTED',alias:'LOAD.cgx',
   parent_filespace:'Cognigrex.cgx',canonical_object_id:null,
   accepted_parent_object_id:null,canonical_mutation:false,
   network_fetch:'DENY_UNTIL_HOST_AUTHORIZED'},
  client_permissions:{mode:'review_only',revoked:false,
   allowed_object_ids:[id],allowed_filespaces:['Romer.cgx']},
  source_status:{collision:'no_conflict_reported',rights:'cleared_for_review',
   evidence_class:'scientific'}};
 const pins={plan_sha256:plan.plan_sha256,bundle_sha256:item.bundle_sha256,
  product_facet_sha256:item.product_facet_sha256};
 const sourceReview=reviewPrintspaceHostR0(input,pins);
 assert.equal(sourceReview.state,'PLAN_ONLY_NOT_HYDRATED',JSON.stringify(sourceReview));
 const trust={schema:R0_TRUST_PINS_SCHEMA,key_roles:{},revocation_epoch:7};
 const keys={};
 for(const role of roles){
  const {publicKey,privateKey}=generateKeyPairSync('ed25519');
  const pem=publicKey.export({format:'pem',type:'spki'}).toString();
  const fingerprint=createHash('sha256').update(publicKey.export({type:'spki',format:'der'})).digest('hex');
  trust.key_roles[role]={key_id:'synthetic-'+role+'-key-001',public_key_pem:pem,
   spki_sha256:fingerprint,revoked:false};
  keys[role]=privateKey;
 }
 const challenge={nonce:'a'.repeat(64),issued_at_seconds:now-15,expires_at_seconds:now+60};
 const statements=roles.map(role=>{
  const assertions=role==='registry'?
   {identity_matches:1,collision_state:'NO_COLLISION_IN_ATTESTOR_SNAPSHOT',
    lineage_state:'EXACT_ID_AND_TWIN_IN_ATTESTOR_SNAPSHOT',revoked:false,
    source_snapshot_sha256:'sha256:'+'b'.repeat(64)}:
   role==='rights'?{rights_scope:'R0_REVIEW_ONLY',licence_ref:'SYNTHETIC-RIGHTS-REF',
    revoked:false,rights_scope_state:'REVIEW_PERMISSION_ASSERTED_BY_SIGNER'}:
   {acl_scope:'R0_REVIEW_ONLY',session_review_state:'REVIEW_CONTEXT_ASSERTED_BY_SIGNER',
    revoked:false,dbr_mutation:false};
  return {schema:R0_SIGNED_STATEMENT_SCHEMA,role,scope:'R0_REVIEW_ONLY',
   request_nonce:challenge.nonce,
   issued_at_seconds:challenge.issued_at_seconds,
   expires_at_seconds:challenge.expires_at_seconds,
   revocation_epoch:trust.revocation_epoch,
   plan_sha256:sourceReview.plan_sha256,
   product_facet_sha256:sourceReview.product_facet_sha256,
   bundle_sha256:sourceReview.bundle_sha256,
   object_id:sourceReview.object_id,twin_id:twin,filespace:'Romer.cgx',
   lineage_git_blob_sha:sourceReview.source_lineage_sha_candidate,
   registry_git_blob_sha:sourceReview.source_registry_sha_candidate,
   evidence_ref:'SYNTHETIC-'+role+'-'+product,
   assertions};
 });
 const receipts=roles.map((role,i)=>({role,
  key_id:trust.key_roles[role].key_id,statement:statements[i],
  signature_b64:sign(null,canonicalR0StatementBytes(statements[i]),keys[role]).toString('base64')}));
 const request={source_review_input:input,source_review_pins:pins,challenge,role_receipts:receipts};
 return {request,trust,keys};
}

function makeCase(product='diode',label='one'){
 const x=construct(product);
 const nonce=createHash('sha256').update('R0-batch-'+label).digest('hex');
 x.request.challenge.nonce=nonce;
 for(const row of x.request.role_receipts){
  row.statement.request_nonce=nonce;
  row.signature_b64=sign(null,canonicalR0StatementBytes(row.statement),x.keys[row.role]).toString('base64');
 }
 return {request:x.request,trust_pins:x.trust,clock_seconds:now,private_keys_for_tests:x.keys};
}
const only=x=>({request:x.request,trust_pins:x.trust_pins,clock_seconds:x.clock_seconds});
const pack=(cases,hints=[])=>({schema:SCHEMA,cases:cases.map(only),known_consumed_nonce_sha256:hints});



test('three fresh challenges all review digitally and preserve physical safety gates',()=>{
 const inputs=['diode','board','phone'].map(p=>makeCase(p,p));
 const out=batchReview(pack(inputs));
 assert.equal(out.state,'BATCH_DIGITAL_REVIEW_ONLY');
 assert.equal(out.review_valid_count,3);
 assert.equal(out.invalid_count,0);
 assert.equal(out.within_batch_replay_count,0);
 assert.equal(new Set(out.results.map(r=>r.nonce_digest_sha256)).size,3);
 for(const k of ['native_admitted','challenge_consumption_recorded','trust_root_origin_authenticated',
 'machine_authorised','native_dbr_written','mint_authorised','commercial_release_authorised',
 'host_challenge_ledger_persisted','across_batch_replay_prevented'])assert.equal(out[k],false,k);
 assert.equal(back(out,pack(inputs)).state,'PASS_DIGITAL_ONLY');
 assert.equal(JSON.stringify(out).includes('BEGIN PUBLIC KEY'),false);
});

test('same valid challenge twice is denied without verifying it twice',()=>{
 const a=makeCase('diode','same');const input=pack([a,a,a]);
 const r=batchReview(input);
 assert.deepEqual([r.review_valid_count,r.within_batch_replay_count,r.invalid_count],[1,2,0]);
 assert.deepEqual(r.results.map(x=>x.state),['SIGNATURES_VALID_REVIEW_ONLY','HOLD','HOLD']);
 assert.equal(r.results[1].hold_code,'WITHIN_BATCH_NONCE_REPLAY');
 assert.deepEqual(batchReview(input),r);
});

test('same nonce is denied even when product changes (global in-batch scope)',()=>{
 const a=makeCase('diode','reuse');const b=makeCase('phone','reuse');
 const r=batchReview(pack([a,b]));
 assert.equal(r.review_valid_count,1);
 assert.equal(r.within_batch_replay_count,1);
});

test('a prior negative-only nonce hint blocks review but is NOT an authenticated ledger',()=>{
 const a=makeCase('board','historical');
 const baseline=batchReview(pack([a]));
 const hint=baseline.results[0].nonce_digest_sha256;
 const r=batchReview(pack([a],[hint]));
 assert.equal(r.review_valid_count,0);
 assert.equal(r.consumed_hint_replay_count,1);
 assert.equal(r.results[0].hold_code,'UNTRUSTED_HISTORY_REPLAY_DENY');
 assert.equal(r.historical_hints_independently_authenticated,false);
 assert.equal(r.across_batch_replay_prevented,false);
});

test('tampered signature is not counted as consumed; valid following same nonce still reviews',()=>{
 const first=makeCase('diode','tamper');const clean=structuredClone(only(first));
 first.request.role_receipts[0].signature_b64='A'.repeat(88);
 const r=batchReview({schema:SCHEMA,cases:[only(first),clean],known_consumed_nonce_sha256:[]});
 assert.equal(r.invalid_count,1);
 assert.equal(r.review_valid_count,1);
 assert.equal(r.within_batch_replay_count,0);
 assert.equal(r.results[0].state,'HOLD');
});

test('individual malformed entries fail but do not stop other known-good cases',()=>{
 const a=makeCase('diode','wellformed');
 const caseList=[null,{},only(a),{...only(a),gcode:'G0 X1'}, {request:a.request,trust_pins:a.trust,clock_seconds:NaN}];
 const r=batchReview({schema:SCHEMA,cases:caseList,known_consumed_nonce_sha256:[]});
 assert.equal(r.review_valid_count,1);
 assert.equal(r.invalid_count,4);
 assert.equal(r.case_count,5);
 assert.equal(r.machine_authorised,false);
});

test('missing schema, unsupported hints, upper bound and additional fields are denied',()=>{
 const valid=only(makeCase('diode','test'));
 const input={schema:SCHEMA,cases:[valid],known_consumed_nonce_sha256:[]};
 assert.equal(batchReview({...input,authority:true}).state,'HOLD');
 assert.equal(batchReview({...input,schema:'FORGED'}).state,'HOLD');
 assert.equal(batchReview({...input,cases:[]}).hold_code,'BATCH_SIZE_EXCEEDED');
 assert.equal(batchReview({...input,cases:Array(MAX_CASES+1).fill(valid)}).hold_code,'BATCH_SIZE_EXCEEDED');
 assert.equal(batchReview({...input,known_consumed_nonce_sha256:['0'.repeat(64),'0'.repeat(64)]}).state,'HOLD');
 assert.equal(batchReview({...input,known_consumed_nonce_sha256:['NOT_A_SHA']}).state,'HOLD');
 assert.equal(batchReview(null).state,'HOLD');
});

test('batch back-down rejects reordering, tamper and false native approval',()=>{
 const inputs=[makeCase('diode','a'),makeCase('board','b')];
 const a=pack(inputs),r=batchReview(a);
 assert.equal(back(r,a).state,'PASS_DIGITAL_ONLY');
 assert.equal(back(r,{...a,cases:a.cases.slice().reverse()}).state,'HOLD');
 assert.equal(back({...r,native_admitted:true},a).state,'HOLD');
 assert.equal(back({...r,receipt_sha256:'0'.repeat(64)},a).state,'HOLD');
});

test('256-case deterministic negative/positive cross-sweep stays bounded',()=>{
 const base=makeCase('diode','seed');
 const cases=[];
 for(let i=0;i<256;i++){
  const copy=structuredClone(only(base));
  const uniqueNonce=createHash('sha256').update('cross-sweep:'+i).digest('hex');
  copy.request.challenge.nonce=uniqueNonce;
  for(const entry of copy.request.role_receipts){
   entry.statement.request_nonce=uniqueNonce;
   entry.signature_b64=sign(null,canonicalR0StatementBytes(entry.statement),base.private_keys_for_tests[entry.role]).toString('base64');
  }
  if(i%4===1)copy.request.role_receipts[0].statement.object_id='FORGED';
  else if(i%4===2)copy.trust_pins={...copy.trust_pins,revocation_epoch:copy.trust_pins.revocation_epoch+1};
  else if(i%4===3)copy.clock_seconds=now+600;
  cases.push(copy);
 }
 const start=performance.now();const result=batchReview({schema:SCHEMA,cases,known_consumed_nonce_sha256:[]});
 const elapsed=performance.now()-start;
 assert.equal(result.case_count,256);
 assert.equal(result.review_valid_count,64);
 assert.equal(result.invalid_count,192);
 assert.equal(result.within_batch_replay_count,0);
 assert.equal(result.native_admitted,false);
 assert.ok(elapsed<30_000,'CPU-only CI safety bound, not an operational throughput SLA');
 assert.equal(back(result,{schema:SCHEMA,cases,known_consumed_nonce_sha256:[]}).state,'PASS_DIGITAL_ONLY');
});

test('bulk repeated 512-case scenario is rejected after the first valid nonce',()=>{
 const valid=only(makeCase('phone','bulk'));
 const input={schema:SCHEMA,cases:Array.from({length:512},()=>valid),known_consumed_nonce_sha256:[]};
 const output=batchReview(input);
 assert.equal(output.review_valid_count,1);
 assert.equal(output.within_batch_replay_count,511);
 assert.equal(output.case_count,512);
 assert.equal(output.challenge_consumption_recorded,false);
});