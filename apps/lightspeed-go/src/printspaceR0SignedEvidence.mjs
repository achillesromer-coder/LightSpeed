/**
 * CGX PrintSpace R0 Ed25519 proof verifier over EXISTING UniSpace review.
 * Pure and read-only: no network, private keys, source hydration, DBR, mint,
 * native host ACL approval, tool control, or claims that supplied key pins
 * themselves came from the independent owner-trust registry.
 */
import {createHash, createPublicKey, verify as verifySignature} from 'node:crypto';
import {reviewPrintspaceHostR0} from './printspaceCgxHostR0Bridge.mjs';

export const R0_SIGNED_EVIDENCE_SCHEMA='CGX-PRINTSPACE-R0-SIGNED-EVIDENCE/0.1';
export const R0_SIGNED_STATEMENT_SCHEMA='CGX-PRINTSPACE-R0-SIGNED-STATEMENT/0.1';
export const R0_TRUST_PINS_SCHEMA='CGX-PRINTSPACE-R0-OWNER-TRUST-PINS/0.1';
const ROLES=['host','registry','rights'];
const HEX64=/^[a-f0-9]{64}$/;
const CONTENT_SHA=/^sha256:[a-f0-9]{64}$/;
const HEX40=/^[a-f0-9]{40}$/;
const SAFE_ID=/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;
const MAX_BYTES=128*1024;
const MAX_AGE_SECONDS=300;
const ALLOWED_SKEW_SECONDS=30;
const BAD=new Set(['password','secret','cookie','authorization','token','private_key','private_key_pem','source_bytes','source_locator','source_url','private_path','toolpath','gcode','machine_command','mint_receipt','native_dbr_receipt','lease']);
const isRecord=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const exact=(obj,keys)=>isRecord(obj)&&Object.keys(obj).sort().join('|')===keys.slice().sort().join('|');
function canonical(value,depth=0){
  if(depth>20)throw Error('NESTED_INPUT_BUDGET');
  if(Array.isArray(value))return value.map(x=>canonical(x,depth+1));
  if(isRecord(value)){
    const out={};
    for(const key of Object.keys(value).sort()){
      if(key==='__proto__'||BAD.has(key.toLowerCase()))throw Error('PRIVATE_OR_DEVICE_FIELD');
      out[key]=canonical(value[key],depth+1);
    }
    return out;
  }
  if(value===null||typeof value==='string'||typeof value==='boolean'||
     (typeof value==='number'&&Number.isSafeInteger(value)))return value;
  throw Error('NONCANONICAL_INPUT');
}
export const canonicalR0StatementBytes=statement=>Buffer.from(JSON.stringify(canonical(statement)),'utf8');
const digest=raw=>createHash('sha256').update(raw).digest('hex');
const deny=code=>Object.freeze({schema:R0_SIGNED_EVIDENCE_SCHEMA,state:'HOLD',hold_code:code,
  signatures_verified:false,trust_root_origin_authenticated:false,
  real_source_readback_authenticated:false,real_rights_independently_accepted:false,
  host_session_independently_authenticated:false,challenge_consumption_recorded:false,
  native_admitted:false,private_hydration_authorised:false,source_bytes_hydrated:0,
  native_dbr_written:false,machine_authorised:false,mint_authorised:false,
  commercial_release_authorised:false});
const safeId=s=>typeof s==='string'&&SAFE_ID.test(s);

function pinnedRoot(trust){
  if(!exact(trust,['schema','key_roles','revocation_epoch'])||trust.schema!==R0_TRUST_PINS_SCHEMA||
     !Number.isSafeInteger(trust.revocation_epoch)||trust.revocation_epoch<0||trust.revocation_epoch>1_000_000)
    throw Error('TRUST_ROOT_STRUCTURE');
  if(!exact(trust.key_roles,ROLES))throw Error('THREE_INDEPENDENT_ROLES_REQUIRED');
  const pins={};const fingerprints=new Set();const ids=new Set();
  for(const role of ROLES){
    const row=trust.key_roles[role];
    if(!exact(row,['key_id','public_key_pem','spki_sha256','revoked'])||
       !safeId(row.key_id)||!HEX64.test(row.spki_sha256)||row.revoked!==false||
       typeof row.public_key_pem!=='string'||
       !row.public_key_pem.startsWith('-----BEGIN PUBLIC KEY-----\n')||
       !row.public_key_pem.trimEnd().endsWith('-----END PUBLIC KEY-----'))
      throw Error('UNTRUSTED_OR_REVOKED_KEY');
    const key=createPublicKey(row.public_key_pem);
    if(key.type!=='public'||key.asymmetricKeyType!=='ed25519')throw Error('NON_ED25519_PUBLIC_KEY');
    const fingerprint=digest(key.export({type:'spki',format:'der'}));
    if(fingerprint!==row.spki_sha256||fingerprints.has(fingerprint)||ids.has(row.key_id))
      throw Error('PIN_DRIFT_OR_ROLE_KEY_REUSE');
    fingerprints.add(fingerprint);ids.add(row.key_id);
    pins[role]={key,key_id:row.key_id,spki_sha256:fingerprint};
  }
  return pins;
}

function strictAssertions(role,x){
  if(role==='registry')return exact(x,['identity_matches','collision_state','lineage_state','revoked','source_snapshot_sha256'])&&
    x.identity_matches===1&&x.collision_state==='NO_COLLISION_IN_ATTESTOR_SNAPSHOT'&&
    x.lineage_state==='EXACT_ID_AND_TWIN_IN_ATTESTOR_SNAPSHOT'&&x.revoked===false&&CONTENT_SHA.test(x.source_snapshot_sha256);
  if(role==='rights')return exact(x,['rights_scope','licence_ref','revoked','rights_scope_state'])&&
    x.rights_scope==='R0_REVIEW_ONLY'&&safeId(x.licence_ref)&&x.revoked===false&&
    x.rights_scope_state==='REVIEW_PERMISSION_ASSERTED_BY_SIGNER';
  return exact(x,['acl_scope','session_review_state','revoked','dbr_mutation'])&&
    x.acl_scope==='R0_REVIEW_ONLY'&&
    x.session_review_state==='REVIEW_CONTEXT_ASSERTED_BY_SIGNER'&&
    x.revoked===false&&x.dbr_mutation===false;
}

export function verifyPrintspaceR0SignedEvidence(request,trustPins,clockSeconds){
  if(!exact(request,['source_review_input','source_review_pins','challenge','role_receipts']))
    return deny('SIGNED_REVIEW_REQUEST_SCHEMA');
  if(!Number.isSafeInteger(clockSeconds)||clockSeconds<0)return deny('HOST_CLOCK_REQUIRED');
  let roleKeys;
  try{roleKeys=pinnedRoot(trustPins);}catch(_){return deny('UNTRUSTED_ROOT_PIN_SET')}
  try{
    const json=JSON.stringify(canonical({request,trustPins}));
    if(Buffer.byteLength(json,'utf8')>MAX_BYTES)return deny('SIGNED_EVIDENCE_SIZE_BUDGET');
    const ctx=reviewPrintspaceHostR0(request.source_review_input,request.source_review_pins);
    if(ctx.state!=='PLAN_ONLY_NOT_HYDRATED')return deny('EXISTING_UNISPACE_SOURCE_REVIEW_HOLD');
    const challenge=request.challenge;
    if(!exact(challenge,['nonce','issued_at_seconds','expires_at_seconds'])||
       typeof challenge.nonce!=='string'||!HEX64.test(challenge.nonce)||
       !Number.isSafeInteger(challenge.issued_at_seconds)||
       !Number.isSafeInteger(challenge.expires_at_seconds)||
       challenge.expires_at_seconds<=challenge.issued_at_seconds||
       challenge.expires_at_seconds-challenge.issued_at_seconds>MAX_AGE_SECONDS||
       clockSeconds+ALLOWED_SKEW_SECONDS<challenge.issued_at_seconds||
       clockSeconds>=challenge.expires_at_seconds)
      return deny('UNBOUND_STALE_OR_FUTURE_CHALLENGE');
    const rows=request.role_receipts;
    if(!Array.isArray(rows)||rows.length!==ROLES.length)return deny('THREE_ROLE_RECEIPTS_REQUIRED');
    const completed=new Set();const evidences=[];
    const item=request.source_review_input.plan.r0_cases.find(x=>x.product_id===ctx.product_id);
    if(!item||!item.candidate_object_id||!item.twin_id_candidate)return deny('ORIGINAL_PRODUCT_BINDING_MISSING');
    const requiredKeys=['schema','role','scope','request_nonce','issued_at_seconds','expires_at_seconds',
      'revocation_epoch','plan_sha256','product_facet_sha256','bundle_sha256','object_id','twin_id',
      'filespace','lineage_git_blob_sha','registry_git_blob_sha','evidence_ref','assertions'];
    for(const entry of rows){
      if(!exact(entry,['role','key_id','statement','signature_b64'])||
         !ROLES.includes(entry.role)||completed.has(entry.role)||!safeId(entry.key_id)||
         entry.key_id!==roleKeys[entry.role].key_id||!exact(entry.statement,requiredKeys))
        return deny('DUPLICATE_OR_UNKNOWN_ATTESTOR_ROLE');
      completed.add(entry.role);
      const s=entry.statement;
      if(s.schema!==R0_SIGNED_STATEMENT_SCHEMA||s.role!==entry.role||
         s.scope!=='R0_REVIEW_ONLY'||s.request_nonce!==challenge.nonce||
         s.issued_at_seconds!==challenge.issued_at_seconds||
         s.expires_at_seconds!==challenge.expires_at_seconds||
         s.revocation_epoch!==trustPins.revocation_epoch||
         s.plan_sha256!==ctx.plan_sha256||s.product_facet_sha256!==ctx.product_facet_sha256||
         s.bundle_sha256!==ctx.bundle_sha256||s.object_id!==ctx.object_id||
         s.twin_id!==item.twin_id_candidate||s.filespace!=='Romer.cgx'||
         s.lineage_git_blob_sha!==ctx.source_lineage_sha_candidate||
         s.registry_git_blob_sha!==ctx.source_registry_sha_candidate||
         !HEX40.test(s.lineage_git_blob_sha)||!HEX40.test(s.registry_git_blob_sha)||
         !safeId(s.evidence_ref)||!strictAssertions(entry.role,s.assertions))
        return deny('SIGNATURE_STATEMENT_CONTEXT_OR_RIGHTS_DRIFT');
      if(typeof entry.signature_b64!=='string'||entry.signature_b64.length>128||
         !/^[A-Za-z0-9+/]+={0,2}$/.test(entry.signature_b64))
        return deny('SIGNATURE_ENCODING');
      const sig=Buffer.from(entry.signature_b64,'base64');
      if(sig.length!==64||sig.toString('base64')!==entry.signature_b64||
         !verifySignature(null,canonicalR0StatementBytes(s),roleKeys[entry.role].key,sig))
        return deny('ED25519_SIGNATURE_INVALID');
      evidences.push({role:entry.role,key_id:entry.key_id,
        public_key_sha256:roleKeys[entry.role].spki_sha256,
        signed_statement_sha256:digest(canonicalR0StatementBytes(s)),
        evidence_ref:s.evidence_ref});
    }
    if(completed.size!==ROLES.length)return deny('ROLE_QUORUM_NOT_SATISFIED');
    evidences.sort((a,b)=>a.role.localeCompare(b.role));
    const summary={schema:R0_SIGNED_EVIDENCE_SCHEMA,
      state:'THREE_ROLE_ED25519_SIGNATURES_VALID_REVIEW_ONLY',
      product_id:ctx.product_id,object_id:ctx.object_id,filespace:'Romer.cgx',
      product_facet_sha256:ctx.product_facet_sha256,bundle_sha256:ctx.bundle_sha256,
      plan_sha256:ctx.plan_sha256,nonce_digest_sha256:digest(challenge.nonce),
      valid_until_seconds:challenge.expires_at_seconds,
      proof_roles:evidences,signatures_verified:true,
      trust_root_origin_authenticated:false,
      real_source_readback_authenticated:false,
      real_rights_independently_accepted:false,
      host_session_independently_authenticated:false,
      challenge_consumption_recorded:false,
      native_admitted:false,private_hydration_authorised:false,source_bytes_hydrated:0,
      native_dbr_written:false,machine_authorised:false,mint_authorised:false,
      commercial_release_authorised:false,
      next_gate:'OWNER_ROOT_ANCHOR_AND_HOST_DB_ACL_REVOCATION_LEDGER_READBACK'};
    summary.review_receipt_sha256=digest(Buffer.from(JSON.stringify(canonical(summary))));
    return Object.freeze(summary);
  }catch(_){return deny('MALFORMED_PRIVATE_OR_UNBOUND_ATTESTATION')}
}
