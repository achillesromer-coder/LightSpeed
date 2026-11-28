/** Synthetic Ed25519 test keys are generated in process only. No owner key or
 * actual source-rights, ACL or native DBR evidence is asserted by this suite. */
import {test} from 'vitest';
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
const run=(x,t=now)=>verify(x.request,x.trust,t);
const hold=(x,code,t=now)=>assert.equal(run(x,t).hold_code,code,JSON.stringify(run(x,t)));

test('three independent valid synthetic Ed25519 roles validate R0 only for each product',()=>{
 for(const product of ['diode','board','phone']){
  const x=construct(product);const r=run(x);
  assert.equal(r.state,'THREE_ROLE_ED25519_SIGNATURES_VALID_REVIEW_ONLY',JSON.stringify(r));
  assert.equal(r.product_id,product);
  assert.equal(r.signatures_verified,true);
  assert.equal(r.proof_roles.length,3);
  assert.equal(r.review_receipt_sha256.length,64);
  for(const k of ['trust_root_origin_authenticated','real_source_readback_authenticated',
   'real_rights_independently_accepted','host_session_independently_authenticated',
   'challenge_consumption_recorded','native_admitted','private_hydration_authorised',
   'native_dbr_written','machine_authorised','mint_authorised','commercial_release_authorised'])
   assert.equal(r[k],false,k);
  assert.equal(r.source_bytes_hydrated,0);
  assert.equal(JSON.stringify(r).includes('BEGIN PUBLIC KEY'),false);
 }
});

test('deterministic review receipt despite role receipt permutation',()=>{
 const x=construct();const v=run(x);
 x.request.role_receipts.reverse();
 assert.deepEqual(run(x),v);
});

test('missing owner-pinned keys, private-key input, reused role key and revoked keys denied',()=>{
 const x=construct();hold({...x,trust:null},'UNTRUSTED_ROOT_PIN_SET');
 x.trust.key_roles.host.public_key_pem=x.keys.host.export({format:'pem',type:'pkcs8'}).toString();
 hold(x,'UNTRUSTED_ROOT_PIN_SET');
 const y=construct();y.trust.key_roles.rights={...y.trust.key_roles.registry};
 hold(y,'UNTRUSTED_ROOT_PIN_SET');
 const z=construct();z.trust.key_roles.registry.revoked=true;
 hold(z,'UNTRUSTED_ROOT_PIN_SET');
});

test('signed statement mutation or wrong cryptographic key cannot verify',()=>{
 const x=construct();x.request.role_receipts[0].statement.object_id='OTHER';
 hold(x,'SIGNATURE_STATEMENT_CONTEXT_OR_RIGHTS_DRIFT');
 const y=construct();y.request.role_receipts[1].signature_b64=y.request.role_receipts[0].signature_b64;
 hold(y,'ED25519_SIGNATURE_INVALID');
 const z=construct();z.request.role_receipts[2].signature_b64=z.request.role_receipts[2].signature_b64.slice(0,-3)+'AAA';
 hold(z,'ED25519_SIGNATURE_INVALID');
});

test('missing or duplicated roles, cross-role signatures and unknown identity denied',()=>{
 const x=construct();x.request.role_receipts.pop();hold(x,'THREE_ROLE_RECEIPTS_REQUIRED');
 const y=construct();y.request.role_receipts[1].role='host';hold(y,'DUPLICATE_OR_UNKNOWN_ATTESTOR_ROLE');
 const z=construct();z.request.role_receipts[2].key_id='wrong-key';hold(z,'DUPLICATE_OR_UNKNOWN_ATTESTOR_ROLE');
});

test('expiry, clock rollback, stale challenge and arbitrary nonce replay denied',()=>{
 const x=construct();hold(x,'UNBOUND_STALE_OR_FUTURE_CHALLENGE',now+70);
 const y=construct();hold(y,'UNBOUND_STALE_OR_FUTURE_CHALLENGE',now-120);
 const z=construct();z.request.challenge.nonce='c'.repeat(64);
 hold(z,'SIGNATURE_STATEMENT_CONTEXT_OR_RIGHTS_DRIFT');
});

test('revocation epoch and proof revocation guard against replay',()=>{
 const x=construct();x.trust.revocation_epoch=8;hold(x,'SIGNATURE_STATEMENT_CONTEXT_OR_RIGHTS_DRIFT');
 const y=construct();y.request.role_receipts[1].statement.assertions.revoked=true;
 hold(y,'SIGNATURE_STATEMENT_CONTEXT_OR_RIGHTS_DRIFT');
 const z=construct();z.request.role_receipts[0].statement.assertions.identity_matches=2;
 hold(z,'SIGNATURE_STATEMENT_CONTEXT_OR_RIGHTS_DRIFT');
});

test('rights escalation, native mutation and mismatched FileSpace all fail closed',()=>{
 const x=construct();x.request.role_receipts[2].statement.assertions.rights_scope='MINT_AND_MACHINE';
 hold(x,'SIGNATURE_STATEMENT_CONTEXT_OR_RIGHTS_DRIFT');
 const y=construct();y.request.role_receipts[0].statement.assertions.dbr_mutation=true;
 hold(y,'SIGNATURE_STATEMENT_CONTEXT_OR_RIGHTS_DRIFT');
 const z=construct();z.request.role_receipts[2].statement.filespace='Eco.cgx';
 hold(z,'SIGNATURE_STATEMENT_CONTEXT_OR_RIGHTS_DRIFT');
});

test('untrusted source reviews, synthetic scope drift and secret fields fail closed',()=>{
 const x=construct();x.request.source_review_input.plan.r0_cases[0].candidate_object_id='FORGED';
 hold(x,'EXISTING_UNISPACE_SOURCE_REVIEW_HOLD');
 const y=construct();y.request.role_receipts[0].statement.source_bytes='PRIVATE';
 hold(y,'MALFORMED_PRIVATE_OR_UNBOUND_ATTESTATION');
 const z=construct();z.request.source_review_input.client_permissions.revoked=true;
 hold(z,'EXISTING_UNISPACE_SOURCE_REVIEW_HOLD');
});

test('invalid clocks and unauthorized schema cannot create any admission',()=>{
 const x=construct();hold(x,'HOST_CLOCK_REQUIRED',NaN);
 const y=construct();y.request.role_receipts[0].statement.extra_authority=true;
 hold(y,'DUPLICATE_OR_UNKNOWN_ATTESTOR_ROLE');
 const z=construct();z.trust.keys='NEW_ROOT';
 hold(z,'UNTRUSTED_ROOT_PIN_SET');
});

test('noncanonical own keys are rejected before statement or review verification',()=>{
  for(const value of [{},null,7]){
    const x=construct();
    const statement=x.request.role_receipts[0].statement;
    Object.defineProperty(statement.assertions,'__proto__',{value,enumerable:true});
    assert.throws(()=>canonicalR0StatementBytes(statement));
    assert.equal(run(x).state,'HOLD');
  }
});
