/**
 * CGX read-only batch planner / exact source verifier.
 * Input metadata is untrusted; plan never performs I/O, native writes, model training or minting.
 * Reuse existing Cognigrex/CCC registries and source envelopes for actual adoption.
 */
import {createHash} from 'node:crypto';

const SHA=/^[0-9a-f]{64}$/i;
const ID=/^[A-Za-z0-9][A-Za-z0-9_.:\/-]{0,127}$/;
const STATES=new Set(['KNOWN','REFERENCE','UNRESOLVED','NOT_HYDRATED','WITHHELD','NOT_APPLICABLE','UNINSTANTIATED']);
const OWNERS=new Set(['Cognigrex.cgx','Earth.cgx','Eco.cgx','Romer.cgx','EMASSC.cgx','LS.cgx','Raphael.cgx','LOAD.cgx','UniSpace']);
function need(b,why){if(!b)throw Error(why)}
export function stableJSON(x){
 function norm(v,depth){need(depth<=32,'CANONICAL_DEPTH');if(v===null||typeof v==='boolean'||typeof v==='string')return v;
  if(typeof v==='number'){need(Number.isFinite(v),'NONFINITE');return v}
  if(Array.isArray(v)){need(v.length<=10000,'ARRAY_BOUND');return v.map(y=>norm(y,depth+1))}
  need(v&&typeof v==='object'&&(Object.getPrototypeOf(v)===Object.prototype||Object.getPrototypeOf(v)===null),'INVALID_OBJECT');
  const keys=Object.keys(v);need(keys.length<=10000,'OBJECT_BOUND');const o={};for(const k of keys.sort()){need(k!=='__proto__'&&k!=='constructor'&&k!=='prototype','UNSAFE_KEY');o[k]=norm(v[k],depth+1)}return o;
 }
 return JSON.stringify(norm(x,0));
}
export const digest=x=>createHash('sha256').update(typeof x==='string'?Buffer.from(x):x).digest('hex');
export function verifyBytes(bytes,record){
 need(record&&typeof record==='object','INVALID_SOURCE');need(Buffer.isBuffer(bytes)||bytes instanceof Uint8Array,'BYTES_REQUIRED');
 need(Number.isSafeInteger(record.bytes)&&record.bytes>=0&&record.bytes<=128*1024*1024,'BYTES_BOUND');
 need(SHA.test(record.sha256),'MISSING_SOURCE_HASH');const data=Buffer.from(bytes);
 need(data.byteLength===record.bytes,'BYTE_COUNT_MISMATCH');need(digest(data)===record.sha256.toLowerCase(),'DIGEST_MISMATCH');
 return Object.freeze({status:'R0_BYTES_VERIFIED',sha256:record.sha256.toLowerCase(),bytes:record.bytes,authority:false});
}
export function t173(path){
 need(typeof path==='string'&&path.length<=16*4+15,'INVALID_ADDRESS');if(!path)return [];
 const parts=path.split('/');need(parts.length<=16,'ADDRESS_DEPTH');return parts.map(part=>{need(/^\d{3}$/.test(part),'ADDRESS_FORMAT');let v=Number(part);need(v>=1&&v<=173,'ADDRESS_RANGE_OR_174');return v});
}
function validateNode(n){
 need(n&&typeof n==='object'&&!Array.isArray(n),'NODE_OBJECT');need(ID.test(n.id||''),'NODE_ID');
 need(OWNERS.has(n.owner),'OWNER_IDENTITY');need(STATES.has(n.state),'UNKNOWN_STATE');
 need(Array.isArray(n.dependencies)&&n.dependencies.length<=32,'DEPENDENCIES_BOUND');
 need(new Set(n.dependencies).size===n.dependencies.length,'DUPLICATE_DEPENDENCY');
 for(const d of n.dependencies)need(ID.test(d),'DEPENDENCY_ID');
 need(n.access==='owner' || n.access==='public','ACCESS_CLASS');
 if(n.sha256!==null){need(SHA.test(n.sha256||''),'DIGEST_FORMAT');need(Number.isSafeInteger(n.bytes)&&n.bytes>=0,'BYTE_COUNT')} else need(n.state!=='KNOWN','KNOWN_MISSING_HASH');
 if(n.address!==null)t173(n.address);
 need(n.verified!==true || (n.sha256!==null && n.state==='KNOWN'),'INVALID_VERIFICATION_CLAIM');
 return n;
}
/** No direct loads: a bounded selection of registered content references in deterministic DAG order. */
export function plan(nodes,requested,{publicView=false,maxNodes=4096}={}){
 need(Array.isArray(nodes)&&nodes.length<=maxNodes&&nodes.length>0,'NODE_LIST_BOUND');
 need(Array.isArray(requested)&&requested.length>0&&requested.length<=maxNodes,'REQUEST_BOUND');
 const byId=new Map();for(const raw of nodes){const n=validateNode(raw);need(!byId.has(n.id),'DUPLICATE_SEMANTIC_ID');byId.set(n.id,n)}
 const visiting=new Set(),done=new Set(),order=[],holds=[],missing=[],blocked=new Set();
 function visit(id){need(ID.test(id),'REQUEST_ID');if(done.has(id))return;need(!visiting.has(id),'DEPENDENCY_CYCLE');const n=byId.get(id);if(!n){missing.push(id);return}
  visiting.add(id);for(const dep of n.dependencies)visit(dep);visiting.delete(id);done.add(id);
  if(n.access==='owner' && publicView){blocked.add(id);holds.push({id,reason:'PRIVATE_SOURCE_EXCLUDED'});return}
  if(n.dependencies.some(d=>blocked.has(d)||!byId.has(d))){blocked.add(id);holds.push({id,reason:'DEPENDENCY_UNAVAILABLE_OR_WITHHELD'});return}
  if(n.state!=='KNOWN'||!n.verified)holds.push({id,reason:n.verified?'UNRESOLVED_STATE':'UNVERIFIED_SOURCE'});
  order.push({id:n.id,owner:n.owner,state:n.state,sha256:n.sha256,bytes:n.bytes,access:n.access,address:n.address});
 }
 for(const id of requested)visit(id);
 const sourceHashes=new Map();for(const n of order)if(n.sha256)sourceHashes.set(n.sha256,(sourceHashes.get(n.sha256)||0)+1);
 const repeated=[...sourceHashes.values()].reduce((a,b)=>a+b-1,0);
 const result={schema:'CGX-FRACTAL-BATCH-PLAN/1',action:'REVIEW_ONLY',publicView,order,requested:[...new Set(requested)],holds,missing:[...new Set(missing)],repeated_exact_source_hash_refs:repeated,unique_source_hashes:sourceHashes.size,mutated:false,minted:false,model_weights_updated:false};
 return {...result,root_sha256:digest(stableJSON(result))};
}
export function reconcile(oldPlan,nextNodes,requested,options){
 need(oldPlan?.schema==='CGX-FRACTAL-BATCH-PLAN/1'&&SHA.test(oldPlan.root_sha256),'INVALID_BASE_PLAN');
 const {root_sha256,...oldBody}=oldPlan;need(digest(stableJSON(oldBody))===root_sha256,'BASE_ROOT_MISMATCH');
 const now=plan(nextNodes,requested,options),oldBy=new Map(oldPlan.order.map(x=>[x.id,x]));
 const nextBy=new Map(now.order.map(x=>[x.id,x]));const changed=[],added=[],deleted=[];
 for(const [id,x] of nextBy){let prev=oldBy.get(id);if(!prev)added.push(id);else if(stableJSON(prev)!==stableJSON(x))changed.push(id)}
 for(const id of oldBy.keys())if(!nextBy.has(id))deleted.push(id);
 return {status:'CANDIDATE_DIFF_ONLY',base_root:root_sha256,result_root:now.root_sha256,added,changed,deleted,remaining_holds:now.holds,missing:now.missing,automatic_commit:false,native_approval:false};
}
export function publicReceipt(planValue){
 need(planValue?.schema==='CGX-FRACTAL-BATCH-PLAN/1','INVALID_PLAN');
 const {root_sha256,...body}=planValue;need(digest(stableJSON(body))===root_sha256,'RECEIPT_ROOT_MISMATCH');
 return {schema:'CGX-BATCH-RECEIPT/1',root_sha256,planned_nodes:planValue.order.length,unique_sources:planValue.unique_source_hashes,reused_source_refs:planValue.repeated_exact_source_hash_refs,held:planValue.holds.length+planValue.missing.length,ready_for_native_admission:false,model_trained:false,public_release:false};
}
