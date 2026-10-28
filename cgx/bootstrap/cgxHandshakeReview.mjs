/** Native CGX node exchange / LS GO readiness SHAPE review.
 * No signature validation or provider I/O; real sender/receiver readback and policy
 * proof are exclusively owned by the authorised native CGX/LS host.
 */
export const HANDSHAKE_SCHEMA="CGX-BOOTSTRAP-HANDSHAKE-REVIEW/0.1";
const SHA=/^[a-f0-9]{64}$/i;
const id=x=>typeof x==="string"&&x.length>0&&x.length<=256&&!/[\u0000-\u001f]/.test(x);
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const allowed=new Set(["read","metadata","digital_write","compute_only"]);
const AUTHORITY="HOST_SIGNATURE_AND_DBR_NOT_VERIFIED_BY_PLANNER";
export function planCGXHandshake({parent,child,lease,exchange=null,now=null}={}){
 if(!obj(parent)||!obj(child)||!obj(lease))return {status:"DENIED",reason:"MISSING_CONTEXT"};
 for(const x of [parent.object_id,parent.state_root,parent.dbr_root,child.object_id,child.filespace,child.parent_object_id,lease.lease_id,lease.target_object_id,lease.scope]){
  if(!id(x))return {status:"DENIED",reason:"INCOMPLETE_IDENTITY_OR_LEASE"};
 }
 if(!SHA.test(parent.state_root)||!SHA.test(parent.dbr_root))return {status:"DENIED",reason:"INVALID_ROOT_HASH"};
 if(child.parent_object_id!==parent.object_id)return {status:"DENIED",reason:"CROSS_PARENT_CHILD"};
 if(lease.target_object_id!==child.object_id)return {status:"DENIED",reason:"LEASE_SUBJECT_MISMATCH"};
 if(!allowed.has(lease.scope))return {status:"DENIED",reason:"UNRECOGNISED_LEASE_SCOPE"};
 const holds=[AUTHORITY],facts={};
 if(!obj(lease.signer_ref)||!id(lease.signer_ref.key_id))holds.push("SIGNED_LEASE_PROVIDER_REQUIRED");
 if(!Number.isFinite(Date.parse(lease.expires_utc??""))){holds.push("INVALID_LEASE_EXPIRY");}
 else if(now!==null){
  if(!Number.isFinite(Date.parse(now)))return {status:"DENIED",reason:"INVALID_NOW"};
  if(Date.parse(lease.expires_utc)<=Date.parse(now))holds.push("LEASE_EXPIRED");
 }
 if(exchange!==null){
  if(!obj(exchange))return {status:"DENIED",reason:"INVALID_EXCHANGE"};
  const required=["transfer_id","source_node_id","target_node_id","source_ref","source_sha256","size_bytes","target_root_id","target_relative_path","created_utc"];
  if(required.some(x=>exchange[x]===null||exchange[x]===undefined))return {status:"DENIED",reason:"MISSING_EXCHANGE_FIELD"};
  if(![exchange.transfer_id,exchange.source_node_id,exchange.target_node_id,exchange.source_ref,exchange.target_root_id,exchange.target_relative_path].every(id)
  ||!SHA.test(exchange.source_sha256)||!Number.isSafeInteger(exchange.size_bytes)||exchange.size_bytes<0)
   return {status:"DENIED",reason:"INVALID_TRANSFER_ENVELOPE"};
  if(exchange.source_node_id===exchange.target_node_id)holds.push("DISTINCT_SECOND_NODE_NOT_PROVEN");
  if(exchange.source_node_id!==exchange.target_node_id)facts.distinct_node_ids_claimed=true;
  if(!exchange.receiver_receipt||exchange.receiver_receipt.sha256!==exchange.source_sha256||
      exchange.receiver_receipt.size_bytes!==exchange.size_bytes)holds.push("EXACT_RECEIVER_HASH_SIZE_READBACK_REQUIRED");
  else facts.hash_size_fields_match=true; // still not independent provider attestation
  if(exchange.target_relative_path.startsWith("/")||exchange.target_relative_path.includes("..")||
   exchange.target_relative_path.includes("\\")||exchange.target_relative_path.startsWith("."))return {status:"DENIED",reason:"UNSAFE_TRANSFER_TARGET"};
  if(exchange.size_bytes>60*1024*1024)holds.push("BOUNDED_TRANSFER_SEGMENT_REQUIRED");
 }
 return {
  schema:HANDSHAKE_SCHEMA,status:"UNVERIFIED_SHAPE_REVIEW",parent_object_id:parent.object_id,
  child_object_id:child.object_id,filespace:child.filespace,lease_scope:lease.scope,
  holds,reported_field_consistency:facts,host_signature_verified:false,
  source_node_authenticated:false,target_node_authenticated:false,
  root_authority_verified:false,receiver_readback_independently_verified:false,
  db_r_mutated:false,node_transfer_executed:false,
  ls_go_toggle_enabled:false,may_execute:false,may_publish:false,
  next_native_step:"Resolve true signed roots, lease and distinct node identity on the host. Verify provider receipt signature, exact hash/size and DBR readback in separate authenticated tests."
 };
}
