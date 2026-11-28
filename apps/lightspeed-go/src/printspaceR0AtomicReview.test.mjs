/** Synthetic Ed25519 test keys are generated in process only. No owner key or
 * actual source-rights, ACL or native DBR evidence is asserted by this suite. */
import {test} from 'vitest';
import {reviewPrintspaceR0WithAtomicLedger as review, inspectPrintspaceR0AtomicReceipt as inspect, R0_LEDGER_ACK_SCHEMA} from './printspaceR0AtomicReview.mjs';
import assert from 'node:assert/strict';
import {generateKeyPairSync,createHash,sign} from 'node:crypto';
import {execFileSync, execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {mkdtempSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
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
const onlyCase=x=>({request:x.request,trust_pins:x.trust_pins,clock_seconds:x.clock_seconds});

const script = new URL('../../../scripts/printspace_r0_sqlite_reference_ledger.py',import.meta.url).pathname;
const runAsync=promisify(execFile);
const dbDir=()=>mkdtempSync(join(tmpdir(),'cgx-r0-ledger-test-'));
const rowFor=x=>({schema:'CGX-PRINTSPACE-R0-NONCE-INSERT-REQUEST/0.1',
 nonce_digest_sha256:x.nonce_digest_sha256,review_receipt_sha256:x.review_receipt_sha256,
 product_facet_sha256:x.product_facet_sha256,plan_sha256:x.plan_sha256,
 expires_at_seconds:x.expires_at_seconds});
function referenceLedger(db){
 return {consumeNonce:async row=>{
  const child=await new Promise((resolve,reject)=>{
   const cp=requireForTestSpawn('python',[script,'consume','--db',db],
    {stdio:['pipe','pipe','pipe']},(error,stdout,stderr)=>error?reject(error):resolve(stdout));
   cp.stdin.end(JSON.stringify(row));
  });
  return JSON.parse(child);
 }};
}
// Callback wrapper is deliberately split from the production module.
function requireForTestSpawn(...args){return spawnCallback(...args)}
function spawnCallback(bin,args,opts,callback){
 const {spawn}=nodeSpawnShim;
 const child=spawn(bin,args,{stdio:['pipe','pipe','pipe']});
 let out='',err='';
 child.stdout.setEncoding('utf8');child.stdout.on('data',v=>{out+=v});
 child.stderr.setEncoding('utf8');child.stderr.on('data',v=>{err+=v});
 child.on('error',callback);
 child.on('close',code=>code===0?callback(null,out,err):callback(new Error('ledger exit '+code+' '+err)));
 return child;
}
const nodeSpawnShim=await import('node:child_process');
function init(db){execFileSync('python',[script,'init','--db',db],{stdio:'pipe'});}
async function inDb(fn){const d=dbDir(),db=join(d,'nonce.sqlite');try{init(db);return await fn(db)}finally{rmSync(d,{force:true,recursive:true})}}

test('atomic reference insert survives new worker and process restart, rejects cross-batch replay',async()=>{
 await inDb(async db=>{
  const x=makeCase('diode','atomic-once');
  const a=await review(onlyCase(x),referenceLedger(db));
  assert.equal(a.state,'REFERENCE_LEDGER_INSERTED_REVIEW_ONLY');
  assert.equal(inspect(a).state,'REVIEW_RECEIPT_SHAPE_ONLY');
  for(const k of ['native_admitted','challenge_consumption_authoritative',
    'host_ledger_independently_authenticated','owner_trust_root_authenticated','machine_authorised'])
     assert.equal(a[k],false,k);
  const second=await review(onlyCase(x),referenceLedger(db));
  assert.equal(second.state,'HOLD');
  assert.equal(second.hold_code,'NONCE_ALREADY_PRESENT_IN_REFERENCE_LEDGER');
  assert.equal(second.reference_replay_conflict,true);
  assert.equal(second.native_admitted,false);
 });
});

test('concurrent worker processes: exactly one global winner for one valid signed nonce',async()=>{
 await inDb(async db=>{
  const x=onlyCase(makeCase('board','concurrent'));const led=referenceLedger(db);
  const outcomes=await Promise.all(Array.from({length:16},()=>review(x,led)));
  assert.equal(outcomes.filter(x=>x.state==='REFERENCE_LEDGER_INSERTED_REVIEW_ONLY').length,1);
  assert.equal(outcomes.filter(x=>x.hold_code==='NONCE_ALREADY_PRESENT_IN_REFERENCE_LEDGER').length,15);
  assert.ok(outcomes.every(x=>x.native_admitted===false));
 });
});

test('cross-product nonce cannot be replayed even when all three role signatures are valid',async()=>{
 await inDb(async db=>{
  const a=onlyCase(makeCase('diode','cross-product'));
  const b=onlyCase(makeCase('phone','cross-product'));
  assert.equal((await review(a,referenceLedger(db))).state,'REFERENCE_LEDGER_INSERTED_REVIEW_ONLY');
  assert.equal((await review(b,referenceLedger(db))).hold_code,'NONCE_ALREADY_PRESENT_IN_REFERENCE_LEDGER');
 });
});

test('distinct challenges across concurrent worker invocations are all recorded',async()=>{
 await inDb(async db=>{
  const list=Array.from({length:12},(_,i)=>onlyCase(makeCase(['diode','board','phone'][i%3],String(i))));
  const outcomes=await Promise.all(list.map(x=>review(x,referenceLedger(db))));
  assert.equal(outcomes.filter(x=>x.state==='REFERENCE_LEDGER_INSERTED_REVIEW_ONLY').length,12);
  assert.equal(outcomes.filter(x=>x.state==='HOLD').length,0);
 });
});

test('invalid signature never consumes challenge; re-signed valid case then consumes',async()=>{
 await inDb(async db=>{
  const x=makeCase('diode','invalid-then-valid');
  const correct=onlyCase(x);
  const invalid=structuredClone(correct);
  invalid.request.role_receipts[0].signature_b64='A'.repeat(88);
  const first=await review(invalid,referenceLedger(db));
  assert.equal(first.state,'HOLD');
  assert.equal((await review(correct,referenceLedger(db))).state,'REFERENCE_LEDGER_INSERTED_REVIEW_ONLY');
  assert.equal((await review(correct,referenceLedger(db))).state,'HOLD');
 });
});

test('unavailable, missing and malformed host ledger must HOLD',async()=>{
 const x=onlyCase(makeCase('diode','unavailable'));
 assert.equal((await review(x,null)).hold_code,'HOST_ATOMIC_LEDGER_REQUIRED');
 assert.equal((await review(x,{consumeNonce:async()=>{throw new Error('offline')}})).hold_code,'SIGNED_REVIEW_OR_LEDGER_UNAVAILABLE');
 assert.equal((await review(x,{consumeNonce:async()=>({schema:R0_LEDGER_ACK_SCHEMA,state:'INSERTED',nonce_digest_sha256:'0'.repeat(64),review_receipt_sha256:'0'.repeat(64)})})).hold_code,'UNTRUSTED_LEDGER_ACK');
 assert.equal((await review(x,{consumeNonce:async()=>({schema:R0_LEDGER_ACK_SCHEMA,state:'INSERTED',nonce_digest_sha256:'0'.repeat(64),review_receipt_sha256:'0'.repeat(64),machine_authorised:true})})).hold_code,'UNTRUSTED_LEDGER_ACK');
});

test('unsigned and expired source data cannot reach persistent nonce adapter',async()=>{
 const x=onlyCase(makeCase('diode','too-late'));let called=0;
 const led={consumeNonce:async()=>{called++;throw Error('should not be called')}};
 x.clock_seconds=now+500;
 const out=await review(x,led);
 assert.equal(out.state,'HOLD');assert.equal(called,0);
});

test('host acknowledgement is not independent owner trust even if host lies about persistence',async()=>{
 const x=onlyCase(makeCase('diode','fake-ledger'));
 const fake={consumeNonce:async row=>({schema:R0_LEDGER_ACK_SCHEMA,state:'INSERTED',
  nonce_digest_sha256:row.nonce_digest_sha256,review_receipt_sha256:row.review_receipt_sha256})};
 const out=await review(x,fake);
 assert.equal(out.state,'REFERENCE_LEDGER_INSERTED_REVIEW_ONLY');
 assert.equal(out.host_ledger_independently_authenticated,false);
 assert.equal(out.challenge_consumption_authoritative,false);
 assert.equal(out.native_admitted,false);
 assert.equal(out.machine_authorised,false);
});

test('SQLite reference CLI rejects non-digest values and fails rather than fall back',async()=>{
 await inDb(async db=>{
  const p=rowFor({nonce_digest_sha256:'X'.repeat(64),review_receipt_sha256:'a'.repeat(64),
   product_facet_sha256:'b'.repeat(64),plan_sha256:'c'.repeat(64),expires_at_seconds:now+10});
  const {spawnSync}=nodeSpawnShim;
  const s=spawnSync('python',[script,'consume','--db',db],{input:JSON.stringify(p),encoding:'utf8'});
  assert.notEqual(s.status,0);
  assert.equal(s.stdout.trim(),'');
 });
});
