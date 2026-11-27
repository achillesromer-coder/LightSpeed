/** Reversible contract configuration vocabulary. Not legal drafting, a signature
 * verifier, a lease issuer, a contract VM, or a replacement for native standards.
 * Original R0 bytes, exceptions and provider-native signing payloads stay intact.
 */
export const CONTRACT_SCHEMA="CGX-COMMITMENT-SHORTHAND/1";
export const COMMITMENT_CLASSES=Object.freeze(["oblige","permit","prohibit","declare"]);
export const VARIABLE_TYPES=Object.freeze(["ref","text","bool","integer","decimal","quantity","utc","sha256"]);
const profiles={
 exchange:["oblige","permit"], service:["oblige","declare"], confidentiality:["prohibit","oblige","permit"],
 licence:["permit","prohibit","oblige"], execution_lease:["permit","prohibit","oblige"],
 delegation:["permit","oblige","prohibit"], attestation:["declare"], governance:["declare","oblige","permit","prohibit"],
 custom:[...COMMITMENT_CLASSES]
};
export const CONFIGURATIONS=Object.freeze(Object.fromEntries(Object.entries(profiles).map(([k,v])=>[k,Object.freeze(v)])));
export const SIGNATURE_PROFILES=Object.freeze(["cgx-ed25519-bytes/1","external-pades","external-cades","external-jades","external-eip712","external-provider"]);
const F=["contract_ref","revision","previous_payload_sha256","source_ref","source_sha256","residual_ref","configuration","parties","variables","commitments","signature_policy","valid_from","valid_until","native_adapter"];
const fail=code=>{throw Error(code);},must=(ok,code)=>{if(!ok)fail(code);};
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const exact=(x,keys)=>obj(x)&&Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
const text=(x,n=256)=>typeof x==="string"&&x.length>0&&x.length<=n&&x===x.normalize("NFC")&&!/[\p{Cc}\p{Cf}\p{Cs}\p{Zl}\p{Zp}]/u.test(x);
const id=x=>typeof x==="string"&&/^[A-Za-z][A-Za-z0-9_.:-]{0,95}$/.test(x)&&!["__proto__","constructor","prototype"].includes(x);
const sha=x=>typeof x==="string"&&/^[a-f0-9]{64}$/.test(x);
const utc=x=>typeof x==="string"&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(x)&&Number.isFinite(Date.parse(x))&&new Date(x).toISOString()===x;
const int=x=>typeof x==="string"&&/^(?:0|-?[1-9][0-9]{0,63})$/.test(x);
const dec=x=>typeof x==="string"&&/^-?(?:0|[1-9][0-9]{0,47})(?:\.[0-9]{0,30}[1-9])?$/.test(x)&&x!=="-0";
const dense=x=>Array.isArray(x)&&Object.keys(x).length===x.length&&Array.from({length:x.length},(_,i)=>Object.hasOwn(x,i)).every(Boolean);
const rows=(x,max)=>Array.isArray(x)&&x.length<=max&&dense(x);
const tuple=(x,n)=>Array.isArray(x)&&x.length===n&&dense(x);
const unique=a=>new Set(a).size===a.length;
const checkValue=(type,v)=>{
 switch(type){
  case "ref":return text(v);case "text":return text(v,2048);case "bool":return typeof v==="boolean";
  case "integer":return int(v);case "decimal":return dec(v);
  case "quantity":return tuple(v,2)&&dec(v[0])&&typeof v[1]==="string"&&/^[A-Za-z0-9][A-Za-z0-9./*^_-]{0,31}$/.test(v[1]);
  case "utc":return utc(v);case "sha256":return sha(v);default:return false;
 }
};
const clone=v=>Array.isArray(v)?Array.from(v,clone):v;
const bounded=x=>{must(new TextEncoder().encode(JSON.stringify(x)).length<=262144,"CONTRACT_METADATA_BUDGET");return x;};
/** Exact record. No missing-field defaults, inferred consent, floating-point
 * amount rounding, sorting of legally meaningful clauses or implicit amendments.
 * Parties [id,identity_ref,role]; variables [id,type,value]; commitments
 * [id,class,actor,beneficiary|null,action_ref,variable_ids,conditions,evidence_refs,requires].
 * Each condition [variable_id,eq|ne|lt|le|gt|ge,typed_literal].
 * Conditions are AND within a clause. Other logic must remain in original source/residual.
 */
function normalise(d){
 must(exact(d,F),"CONTRACT_FIELD_SET");
 must(id(d.contract_ref)&&Number.isSafeInteger(d.revision)&&d.revision>=1,"CONTRACT_ID_REVISION");
 must(d.revision===1?d.previous_payload_sha256===null:sha(d.previous_payload_sha256),"AMENDMENT_LINK_REQUIRED");
 must(text(d.source_ref)&&sha(d.source_sha256)&&(d.residual_ref===null||text(d.residual_ref)),"CONTRACT_SOURCE_REQUIRED");
 must(Object.hasOwn(CONFIGURATIONS,d.configuration),"UNKNOWN_CONFIGURATION");
 must(rows(d.parties,64)&&d.parties.length>0&&d.parties.every(p=>tuple(p,3)&&id(p[0])&&text(p[1])&&id(p[2]))&&unique(d.parties.map(p=>p[0])),"PARTIES_INVALID");
 const parties=new Set(d.parties.map(p=>p[0])),identities=new Map(d.parties.map(p=>[p[0],p[1]]));
 must(rows(d.variables,128)&&d.variables.every(v=>tuple(v,3)&&id(v[0])&&VARIABLE_TYPES.includes(v[1])&&checkValue(v[1],v[2]))&&unique(d.variables.map(v=>v[0])),"VARIABLES_INVALID");
 const vars=new Map(d.variables.map(v=>[v[0],v]));
 must(rows(d.commitments,128)&&d.commitments.length>0&&d.commitments.every(c=>tuple(c,9)&&id(c[0]))&&unique(d.commitments.map(c=>c[0])),"COMMITMENTS_INVALID");
 const clauses=new Map(d.commitments.map(c=>[c[0],c]));
 for(const c of d.commitments){
  const [key,kind,actor,beneficiary,action,inputs,conditions,evidence,requires]=c;
  // Configuration is a view/preset, not a constraint that silently deletes unfamiliar commitments.
  must(COMMITMENT_CLASSES.includes(kind)&&parties.has(actor)&&(beneficiary===null||parties.has(beneficiary))&&text(action),"COMMITMENT_SCOPE");
  must(rows(inputs,32)&&unique(inputs)&&inputs.every(x=>vars.has(x)),"COMMITMENT_VARIABLE_REF");
  must(rows(conditions,32)&&conditions.every(q=>tuple(q,3)&&vars.has(q[0])&&inputs.includes(q[0])&&
   ["eq","ne","lt","le","gt","ge"].includes(q[1])&&checkValue(vars.get(q[0])[1],q[2])&&
   (["eq","ne"].includes(q[1])||["integer","decimal","utc"].includes(vars.get(q[0])[1]))),"CONDITION_INVALID");
  must(rows(evidence,32)&&unique(evidence)&&evidence.every(x=>text(x)),"EVIDENCE_REF_INVALID");
  must(rows(requires,32)&&unique(requires)&&requires.every(x=>x!==key&&clauses.has(x)),"COMMITMENT_DEPENDENCY_INVALID");
 }
 const seen=new Set(),active=new Set();
 function visit(key){must(!active.has(key),"COMMITMENT_CYCLE");if(seen.has(key))return;active.add(key);for(const dep of clauses.get(key)[8])visit(dep);active.delete(key);seen.add(key);}
 for(const key of clauses.keys())visit(key);
 const sig=d.signature_policy;
 must(tuple(sig,3)&&SIGNATURE_PROFILES.includes(sig[0])&&rows(sig[1],64)&&sig[1].length>0&&unique(sig[1])&&sig[1].every(x=>parties.has(x))&&
  unique(sig[1].map(x=>identities.get(x)))&&Number.isSafeInteger(sig[2])&&sig[2]>=1&&sig[2]<=sig[1].length,"SIGNATURE_POLICY_INVALID");
 must(utc(d.valid_from)&&utc(d.valid_until)&&Date.parse(d.valid_from)<Date.parse(d.valid_until),"VALIDITY_INTERVAL_INVALID");
 const a=d.native_adapter;
 must(a===null||(tuple(a,4)&&["execution-lease","node-exchange","evm-abi","document-signature","external"].includes(a[0])&&text(a[1])&&text(a[2])&&sha(a[3])),"NATIVE_ADAPTER_INVALID");
 return bounded(Object.fromEntries(F.map(k=>[k,clone(d[k])])));
}
export function packContract(d){const n=normalise(d);return [CONTRACT_SCHEMA,...F.map(k=>n[k])];}
export function unpackContract(t){
 must(tuple(t,F.length+1)&&t[0]===CONTRACT_SCHEMA,"CONTRACT_TUPLE_INVALID");
 const d=normalise(Object.fromEntries(F.map((k,i)=>[k,t[i+1]])));
 must(JSON.stringify(packContract(d))===JSON.stringify(t),"CONTRACT_TUPLE_NONCANONICAL");return d;
}
/** Symbolic ternary addresses, not T173 shape IDs or physical geometry.
 * Section trit path identifies constituent class; five trits encode ordinal
 * within the exact revision. Insertion can move an ordinal, never the stable ID.
 */
const addr=(section,i)=>[...section,...i.toString(3).padStart(5,"0").split("").map(Number)];
export function projectContract(t){
 const d=unpackContract(t),groups=[
 ["parties",[0,0],d.parties],["variables",[0,1],d.variables],["commitments",[0,2],d.commitments],
 ["signature_policy",[1,0],[["policy",...d.signature_policy]]],["validity",[1,1],[["interval",d.valid_from,d.valid_until]]],
 ["lineage",[1,2],[["source",d.source_ref,d.source_sha256,d.residual_ref,d.revision,d.previous_payload_sha256]]],
 ["adapter",[2,0],d.native_adapter?[["adapter",...d.native_adapter]]:[]]];
 const constituents=groups.map(([kind,path,items])=>({kind,path,children:items.map((v,i)=>({ref:v[0],path:addr(path,i),value:clone(v)}))}));
 const order=[],visited=new Set(),byId=new Map(d.commitments.map(c=>[c[0],c]));
 const visit=key=>{if(visited.has(key))return;for(const k of byId.get(key)[8])visit(k);visited.add(key);order.push(key);};
 for(const k of byId.keys())visit(k);
 return {schema:CONTRACT_SCHEMA,ref:d.contract_ref,revision:d.revision,configuration:d.configuration,
  suggested_classes:[...CONFIGURATIONS[d.configuration]],human_top_down:{ref:d.contract_ref,children:constituents},
  machine_bottom_up:{commitment_order:order,tuple:packContract(d)},symbolic_geometry:true,physical_geometry_verified:false,
  legal_validity_verified:false,semantic_equivalence_verified:false,signature_verified:false,native_admission:false,execution_authorized:false};
}
/** Domain separated, exact UTF-8 signing preimage for this schema only.
 * Native EIP-712/PAdES/etc signing MUST use the actual native adapter's bytes.
 * No key, signature, consent, clock authority, verification or signing occurs here.
 */
export function prepareContractSignature(t,{party_id,key_ref,challenge,context_ref}={}){
 const d=unpackContract(t),[profile,signers]=d.signature_policy;
 must(signers.includes(party_id)&&text(key_ref)&&text(context_ref)&&typeof challenge==="string"&&/^[a-f0-9]{64}$/.test(challenge),"SIGN_REQUEST_INVALID");
 const binding=["CGX-CONTRACT-SIGNING-INTENT/1","cgx:root:cognigrex",packContract(d),party_id,key_ref,challenge,context_ref];
 const native=profile!=="cgx-ed25519-bytes/1";
 return {schema:"CGX-CONTRACT-SIGNING-INTENT/1",profile,party_id,
  state:native?"HOLD_NATIVE_SIGNING_PAYLOAD_ADAPTER":"UNSIGNED_PREIMAGE_ONLY",
  preimage_utf8:native?null:JSON.stringify(binding),intent_binding:binding,
  native_payload_verified:false,key_binding_verified:false,signature_verified:false,
  threshold_satisfied:false,consent_verified:false,legal_validity_verified:false,execution_authorized:false};
}

/** Verify an exact, recomputed CGX signing preimage with a caller-supplied
 * Ed25519 public key. This is only mathematical verification, never a trust
 * store, identity/key binding, replay check, consent or threshold decision.
 * External signature schemes must use their own native verification adapter.
 */
export async function verifyContractSignature(t,intent,publicKeyHex,signatureHex){
 const result=(state,valid=false)=>({schema:"CGX-CONTRACT-SIGNATURE-CHECK/1",state,mathematical_signature_valid:valid,
  signer_identity_verified:false,key_binding_verified:false,challenge_freshness_verified:false,
  threshold_satisfied:false,consent_verified:false,legal_validity_verified:false,
  execution_authorized:false,native_admission:false});
 try{
  const p=prepareContractSignature(t,intent);
  if(p.profile!=="cgx-ed25519-bytes/1")return result("HOLD_NATIVE_VERIFICATION_ADAPTER");
  if(!/^[a-f0-9]{64}$/.test(publicKeyHex)||typeof publicKeyHex!=="string"||
     typeof signatureHex!=="string"||!/^[a-f0-9]{128}$/.test(signatureHex))return result("INVALID_SIGNATURE_ENCODING");
  const subtle=globalThis.crypto?.subtle;
  if(!subtle)return result("HOLD_CRYPTO_PROVIDER_UNAVAILABLE");
  const bytes=x=>Uint8Array.from(x.match(/../g),b=>parseInt(b,16));
  const key=await subtle.importKey("raw",bytes(publicKeyHex),{name:"Ed25519"},false,["verify"]);
  const valid=await subtle.verify({name:"Ed25519"},key,bytes(signatureHex),new TextEncoder().encode(p.preimage_utf8));
  return result(valid?"MATHEMATICAL_SIGNATURE_VALID_ONLY":"SIGNATURE_MISMATCH",valid);
 }catch{return result("SIGNATURE_CHECK_FAILED");}
}
