/**
 * PrintSpace R0 deterministic, bounded *review* batch and replay simulation.
 * Reuses the existing three-role Ed25519 verifier. No new signing, native DBR,
 * authenticated challenge consumption, network, persistent store, or machine IO.
 * A repeated nonce in one batch is denied. Cross-batch replay is NOT prevented;
 * the supplied historical digest set is an UNTRUSTED negative-only deny hint.
 */
import {createHash} from 'node:crypto';
import {verifyPrintspaceR0SignedEvidence} from './printspaceR0SignedEvidence.mjs';

export const SCHEMA='CGX-PRINTSPACE-R0-BATCH-REVIEW/0.1';
export const MAX_CASES=512;
export const MAX_BYTES=8*1024*1024;
const HEX=/^[0-9a-f]{64}$/;
const record=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const sha=s=>createHash('sha256').update(s).digest('hex');
const denial=(code)=>Object.freeze({schema:SCHEMA,state:'HOLD',hold_code:code,
  case_count:0,results:[],review_valid_count:0,invalid_count:0,
  within_batch_replay_count:0,consumed_hint_replay_count:0,
  native_admitted:false,challenge_consumption_recorded:false,
  trust_root_origin_authenticated:false,machine_authorised:false,
  native_dbr_written:false,mint_authorised:false,commercial_release_authorised:false});
function safeTransport(value){
  // Never echo input. Validate shape and byte budget without accepting private
  // keys, executable values, NaN, cycles or prototype tricks in the batch.
  if(!record(value))return null;
  try {
    const json=JSON.stringify(value);
    if(typeof json!=='string'||Buffer.byteLength(json,'utf8')>MAX_BYTES)return null;
    return json;
  }catch(_){return null}
}
export function reviewPrintspaceR0Batch(batch){
  if(!record(batch))return denial('BATCH_INPUT_NOT_CANONICAL_OR_TOO_LARGE');
  if(Object.keys(batch).sort().join('|')!==['cases','known_consumed_nonce_sha256','schema'].sort().join('|')||batch.schema!==SCHEMA)
    return denial('BATCH_SCHEMA_OR_PRIVILEGE_EXTRA');
  if(!Array.isArray(batch.cases)||batch.cases.length<1||batch.cases.length>MAX_CASES)
    return denial('BATCH_SIZE_EXCEEDED');
  const raw=safeTransport(batch);
  if(raw===null)return denial('BATCH_INPUT_NOT_CANONICAL_OR_TOO_LARGE');
  const historical=batch.known_consumed_nonce_sha256;
  if(!Array.isArray(historical)||historical.length>4096||historical.some(x=>typeof x!=='string'||!HEX.test(x))||new Set(historical).size!==historical.length)
    return denial('INVALID_HISTORICAL_NONCE_DENY_HINTS');
  const consumedHint=new Set(historical);
  const observed=new Set();
  const results=[];
  let reviewValid=0,invalid=0,duplicate=0,historicalHold=0;
  for(let i=0;i<batch.cases.length;i++){
    const item=batch.cases[i];
    const props=['request','trust_pins','clock_seconds'];
    if(!record(item)||Object.keys(item).sort().join('|')!==props.slice().sort().join('|')){
      results.push({index:i,state:'HOLD',hold_code:'CASE_SCHEMA',nonce_digest_sha256:null}); invalid++;continue;
    }
    if(!Number.isSafeInteger(item.clock_seconds)||item.clock_seconds<0){
      results.push({index:i,state:'HOLD',hold_code:'HOST_CLOCK_REQUIRED',nonce_digest_sha256:null});
      invalid++;continue;
    }
    const nonce=item.request?.challenge?.nonce;
    // Note: verifyPrintspaceR0SignedEvidence independently rejects malformed
    // nonces, stale clocks, source changes and forged signature/rights inputs.
    const nonceHash=typeof nonce==='string'&&HEX.test(nonce)?sha(nonce):null;
    if(nonceHash && consumedHint.has(nonceHash)){
      results.push({index:i,state:'HOLD',hold_code:'UNTRUSTED_HISTORY_REPLAY_DENY',nonce_digest_sha256:nonceHash});
      historicalHold++;continue;
    }
    if(nonceHash && observed.has(nonceHash)){
      results.push({index:i,state:'HOLD',hold_code:'WITHIN_BATCH_NONCE_REPLAY',nonce_digest_sha256:nonceHash});
      duplicate++;continue;
    }
    const value=verifyPrintspaceR0SignedEvidence(item.request,item.trust_pins,item.clock_seconds);
    if(value.state==='THREE_ROLE_ED25519_SIGNATURES_VALID_REVIEW_ONLY'){
      if(nonceHash===null||value.nonce_digest_sha256!==nonceHash){
        results.push({index:i,state:'HOLD',hold_code:'VERIFIED_NONCE_INCONSISTENT',nonce_digest_sha256:nonceHash});invalid++;continue;
      }
      observed.add(nonceHash);
      results.push({index:i,state:'SIGNATURES_VALID_REVIEW_ONLY',hold_code:null,
        nonce_digest_sha256:nonceHash,product_id:value.product_id,
        review_receipt_sha256:value.review_receipt_sha256});
      reviewValid++;
    }else{
      results.push({index:i,state:'HOLD',hold_code:value.hold_code||'SIGNATURE_REVIEW_HOLD',nonce_digest_sha256:nonceHash});
      invalid++;
    }
  }
  const summary={schema:SCHEMA,state:'BATCH_DIGITAL_REVIEW_ONLY',
    case_count:batch.cases.length,results,
    review_valid_count:reviewValid,invalid_count:invalid,
    within_batch_replay_count:duplicate,consumed_hint_replay_count:historicalHold,
    historical_hints_independently_authenticated:false,
    host_challenge_ledger_persisted:false,across_batch_replay_prevented:false,
    trust_root_origin_authenticated:false,native_admitted:false,
    challenge_consumption_recorded:false,machine_authorised:false,
    native_dbr_written:false,mint_authorised:false,commercial_release_authorised:false};
  // Result digest is deterministic, does not contain signatures, tokens, PEM,
  // private paths, raw challenge or captured original request fields.
  summary.receipt_sha256=sha(JSON.stringify(summary));
  return Object.freeze(summary);
}

/** Same input, same digest; not a server-side replay ledger. */
export function replayPrintspaceR0Batch(receipt,batch){
  const expected=reviewPrintspaceR0Batch(batch);
  return Object.freeze({schema:'CGX-PRINTSPACE-R0-BATCH-BACKTRACE/0.1',
    state:record(receipt)&&expected.state==='BATCH_DIGITAL_REVIEW_ONLY'&&
      JSON.stringify(receipt)===JSON.stringify(expected)?'PASS_DIGITAL_ONLY':'HOLD',
    expected_receipt_sha256:expected.receipt_sha256||null,
    native_admitted:false,challenge_consumption_recorded:false,
    physical_machine_authorised:false});
}
