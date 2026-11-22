/**
 * CGX PrintSpace R0: verify signatures FIRST, then ask the supplied host for
 * one atomic challenge insert.  This is an adapter, not a persistent database.
 * A ledger response is structurally checked, but its provider identity and
 * owner authority cannot be proven from these bytes.  No DBR, native LOAD,
 * rights admission, private hydration, publication or physical control.
 */
import {verifyPrintspaceR0SignedEvidence} from './printspaceR0SignedEvidence.mjs';
import {createHash} from 'node:crypto';

export const R0_ATOMIC_SCHEMA='CGX-PRINTSPACE-R0-ATOMIC-REVIEW/0.1';
export const R0_LEDGER_REQUEST_SCHEMA='CGX-PRINTSPACE-R0-NONCE-INSERT-REQUEST/0.1';
export const R0_LEDGER_ACK_SCHEMA='CGX-PRINTSPACE-R0-NONCE-INSERT-ACK/0.1';
const HEX=/^[0-9a-f]{64}$/;
const isRecord=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const exact=(x,fields)=>isRecord(x)&&Object.keys(x).sort().join('|')===fields.slice().sort().join('|');
const hash=x=>createHash('sha256').update(x).digest('hex');
const DENIED={native_admitted:false,private_hydration_authorised:false,source_bytes_hydrated:0,
  native_dbr_written:false,mint_authorised:false,machine_authorised:false,
  commercial_release_authorised:false,owner_trust_root_authenticated:false,
  host_ledger_independently_authenticated:false,challenge_consumption_authoritative:false};
function hold(code){return Object.freeze({schema:R0_ATOMIC_SCHEMA,state:'HOLD',
  hold_code:code,reference_insert_recorded:false,
  reference_replay_conflict:false,...DENIED});}
const requestKeys=['schema','nonce_digest_sha256','review_receipt_sha256',
  'product_facet_sha256','plan_sha256','expires_at_seconds'];

/** Host callback MUST implement a globally UNIQUE atomic insert, no read/insert split.
 * This function cannot confer trust on the callback. It cannot be invoked with
 * arbitrary unsigned review receipts: three-role Ed25519 is checked first.
 */
export async function reviewPrintspaceR0WithAtomicLedger(caseInput, ledger){
  if(!exact(caseInput,['request','trust_pins','clock_seconds']))return hold('CASE_INPUT_SCHEMA');
  if(!isRecord(ledger)||typeof ledger.consumeNonce!=='function')return hold('HOST_ATOMIC_LEDGER_REQUIRED');
  try{
    const proof=verifyPrintspaceR0SignedEvidence(caseInput.request,caseInput.trust_pins,caseInput.clock_seconds);
    if(proof.state!=='THREE_ROLE_ED25519_SIGNATURES_VALID_REVIEW_ONLY')
      return hold(proof.hold_code||'SIGNED_R0_REVIEW_HOLD');
    if(!HEX.test(proof.nonce_digest_sha256)||!HEX.test(proof.review_receipt_sha256)||
       !HEX.test(proof.plan_sha256)||!Number.isSafeInteger(proof.valid_until_seconds))
      return hold('SIGNED_R0_RECEIPT_INVALID');
    const insert={schema:R0_LEDGER_REQUEST_SCHEMA,
      nonce_digest_sha256:proof.nonce_digest_sha256,
      review_receipt_sha256:proof.review_receipt_sha256,
      product_facet_sha256:proof.product_facet_sha256,
      plan_sha256:proof.plan_sha256,
      expires_at_seconds:proof.valid_until_seconds};
    if(!exact(insert,requestKeys))return hold('HOST_INSERT_REQUEST_INVALID');
    // A rejected/restarted/partitioned host must HOLD, never fallback to an
    // in-memory success or replay-safe claim. Atomicity lives in this adapter.
    const ack=await ledger.consumeNonce(Object.freeze(insert));
    if(!exact(ack,['schema','state','nonce_digest_sha256','review_receipt_sha256'])||
       ack.schema!==R0_LEDGER_ACK_SCHEMA||ack.nonce_digest_sha256!==insert.nonce_digest_sha256||
       ack.review_receipt_sha256!==insert.review_receipt_sha256||
       !['INSERTED','ALREADY_PRESENT'].includes(ack.state))return hold('UNTRUSTED_LEDGER_ACK');
    if(ack.state==='ALREADY_PRESENT')return Object.freeze({
      ...hold('NONCE_ALREADY_PRESENT_IN_REFERENCE_LEDGER'),
      reference_replay_conflict:true,
    });
    // INSERTED is only the host ADAPTER'S assertion; it is NOT independent
    // host attestation or proof of native owner/ACL permission.
    const result={schema:R0_ATOMIC_SCHEMA,
      state:'REFERENCE_LEDGER_INSERTED_REVIEW_ONLY',hold_code:null,
      review_receipt_sha256:proof.review_receipt_sha256,
      nonce_digest_sha256:proof.nonce_digest_sha256,
      product_id:proof.product_id,plan_sha256:proof.plan_sha256,
      reference_insert_recorded:true,reference_replay_conflict:false,
      host_insert_ack_sha256:hash(JSON.stringify({schema:ack.schema,
        nonce_digest_sha256:ack.nonce_digest_sha256,
        review_receipt_sha256:ack.review_receipt_sha256,state:ack.state})),...DENIED};
    return Object.freeze(result);
  }catch(_){return hold('SIGNED_REVIEW_OR_LEDGER_UNAVAILABLE')}
}

/** Deterministic audit of an already completed adapter response, not a second
 * ledger read or a native consumption receipt. NEVER calls ledger.consumeNonce.
 */
export function inspectPrintspaceR0AtomicReceipt(receipt){
  if(!isRecord(receipt))return Object.freeze({state:'HOLD',reason:'MISSING_RECEIPT',...DENIED});
  const valid=receipt.schema===R0_ATOMIC_SCHEMA&&
    (receipt.state==='HOLD'||receipt.state==='REFERENCE_LEDGER_INSERTED_REVIEW_ONLY')&&
    receipt.native_admitted===false&&receipt.challenge_consumption_authoritative===false&&
    receipt.owner_trust_root_authenticated===false&&receipt.host_ledger_independently_authenticated===false&&
    receipt.machine_authorised===false&&receipt.native_dbr_written===false;
  return Object.freeze({state:valid?'REVIEW_RECEIPT_SHAPE_ONLY':'HOLD',
    reason:valid?'ORIGIN_AND_DURABLE_STORE_NOT_ATTESTED':'AUTHORITY_OR_SCHEMA_MISMATCH',...DENIED});
}
