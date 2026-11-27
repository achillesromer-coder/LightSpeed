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
export const SIGNATURE_PROFILES=Object.freeze(["cgx-ed25519-bytes/1","external-pades","external-cades","external-jades","external-eip712","external-provider","external-jws","external-cose"]);
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


/** Composition index, not a legal classification. The four primitive classes
 * give 15 nonempty presence masks. Different actors, actions, conditions,
 * remedies, source text and signature policy remain distinct. Three trits
 * encode the mask as a symbolic geometric address, not physical geometry.
 */
export function indexContractComposition(t){
 const d=unpackContract(t),counts=COMMITMENT_CLASSES.map(kind=>d.commitments.filter(c=>c[1]===kind).length);
 const mask=counts.reduce((n,v,i)=>n+(v?2**i:0),0);
 const present=COMMITMENT_CLASSES.filter((_,i)=>counts[i]>0);
 const compatible=Object.keys(CONFIGURATIONS).filter(k=>present.every(x=>CONFIGURATIONS[k].includes(x)));
 return {schema:"CGX-COMMITMENT-COMPOSITION/1",ref:d.contract_ref,revision:d.revision,
  mask,trits:mask.toString(3).padStart(3,"0").split("").map(Number),
  classes:COMMITMENT_CLASSES.map((kind,i)=>({kind,count:counts[i]})),candidate_configurations:compatible,
  declared_configuration:d.configuration,source_retained:true,legal_equivalence_verified:false,
  semantic_equivalence_verified:false,execution_authorized:false};
}
async function shaBytes(b){
 const subtle=globalThis.crypto?.subtle;
 must(!!subtle,"HOLD_CRYPTO_PROVIDER_UNAVAILABLE");
 return Array.from(new Uint8Array(await subtle.digest("SHA-256",b)),x=>x.toString(16).padStart(2,"0")).join("");
}
/** Explicit digest convention for NEW amendment links: UTF-8 JSON serialization
 * of the exact validated version-1 tuple (not original source or a signature).
 */
export async function contractPayloadDigest(t){
 return shaBytes(new TextEncoder().encode(JSON.stringify(packContract(unpackContract(t)))));
}
/** Check a complete caller-supplied history from revision one. No decision
 * about which fork is canonical, who authorized amendments, or legal effect.
 */
export async function verifyContractLineage(history){
 const result=(state,links=[])=>({schema:"CGX-CONTRACT-LINEAGE-CHECK/1",state,links,
  digest_convention:"SHA256_UTF8_JSON_EXACT_CGX_TUPLE_V1",
  complete_global_history_verified:false,amendment_authority_verified:false,
  signatures_verified:false,legal_validity_verified:false,native_admission:false,execution_authorized:false});
 try{
  if(!rows(history,128)||!history.length)return result("LINEAGE_INPUT_INVALID");
  let ref=null,prior=null,total=0;const links=[];
  for(let i=0;i<history.length;i++){
   const d=unpackContract(history[i]),bytes=new TextEncoder().encode(JSON.stringify(packContract(d)));
   total+=bytes.length;if(total>4194304)return result("LINEAGE_METADATA_BUDGET");
   if(i===0)ref=d.contract_ref;
   if(d.contract_ref!==ref||d.revision!==i+1||d.previous_payload_sha256!==prior)return result("LINEAGE_LINK_MISMATCH");
   prior=await shaBytes(bytes);links.push({contract_ref:ref,revision:d.revision,payload_sha256:prior});
  }
  return result("SUPPLIED_LINEAGE_HASH_LINKS_MATCH_ONLY",links);
 }catch(e){return result(e?.message==="HOLD_CRYPTO_PROVIDER_UNAVAILABLE"?e.message:"LINEAGE_INPUT_INVALID");}
}
/** EIP-712 unsigned typed-data projection for a *new CGX-specific* commitment
 * acknowledgement. A destination contract must independently implement and
 * verify this exact schema; this is not a transfer, permit or generic call.
 * No wallet invocation, signing, RPC, Keccak computation or replay state.
 */
export async function prepareEip712Commitment(t,intent,domain){
 const d=unpackContract(t),p=prepareContractSignature(t,intent);
 must(p.profile==="external-eip712","SIGNATURE_PROFILE_MISMATCH");
 must(d.native_adapter!==null&&d.native_adapter[0]==="evm-abi","EVM_ADAPTER_REQUIRED");
 must(exact(domain,["chain_id","verifying_contract"])&&typeof domain.chain_id==="string"&&
  /^[1-9][0-9]{0,77}$/.test(domain.chain_id)&&BigInt(domain.chain_id)<(1n<<256n)&&
  typeof domain.verifying_contract==="string"&&/^0x[0-9a-f]{40}$/.test(domain.verifying_contract)&&
  !/^0x0{40}$/.test(domain.verifying_contract),"EIP712_DOMAIN_INVALID");
 const payload=await contractPayloadDigest(t);
 const binding=await shaBytes(new TextEncoder().encode(JSON.stringify(p.intent_binding)));
 const types={EIP712Domain:[{name:"name",type:"string"},{name:"version",type:"string"},
  {name:"chainId",type:"uint256"},{name:"verifyingContract",type:"address"}],
  CGXCommitment:[{name:"contractRef",type:"string"},{name:"revision",type:"uint256"},
   {name:"payloadSha256",type:"bytes32"},{name:"intentSha256",type:"bytes32"},
   {name:"partyId",type:"string"},{name:"challenge",type:"bytes32"},
   {name:"validUntil",type:"string"}]};
 return {schema:"CGX-EIP712-COMMITMENT-PROJECTION/1",state:"UNSIGNED_TYPED_DATA_REVIEW_ONLY",
  typed_data:{types,primaryType:"CGXCommitment",domain:{name:"CGX Commitment",version:"1",
   chainId:domain.chain_id,verifyingContract:domain.verifying_contract},
   message:{contractRef:d.contract_ref,revision:String(d.revision),payloadSha256:"0x"+payload,
    intentSha256:"0x"+binding,partyId:p.party_id,challenge:"0x"+intent.challenge,validUntil:d.valid_until}},
  adapter_ref:d.native_adapter[1],adapter_version:d.native_adapter[2],adapter_sha256:d.native_adapter[3],
  chain_verified:false,destination_schema_verified:false,replay_protection_verified:false,
  signature_verified:false,key_binding_verified:false,consent_verified:false,legal_validity_verified:false,
  wallet_invoked:false,transaction_constructed:false,execution_authorized:false,native_admission:false};
}
/** Retain exact native payload bytes in FileSpace; bind their *computed* hash
 * to the CGX intent in an unsigned metadata receipt. This proves neither the
 * native message semantics nor its signature. For JWS/COSE/PAdES/CAdES/JAdES,
 * the actual native signature input, canonicalization and verifier remain
 * provider-specific. Never substitute a JSON reserialization.
 */
export async function bindNativeSignaturePayload(t,intent,payloadBytes,metadata){
 const d=unpackContract(t),p=prepareContractSignature(t,intent);
 must(p.profile!=="cgx-ed25519-bytes/1","EXTERNAL_PROFILE_REQUIRED");
 must(d.native_adapter!==null,"NATIVE_ADAPTER_REQUIRED");
 must(payloadBytes instanceof Uint8Array&&payloadBytes.length>0&&payloadBytes.length<=1048576,"NATIVE_PAYLOAD_BUDGET");
 must(exact(metadata,["profile","payload_ref","payload_sha256","intent_sha256","domain_ref","adapter_sha256"])&&
  metadata.profile===p.profile&&text(metadata.payload_ref)&&text(metadata.domain_ref)&&
  sha(metadata.payload_sha256)&&sha(metadata.intent_sha256)&&metadata.adapter_sha256===d.native_adapter[3],"NATIVE_BINDING_INVALID");
 const digest=await shaBytes(Uint8Array.from(payloadBytes));
 const intentDigest=await shaBytes(new TextEncoder().encode(JSON.stringify(p.intent_binding)));
 must(digest===metadata.payload_sha256&&intentDigest===metadata.intent_sha256,"NATIVE_BINDING_DIGEST_MISMATCH");
 return {schema:"CGX-NATIVE-SIGNATURE-PAYLOAD-BINDING/1",state:"EXACT_PAYLOAD_HASH_BOUND_REVIEW_ONLY",
  contract_ref:d.contract_ref,revision:d.revision,party_id:p.party_id,profile:p.profile,
  payload_ref:metadata.payload_ref,payload_sha256:digest,payload_bytes:payloadBytes.length,
  intent_sha256:intentDigest,domain_ref:metadata.domain_ref,adapter_sha256:metadata.adapter_sha256,
  payload_hash_verified:true,native_semantics_verified:false,native_domain_verified:false,
  signature_verified:false,key_binding_verified:false,challenge_freshness_verified:false,
  consent_verified:false,legal_validity_verified:false,execution_authorized:false,native_admission:false};
}
