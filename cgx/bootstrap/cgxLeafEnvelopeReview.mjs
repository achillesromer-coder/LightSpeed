/**
 * Source-only CGX minimal skeleton + content-addressed leaf planning.
 * No filesystem, network, issuer, signing, DBR, or public-release authority.
 */
import {createHash} from 'node:crypto';
export const SCHEMA='CGX-REVIEW-LEAF-ENVELOPE/0.1';
export const MAX_WORK_UNIT_BYTES=60*1024*1024;
const hex=/^[0-9a-f]{64}$/;
const validId=x=>typeof x==='string'&&x.length>0&&x.length<=192
  &&!/[\\\u0000-\u001f]/.test(x)&&!x.includes('..')&&/^[A-Za-z0-9][A-Za-z0-9._:\/-]*$/.test(x);
const digest=v=>createHash('sha256').update(v).digest('hex');
function stable(v){
 if(Array.isArray(v))return '['+v.map(stable).join(',')+']';
 if(v!==null&&typeof v==='object')return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+stable(v[k])).join(',')+'}';
 return JSON.stringify(v);
}
const denial=reason=>({state:'DENIED',reason,canonical_mutation:false,network_transfer:false});
export function verifyEnvelope(envelope){
 if(!envelope||envelope.state!=='REVIEW_ONLY'||!envelope.manifest||!hex.test(envelope.digest_sha256??''))return false;
 const m=envelope.manifest;
 return m.schema===SCHEMA&&Array.isArray(m.leaves)&&m.leaves.length>0
  &&m.leaves.every((x,i)=>!!x&&x.index===i&&hex.test(x.sha256)&&Number.isSafeInteger(x.bytes)&&x.bytes>=0)
  &&!!m.source&&hex.test(m.source.sha256)&&digest(stable(m))===envelope.digest_sha256;
}
export function buildReviewEnvelope({objectId,version,leaves,dependencies=[],rightsRef=null,aclRef=null}={}){
 if(!validId(objectId)||!validId(version))return denial('IDENTITY_OR_VERSION_INVALID');
 if(!Array.isArray(leaves)||leaves.length===0||leaves.length>1024||!leaves.every(Buffer.isBuffer))
  return denial('LEAF_BYTES_REQUIRED');
 const total=leaves.reduce((n,b)=>n+b.length,0);
 if(!Number.isSafeInteger(total)||total>MAX_WORK_UNIT_BYTES)return denial('SOURCE_WORK_UNIT_TOO_LARGE');
 if(!Array.isArray(dependencies)||dependencies.length>1024)return denial('DEPENDENCIES_INVALID');
 let deps=[];
 for(const dep of dependencies){
  if(!dep||!validId(dep.objectId)||!validId(dep.version)||!hex.test(dep.manifestSha256??''))
   return denial('DEPENDENCY_REQUIRES_EXACT_VERSION_AND_DIGEST');
  deps.push({object_id:dep.objectId,version:dep.version,manifest_sha256:dep.manifestSha256});
 }
 deps.sort((a,b)=>stable(a).localeCompare(stable(b),'en'));
 if(new Set(deps.map(d=>d.object_id+'@'+d.version)).size!==deps.length)
  return denial('DUPLICATE_DEPENDENCY');
 if(deps.some(d=>d.object_id===objectId))return denial('SELF_DEPENDENCY');
 const sourceHash=createHash('sha256');
 for(const leaf of leaves)sourceHash.update(leaf);
 const manifest={
  schema:SCHEMA,object_id:objectId,version,
  source:{sha256:sourceHash.digest('hex'),bytes:total},
  leaves:leaves.map((b,i)=>({index:i,sha256:digest(b),bytes:b.length})),
  dependencies:deps,
  rights_ref:typeof rightsRef==='string'&&rightsRef?rightsRef:null,
  acl_ref:typeof aclRef==='string'&&aclRef?aclRef:null
 };
 const bytes=Buffer.byteLength(stable(manifest));
 return {state:'REVIEW_ONLY',manifest,digest_sha256:digest(stable(manifest)),
  accounting:{manifest_bytes:bytes,source_bytes:total,model:'UNCOMPRESSED_SYNTHETIC_OR_ACTUAL_INPUT_ONLY'},
  canonical_mutation:false,network_transfer:false,source_deletion:false,native_mint:false,
  note:'Review-only reference; remote leaf retrieval and dependency DAG acceptance require separately authenticated provider and governance proof'};
}
export function planHydration(envelope,requestedIndexes,proof={}){
 if(!verifyEnvelope(envelope))return denial('ENVELOPE_HASH_INVALID');
 if(!Array.isArray(requestedIndexes)||requestedIndexes.length>1024||
    !requestedIndexes.every(i=>Number.isSafeInteger(i)&&i>=0&&i<envelope.manifest.leaves.length))
  return denial('LEAF_REQUEST_INVALID');
 if(new Set(requestedIndexes).size!==requestedIndexes.length)return denial('LEAF_REQUEST_DUPLICATE');
 const m=envelope.manifest;
 if(!m.rights_ref||!m.acl_ref||proof.rightsVerified!==true||proof.aclVerified!==true||proof.sourceHashCurrent!==true)
  return {state:'HOLD',reason:'RIGHTS_ACL_OR_SOURCE_PROOF_UNVERIFIED',canonical_mutation:false,network_transfer:false};
 return {state:'REQUEST_PLAN_ONLY',manifest_digest:envelope.digest_sha256,
  selected_leaves:requestedIndexes.map(i=>m.leaves[i]),requested_bytes:requestedIndexes.reduce((n,i)=>n+m.leaves[i].bytes,0),
  canonical_mutation:false,network_transfer:false,native_mint:false,
  note:'Caller assertions are not authenticated permissions; transport must independently validate each claim'};
}
export function verifyLeaf(envelope,index,bytes){
 if(!verifyEnvelope(envelope)||!Number.isSafeInteger(index)||!Buffer.isBuffer(bytes))return false;
 const leaf=envelope.manifest.leaves[index];
 return !!leaf&&bytes.length===leaf.bytes&&digest(bytes)===leaf.sha256;
}
export function verifyReconstruction(envelope,orderedLeaves){
 if(!verifyEnvelope(envelope)||!Array.isArray(orderedLeaves)||
    orderedLeaves.length!==envelope.manifest.leaves.length)return false;
 const d=createHash('sha256');let total=0;
 for(let i=0;i<orderedLeaves.length;i++){
  if(!verifyLeaf(envelope,i,orderedLeaves[i]))return false;
  total+=orderedLeaves[i].length;d.update(orderedLeaves[i]);
 }
 return total===envelope.manifest.source.bytes&&d.digest('hex')===envelope.manifest.source.sha256;
}
