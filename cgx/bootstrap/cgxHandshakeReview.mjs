/** Native CGX node exchange / LS GO readiness SHAPE review.
 * No signature validation or provider I/O; real sender/receiver readback and policy
 * proof are exclusively owned by the authorised native CGX/LS host.
 */
export const HANDSHAKE_SCHEMA="CGX-BOOTSTRAP-HANDSHAKE-REVIEW/0.1";
const SHA=/^[a-f0-9]{64}$/i;
const id=x=>typeof x==="string"&&x.length>0&&x.length<=256&&!/[\u0000-\u001f]/.test(x);
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const allowed=new Set(["read","metadata","digital_write","compute_only"]);
// Calendar-valid, offset-aware timestamps only. Date.parse alone normalises
// impossible days (e.g. February 30) and cannot qualify source chronology.
const ISO_INSTANT=/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(Z|[+-]\d{2}:\d{2})$/;
const validInstant=value=>{
 if(typeof value!=="string")return false;
 const m=ISO_INSTANT.exec(value);
 if(!m)return false;
 const year=Number(m[1]),month=Number(m[2]),day=Number(m[3]);
 const hour=Number(m[4]),minute=Number(m[5]),second=Number(m[6]);
 const leap=year%4===0&&(year%100!==0||year%400===0);
 const days=[31,leap?29:28,31,30,31,30,31,31,30,31,30,31];
 if(month<1||month>12||day<1||day>days[month-1]||hour>23||minute>59||second>59)return false;
 const zone=m[7];
 if(zone!=="Z"){
  const offsetHour=Number(zone.slice(1,3)),offsetMinute=Number(zone.slice(4,6));
  if(offsetHour>14||offsetMinute>59||(offsetHour===14&&offsetMinute!==0))return false;
 }
 return Number.isFinite(Date.parse(value));
};
// Portable shape review only; host must still resolve and attest final containment.
// Reject aliases that Windows, POSIX or Unicode normalization can collapse.
const safeRelativeTransferPath=path=>{
 if(path.startsWith("/")||path.startsWith(".")||path.includes("..")||
    path.includes("\\")||/[:%<>"|?*\u007f-\u009f]/.test(path)||path!==path.normalize("NFC")||
    /[\u202a-\u202e\u2066-\u2069]/.test(path))return false;
 return path.split("/").every(segment=>{
  if(!segment||segment==="."||segment===".."||segment.trim()!==segment||
     /[. ]$/.test(segment))return false;
  const stem=segment.split(".")[0];
  return !/^(?:CON|PRN|AUX|NUL|COM[1-9\u00b9\u00b2\u00b3]|LPT[1-9\u00b9\u00b2\u00b3])$/i.test(stem);
 });
};
const AUTHORITY="HOST_SIGNATURE_AND_DBR_NOT_VERIFIED_BY_PLANNER";
// Distinct source-review holds: a claimed key, request scope or nonce is not host proof.
const LEASE_BOUNDARY_HOLDS=Object.freeze([
 "ISSUER_ROOT_AUTHORITY_NOT_VERIFIED",
 "REQUEST_BOUND_OBJECT_TOOL_RESOURCE_SCOPE_NOT_VERIFIED",
 "LEASE_NONCE_CONSUMPTION_NOT_VERIFIED"
]);
export function planCGXHandshake({parent,child,lease,exchange=null,now=null}={}){
 if(!obj(parent)||!obj(child)||!obj(lease))return {status:"DENIED",reason:"MISSING_CONTEXT"};
 for(const x of [parent.object_id,parent.state_root,parent.dbr_root,child.object_id,child.filespace,child.parent_object_id,lease.lease_id,lease.target_object_id,lease.scope]){
  if(!id(x))return {status:"DENIED",reason:"INCOMPLETE_IDENTITY_OR_LEASE"};
 }
 if(!SHA.test(parent.state_root)||!SHA.test(parent.dbr_root))return {status:"DENIED",reason:"INVALID_ROOT_HASH"};
 if(child.parent_object_id!==parent.object_id)return {status:"DENIED",reason:"CROSS_PARENT_CHILD"};
 if(lease.target_object_id!==child.object_id)return {status:"DENIED",reason:"LEASE_SUBJECT_MISMATCH"};
 if(!allowed.has(lease.scope))return {status:"DENIED",reason:"UNRECOGNISED_LEASE_SCOPE"};
 const holds=[AUTHORITY,...LEASE_BOUNDARY_HOLDS],facts={};
 if(!obj(lease.signer_ref)||!id(lease.signer_ref.key_id))holds.push("SIGNED_LEASE_PROVIDER_REQUIRED");
 if(!validInstant(lease.expires_utc)){holds.push("INVALID_LEASE_EXPIRY");}
 else if(now!==null){
  if(!validInstant(now))return {status:"DENIED",reason:"INVALID_NOW"};
  if(Date.parse(lease.expires_utc)<=Date.parse(now))holds.push("LEASE_EXPIRED");
 }
 if(exchange!==null){
  if(!obj(exchange))return {status:"DENIED",reason:"INVALID_EXCHANGE"};
  const required=["transfer_id","source_node_id","target_node_id","source_ref","source_sha256","size_bytes","target_root_id","target_relative_path","created_utc"];
  if(required.some(x=>exchange[x]===null||exchange[x]===undefined))return {status:"DENIED",reason:"MISSING_EXCHANGE_FIELD"};
  // Source-envelope chronology is shape data, never a provider timestamp attestation.
  if(!validInstant(exchange.created_utc))return {status:"DENIED",reason:"INVALID_TRANSFER_TIMESTAMP"};
  if(![exchange.transfer_id,exchange.source_node_id,exchange.target_node_id,exchange.source_ref,exchange.target_root_id,exchange.target_relative_path].every(id)
  ||!SHA.test(exchange.source_sha256)||!Number.isSafeInteger(exchange.size_bytes)||exchange.size_bytes<0)
   return {status:"DENIED",reason:"INVALID_TRANSFER_ENVELOPE"};
  if(exchange.source_node_id===exchange.target_node_id)holds.push("DISTINCT_SECOND_NODE_NOT_PROVEN");
  if(exchange.source_node_id!==exchange.target_node_id)facts.distinct_node_ids_claimed=true;
  if(!exchange.receiver_receipt||exchange.receiver_receipt.sha256!==exchange.source_sha256||
      exchange.receiver_receipt.size_bytes!==exchange.size_bytes)holds.push("EXACT_RECEIVER_HASH_SIZE_READBACK_REQUIRED");
  else facts.hash_size_fields_match=true; // still not independent provider attestation
  // Reject Windows alternate-data-stream colons and encoded path ambiguity, even
  // when the relative path is reviewed on a non-Windows machine. Host still owns
  // final canonical path resolution and containment checks before any write.
  if(!safeRelativeTransferPath(exchange.target_relative_path))
   return {status:"DENIED",reason:"UNSAFE_TRANSFER_TARGET"};
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
  next_native_step:"On the authorised host verify issuer signature, RootAuthority/revocation, request-bound object/tool/resource scope and atomic nonce consumption. Separately authenticate distinct nodes, exact receiver hash/size and signed DBR readback."
 };
}
