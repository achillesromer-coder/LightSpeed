/** Native CGX node exchange / LS GO readiness SHAPE review.
 * No signature validation or provider I/O; real sender/receiver readback and policy
 * proof are exclusively owned by the authorised native CGX/LS host.
 */
export const HANDSHAKE_SCHEMA="CGX-BOOTSTRAP-HANDSHAKE-REVIEW/0.1";
const SHA=/^[a-f0-9]{64}$/i;
// Identity/nonce/transfer references must not carry log-spoofing controls.
const id=x=>typeof x==="string"&&x.length>0&&x.length<=256&&x===x.trim()&&
 !/[\u0000-\u001f\u007f-\u009f]/.test(x)&&
 !/[\p{Cf}\p{Zl}\p{Zp}\p{Cs}]/u.test(x);
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
// Invisible format controls (Cf), line/paragraph separators (Zl/Zp), and
// unpaired UTF-16 surrogates (Cs) are unsafe in portable transfer paths:
// they can spoof log boundaries or change when transcoded to UTF-8.
const safeRelativeTransferPath=path=>{
 // Source-only portable envelope: bound UTF-16 total length and per-component
 // UTF-8 bytes before any native Windows/POSIX containment or lease check.
 if(typeof path!=="string"||path.length>4096)return false;
 if(path.startsWith("/")||path.startsWith(".")||path.includes("..")||
    path.includes("\\")||/[:%<>"|?*\u007f-\u009f]/.test(path)||path!==path.normalize("NFC")||
    /[\p{Cf}\p{Zl}\p{Zp}\p{Cs}]/u.test(path))return false;
 return path.split("/").every(segment=>{
  if(!segment||segment==="."||segment===".."||segment.trim()!==segment||
     /[. ]$/.test(segment)||segment.length>255||
     new TextEncoder().encode(segment).length>255)return false;
  const stem=segment.split(".")[0];
  // CONIN$ and CONOUT$ are Windows console device endpoints, not transfer files.
  return !/^(?:CON|PRN|AUX|NUL|CONIN\$|CONOUT\$|COM[1-9\u00b9\u00b2\u00b3]|LPT[1-9\u00b9\u00b2\u00b3])$/i.test(stem);
 });
};
// Align the non-authorising child FileSpace SHAPE with the Windows host
// basename guard. This does not establish a unique Object_ID or native binding.
const safeChildFilespace=value=>
 typeof value==="string"&&id(value)&&value.length<=128&&value.endsWith(".cgx")&&
 !value.includes("/")&&!value.slice(0,-4).endsWith(" ")&&safeRelativeTransferPath(value);
const AUTHORITY="HOST_SIGNATURE_AND_DBR_NOT_VERIFIED_BY_PLANNER";
// Distinct source-review holds: a claimed key, request scope or nonce is not host proof.
const LEASE_BOUNDARY_HOLDS=Object.freeze([
 "ISSUER_ROOT_AUTHORITY_NOT_VERIFIED",
 "REQUEST_BOUND_OBJECT_TOOL_RESOURCE_SCOPE_NOT_VERIFIED",
 "LEASE_NONCE_CONSUMPTION_NOT_VERIFIED"
]);
export function planCGXHandshake({parent,child,lease,exchange=null,now=null}={}){
 if(!obj(parent)||!obj(child)||!obj(lease))return {status:"DENIED",reason:"MISSING_CONTEXT"};
 if(now!==null&&!validInstant(now))return {status:"DENIED",reason:"INVALID_NOW"};
 if(!safeChildFilespace(child.filespace))return {status:"DENIED",reason:"UNSAFE_CHILD_FILESPACE"};
 for(const x of [parent.object_id,parent.state_root,parent.dbr_root,child.object_id,child.filespace,child.parent_object_id,lease.lease_id,lease.target_object_id,lease.scope]){
  if(!id(x))return {status:"DENIED",reason:"INCOMPLETE_IDENTITY_OR_LEASE"};
 }
 if(!SHA.test(parent.state_root)||!SHA.test(parent.dbr_root))return {status:"DENIED",reason:"INVALID_ROOT_HASH"};
 // The parent and child must be distinct typed identities, not a self-edge.
 // A self-parented FileSpace cannot qualify even when its lease target agrees.
 if(child.object_id===parent.object_id)return {status:"DENIED",reason:"SELF_PARENT_CHILD_IDENTITY"};
 if(child.parent_object_id!==parent.object_id)return {status:"DENIED",reason:"CROSS_PARENT_CHILD"};
 if(lease.target_object_id!==child.object_id)return {status:"DENIED",reason:"LEASE_SUBJECT_MISMATCH"};
 if(!allowed.has(lease.scope))return {status:"DENIED",reason:"UNRECOGNISED_LEASE_SCOPE"};
 const holds=[AUTHORITY,...LEASE_BOUNDARY_HOLDS],facts={};
 if(!obj(lease.signer_ref)||!id(lease.signer_ref.key_id))holds.push("SIGNED_LEASE_PROVIDER_REQUIRED");
 if(!validInstant(lease.expires_utc)){holds.push("INVALID_LEASE_EXPIRY");}
 else if(now!==null){
  if(Date.parse(lease.expires_utc)<=Date.parse(now))holds.push("LEASE_EXPIRED");
 }
 if(exchange!==null){
  if(!obj(exchange))return {status:"DENIED",reason:"INVALID_EXCHANGE"};
  const required=["transfer_id","source_node_id","target_node_id","source_ref","source_sha256","size_bytes","target_root_id","target_relative_path","created_utc"];
  if(required.some(x=>exchange[x]===null||exchange[x]===undefined))return {status:"DENIED",reason:"MISSING_EXCHANGE_FIELD"};
  // Source-envelope chronology is shape data, never a provider timestamp attestation.
  if(!validInstant(exchange.created_utc))return {status:"DENIED",reason:"INVALID_TRANSFER_TIMESTAMP"};
  if(![exchange.transfer_id,exchange.source_node_id,exchange.target_node_id,exchange.source_ref,exchange.target_root_id].every(id)
  ||typeof exchange.target_relative_path!=="string"
  ||!SHA.test(exchange.source_sha256)||!Number.isSafeInteger(exchange.size_bytes)||exchange.size_bytes<0)
   return {status:"DENIED",reason:"INVALID_TRANSFER_ENVELOPE"};
  // Chronology is only a self-reported consistency check, never host time attestation.
  if(validInstant(lease.expires_utc)&&Date.parse(exchange.created_utc)>=Date.parse(lease.expires_utc))
   holds.push("TRANSFER_CREATED_AFTER_LEASE_EXPIRY");
  if(now!==null&&Date.parse(exchange.created_utc)>Date.parse(now))
   holds.push("FUTURE_TRANSFER_TIMESTAMP");
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


/**
 * Non-authorising ABI projection from the *separate* native execution lease
 * contract to the bootstrap handshake SHAPE review. No issuer verification,
 * clock attestation, nonce registry, host transport, DBR or tool invocation.
 * Explicit request binding is required; absent scope/budget is never wildcard.
 */
export const NATIVE_LEASE_ABI_REVIEW_SCHEMA="CGX-NATIVE-LEASE-BOOTSTRAP-ABI-REVIEW/0.1";
export function reviewNativeLeaseHandshakeABI({
 sourceSchema,nativeLease,parent,child,request,now
}={}){
 const deny=reason=>({schema:NATIVE_LEASE_ABI_REVIEW_SCHEMA,status:"DENIED",reason,
  may_execute:false,host_signature_verified:false,db_r_mutated:false});
 if(sourceSchema!=="CGX-EXECUTION-LEASE-CONTRACT/0.1")
  return deny("UNSUPPORTED_NATIVE_LEASE_ABI");
 if(!obj(nativeLease)||!obj(request)||!obj(parent)||!obj(child))
  return deny("MISSING_ABI_CONTEXT");
 if(!validInstant(now))return deny("INVALID_REVIEW_CLOCK");
 if(nativeLease.state!=="ACTIVE"||nativeLease.revocable!==true)
  return deny("NATIVE_LEASE_INACTIVE_OR_NONREVOCABLE");
 // The native contract requires an explicit governance phase and a phase
 // authority reference. This is only a syntactic gate: the referenced
 // authority still requires independent host resolution and verification.
 const phases=new Set(["PRE_LAUNCH","LAUNCH_TRANSITION",
  "DISTRIBUTED_OPERATION","SUCCESSION_OR_RECOVERY"]);
 if(!phases.has(nativeLease.authority_phase)||!id(nativeLease.authority_phase_ref))
  return deny("NATIVE_LEASE_AUTHORITY_PHASE_UNBOUND");
 if(![nativeLease.lease_id,nativeLease.issued_by,nativeLease.subject_agent,
      request.agent_id,request.object_id,request.tool_scope,request.domain,
      request.execution_depth,request.action_class,request.nonce].every(id))
  return deny("MISSING_REQUEST_BOUND_IDENTITY");
 if(nativeLease.subject_agent!==request.agent_id)
  return deny("NATIVE_LEASE_AGENT_MISMATCH");
 const scopes=nativeLease.scope;
 // The native 0.1 contract enumerates every understood scope axis.
 // An unknown declared restriction must not be silently ignored and reported
 // as request-bound; require an explicit versioned ABI mapping instead.
 const supportedScopeAxes=new Set([
  "task_ids","project_ids","object_ids","action_classes","tool_scopes",
  "resource_budgets","geographic_or_orbital_scope","configuration_ids"
 ]);
 if(obj(scopes)&&Reflect.ownKeys(scopes).some(k=>!supportedScopeAxes.has(k)))
  return deny("NATIVE_LEASE_SCOPE_AXIS_UNMAPPED");
 const includes=(xs,x)=>Array.isArray(xs)&&xs.length>0&&xs.length<=100&&xs.every(id)&&xs.includes(x);
 if(!obj(scopes)||!includes(scopes.object_ids,request.object_id)||
    !includes(scopes.tool_scopes,request.tool_scope)||
    !includes(scopes.action_classes,request.action_class)||
    !includes(nativeLease.domains,request.domain)||
    !includes(nativeLease.execution_depths,request.execution_depth))
  return deny("NATIVE_LEASE_REQUEST_SCOPE_MISMATCH");
 // The native contract also scopes task/project/configuration when declared.
 // Do not call a request bound merely because object/tool/action match while
 // another explicitly restricted native dimension was omitted or changed.
 for(const [scopeKey,requestKey] of [
  ["task_ids","task_id"],["project_ids","project_id"],
  ["configuration_ids","configuration_id"]]){
  if(Object.hasOwn(scopes,scopeKey)){
   const entries=scopes[scopeKey];
   if(!Array.isArray(entries)||entries.length>100||!entries.every(id)||
      (entries.length>0&&(!id(request[requestKey])||!entries.includes(request[requestKey]))))
    return deny("NATIVE_LEASE_CONTEXT_SCOPE_MISMATCH");
  }
 }
 // The native lease contract names geographic_or_orbital_scope but does not
 // define a portable typed frame/units/region containment ABI. The existing
 // native runtime validator also does not bind this axis. Never report a
 // request as scope-bound if either side declares spatial restrictions: a
 // host-qualified schema and independent frame-aware containment proof are
 // required first. This review adapter remains non-authorising regardless.
 if(Object.hasOwn(scopes,"geographic_or_orbital_scope")||
    Object.hasOwn(request,"geographic_or_orbital_scope"))
  return deny("NATIVE_LEASE_SPATIAL_SCOPE_UNMAPPED");
 // The native execution contract separately bounds cascade severity and specialist floors.
 // Source-review must not mark request scope bound while ignoring these axes.
 const cascadeRank={C0:0,C1:1,C2:2,C3:3,C4:4};
 const ceiling=nativeLease.max_cascade_class,requestedCascade=request.cascade_class;
 const allowedFloors=nativeLease.allowed_floors,plannedFloors=request.planned_floors;
 if(!Object.hasOwn(cascadeRank,ceiling)||!Object.hasOwn(cascadeRank,requestedCascade)||
    cascadeRank[requestedCascade]>cascadeRank[ceiling]||
    !Array.isArray(allowedFloors)||allowedFloors.length===0||allowedFloors.length>100||
    !allowedFloors.every(id)||
    !Array.isArray(plannedFloors)||plannedFloors.length===0||plannedFloors.length>100||
    !plannedFloors.every(id)||!plannedFloors.every(f=>allowedFloors.includes(f)))
  return deny("NATIVE_LEASE_CASCADE_OR_FLOOR_SCOPE_MISMATCH");
 if(request.object_id!==child.object_id)return deny("NATIVE_LEASE_CHILD_MISMATCH");
 if(!validInstant(nativeLease.valid_from)||!validInstant(nativeLease.valid_until)||
    Date.parse(nativeLease.valid_from)>=Date.parse(nativeLease.valid_until)||
    Date.parse(now)<Date.parse(nativeLease.valid_from)||
    Date.parse(now)>=Date.parse(nativeLease.valid_until))
  return deny("NATIVE_LEASE_TIME_WINDOW_INVALID");
 const budget=scopes.resource_budgets,usage=request.resource_usage;
 if(!obj(budget)||!obj(usage))return deny("NATIVE_RESOURCE_BUDGET_UNDECLARED");
 const keys=Object.keys(usage),budgetKeys=Object.keys(budget);
 const knownBudgetKeys=new Set(["compute_ms","memory_bytes","io_bytes","ops"]);
 // A projection must not ignore a malformed or unknown declared ceiling.
 // Only own, supported integer budgets can bind an explicit usage request.
 if(keys.length===0||keys.length>16||budgetKeys.length===0||budgetKeys.length>16||
    budgetKeys.some(k=>!knownBudgetKeys.has(k)||
      !Number.isSafeInteger(budget[k])||budget[k]<0)||
    keys.some(k=>!knownBudgetKeys.has(k)||!Object.hasOwn(budget,k)||
      !Number.isSafeInteger(usage[k])||usage[k]<0||usage[k]>budget[k]))
  return deny("NATIVE_RESOURCE_BUDGET_EXCEEDED_OR_UNBOUND");
 // A source-declared action-class subset is not enough if the lease class
 // forbids that action. These are explicitly understood high-risk verbs;
 // unknown classes remain unverified and must be resolved by the native ABI.
 const forbiddenActions={
  READ_ONLY:new Set(["execute","compute","simulate","digital_write","write","mutate",
   "publish","publication","external_action","physical_actuation"]),
  COMPUTE_ONLY:new Set(["digital_write","write","mutate","publish","publication",
   "external_action","physical_actuation"]),
  DIGITAL_WRITE:new Set(["publish","publication","external_action","physical_actuation"])
 };
 if(forbiddenActions[nativeLease.lease_class]?.has(request.action_class.toLowerCase()))
  return deny("NATIVE_LEASE_CLASS_ACTION_MISMATCH");
 const mapped={READ_ONLY:"read",COMPUTE_ONLY:"compute_only",
  DIGITAL_WRITE:"digital_write"}[nativeLease.lease_class];
 if(!mapped)return deny("NATIVE_LEASE_CLASS_UNSUPPORTED_BY_HANDSHAKE");
 // Intentionally do not forge signer_ref from issued_by or treat a nonce as consumed.
 const projectedLease={lease_id:nativeLease.lease_id,target_object_id:request.object_id,
  scope:mapped,expires_utc:nativeLease.valid_until,signer_ref:null};
 const shape=planCGXHandshake({parent,child,lease:projectedLease,now});
 if(shape.status==="DENIED")return deny("BOOTSTRAP_SHAPE_"+shape.reason);
 return {...shape,schema:NATIVE_LEASE_ABI_REVIEW_SCHEMA,
  source_schema:sourceSchema,status:"UNVERIFIED_SHAPE_REVIEW",
  holds:[...new Set([...shape.holds,"NATIVE_LEASE_ABI_TRANSLATION_NOT_AUTHORITY",
   "HOST_CLOCK_NOT_ATTESTED","REQUEST_NONCE_UNBOUND_TO_NATIVE_LEASE",
   "NATIVE_ISSUER_SIGNATURE_AND_REVOCATION_NOT_VERIFIED"])],
  issuer_claim:nativeLease.issued_by,subject_agent_claim:nativeLease.subject_agent,
  request_binding_reviewed:true,resource_budget_shape_reviewed:true,
  host_signature_verified:false,root_authority_verified:false,
  db_r_mutated:false,may_execute:false,may_publish:false};
}
