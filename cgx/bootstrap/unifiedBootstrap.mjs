/**
 * CGX first-run / returning-user setup preflight.
 * Pure planner only: cannot install, start a service, send a message, access a node,
 * create an Object_ID, alter a DBR, enable LS GO or publish.
 * Existing native CGX and LightSpeed components retain all execution authority.
 */
export const SCHEMA="CGX-UNIFIED-BOOTSTRAP-PLAN/0.1";
const FAMILIES=new Set(["Cognigrex.cgx","Romer.cgx","Eco.cgx","EMASSC.cgx","LS.cgx"]);
const STEPS=["discover","resume","identity","sources","load","tools","runtime","ls_go","handshake","verify","handoff"];
const text=x=>typeof x==="string"&&x.length>0&&x.length<=256&&!/[\u0000-\u001f]/.test(x)&&!/(?:^|[/\\])\.\.(?:[/\\]|$)/.test(x);
const isObj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const grant=x=>x===true;
const safeArray=(x)=>Array.isArray(x)&&x.length<=100&&x.every(text);
const requireProof=(v,flag,blockers)=>{if(!grant(v))blockers.push(flag)};
export function planCGXSetup(config={}){
 if(!isObj(config))return {state:"DENIED",reason:"INVALID_CONFIGURATION"};
 const {family,mode="first-run",intent="plan",device="desktop",profile="core",lsGORequested=false,
  offlinePreferred=true,sourceBytesPerChunk=60*1024*1024,receipt=null,
  observed={}}=config;
 if(!FAMILIES.has(family))return {state:"DENIED",reason:"UNKNOWN_FILESPACE"};
 if(!["first-run","resume","repair","upgrade"].includes(mode))return {state:"DENIED",reason:"UNKNOWN_SETUP_MODE"};
 if(!["plan","inspect"].includes(intent))return {state:"DENIED",reason:"EXECUTION_NOT_AVAILABLE_IN_PLAN"};
 if(!["desktop","mobile","browser","server"].includes(device))return {state:"DENIED",reason:"UNSUPPORTED_DEVICE"};
 if(!["core","api","data","validation","dev","desktop"].includes(profile))return {state:"DENIED",reason:"UNKNOWN_RUNTIME_PROFILE"};
 if(!Number.isSafeInteger(sourceBytesPerChunk)||sourceBytesPerChunk<1||sourceBytesPerChunk>60*1024*1024)
  return {state:"DENIED",reason:"SOURCE_SEGMENT_TOO_LARGE"};
 if(!isObj(observed))return {state:"DENIED",reason:"INVALID_OBSERVATIONS"};
 if(receipt!==null&&(!isObj(receipt)||!text(receipt.receipt_id)||!text(receipt.family)||receipt.family!==family))
  return {state:"DENIED",reason:"RECEIPT_SCOPE_MISMATCH"};
 const mandatory=[];
 requireProof(observed.hostReachable,"HOST_NOT_CONNECTED",mandatory);
 requireProof(observed.acceptedParent,"PARENT_ROOT_UNVERIFIED",mandatory);
 requireProof(observed.acceptedFamily,"CHILD_ADMISSION_UNVERIFIED",mandatory);
 requireProof(observed.exactObjectId,"EXACT_OBJECT_ID_UNVERIFIED",mandatory);
 requireProof(observed.ownerAcl,"OWNER_ACL_UNVERIFIED",mandatory);
 requireProof(observed.dbrReadback,"DBR_READBACK_UNVERIFIED",mandatory);
 requireProof(observed.signedLease,"SIGNED_LEASE_UNVERIFIED",mandatory);
 const optional=[];
 if(lsGORequested){
  requireProof(observed.privateAssetBoundaryVerified,"ISSUE_158_PRIVATE_ASSETS_HOLD",optional);
  requireProof(observed.familyUiBindingVerified,"GREX_UI_BINDING_UNVERIFIED",optional);
 }
 if(observed.nodeExchangeRequested===true)requireProof(observed.twoNodeProof,"ISSUE_161_TWO_NODE_HOLD",optional);
 if(!grant(observed.loadAliasVerified))optional.push("LOAD_EXISTING_IDENTITY_NOT_VERIFIED");
 if(!grant(observed.sourceRightsVerified))optional.push("PROVIDER_SOURCE_RIGHTS_NOT_VERIFIED");
 const requestedLSGO=!!lsGORequested;
 const last=(receipt&&safeArray(receipt.completed_steps))?new Set(receipt.completed_steps.filter(x=>STEPS.includes(x))):new Set();
 const changed=grant(observed.sourceChanged)||grant(observed.configChanged)||grant(observed.authorityChanged);
 const reusable=mode!=="first-run"&&!!receipt&&!changed?last:new Set();
 const stepPlans=STEPS.map(id=>({
  id,status:reusable.has(id)?"RECHECK_PRIOR_RECEIPT":"PREFLIGHT_REQUIRED",
  canonical_mutation:false,auto_run:false
 }));
 return {
  schema:SCHEMA,state:"REVIEW_ONLY",family,mode,device,runtime_profile:profile,
  source_chunk_limit:sourceBytesPerChunk,offline_minimum:offlinePreferred!==false,
  existing_runtime:{status_owner:"lightspeed_runtime.runtime_productization",settings_owner:"lightspeed_runtime.startup_options"},
  library:{name:"LOAD.cgx",bind:"EXISTING_IDENTITY_ONLY",install:false,network_hydration:false},
  ls_go:{product:"Grex-scoped LS GO",requested:requestedLSGO,enabled:false,
    ready_for_authenticated_host_preflight:requestedLSGO&&mandatory.length===0&&optional.filter(x=>x.startsWith("ISSUE_158")||x.startsWith("GREX_UI")).length===0,
    separate_product:"UniSpace",actual_toggle_write:false},
  handshake:{status:mandatory.length?"BLOCKED_PENDING_PROOF":"PREPARED_FOR_HOST_NEGATIVE_TESTS",
    observed_receipt_reuse:!!receipt&&!changed,node_transport:false,requires_two_node_when_requested:true,
    proposed_receipt_fields:["node_id","current_root","current_dbr_root","lease_scope","expiry","request_id","source_hash","host_readback"]},
  steps:stepPlans,duplicate_wizard_authority:false,independent_host_acceptance:false,
  blockers:[...new Set([...mandatory,...optional])],
  decisions_required:[],runtime_installed:false,source_ingested:false,
  canonical_accepted:false,ls_go_enabled:false,published:false,website_deployed:false,
  user_guidance:mandatory.length?"Continue read-only source reconciliation until accepted native host and family root are verified.":"Run actual host preflight with signed policy, independent tests, and current DBR readback before any apply."
 };
}
export function planOngoingSetup({family,current,previous=null,changes=[]}={}){
 if(!FAMILIES.has(family)||!isObj(current)||!(previous===null||isObj(previous))||!safeArray(changes))
  return {state:"DENIED",reason:"INVALID_RESUME_CONTEXT"};
 const restart=changes.some(x=>["root","authority","identity","rights","network","lease","runtime"].includes(x));
 return {schema:"CGX-ONGOING-SETUP-PLAN/0.1",state:"READ_ONLY",
  family,mode:restart?"REVERIFY_AUTHORITY":"INCREMENTAL_CHECK",
  requested_changes:changes,run_wizard_from_scratch:false,
  recheck:["current signed scope","parent identity and DBR","installed vs registered capabilities",
  "changed source revisions/hashes","LOAD hydration cache validity","per-child LS GO/UI binding"],
  mutation:false,source_copy:false,delete:false,install:false};
}
