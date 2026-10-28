/**
 * Neo LS.cgx review of the EXISTING Python runtime status and startup-options
 * output shapes. Inputs are caller-supplied and UNTRUSTED. This function
 * cannot authenticate a host, verify installation, accept a DBR, or run setup.
 */
export const SCHEMA='CGX-LS-NATIVE-RUNTIME-READBACK-REVIEW/0.1';
const FLOOR_IDS=Object.freeze({
 Trinity:'Z+3_Trinity',Neo:'Z+2_Neo',Architect:'Z+1_Architect',
 TheConstruct:'Z0_TheConstruct',Morpheus:'Z-1_Morpheus',
 Oracle:'Z-2_Oracle',Smith:'Z-3_Smith',Merovingian:'Z-4_Merovingian'
});
const STATUS_KEYS=['schema','slot','source_head','managed_root','slot_root',
 'managed_marker','configured','profile','installed','python',
 'recent_receipts','authority'];
const STARTUP_KEYS=['root','source_files','global_options','floors'];
const REQUEST_KEYS=['family','object_id','capability_id','source_revision',
 'slot','intent','execution_requested','install_requested',
 'canonical_mutation_requested'];
const SECRET=/(?:^|[_-])(secret|token|password|credential|private[_-]?key|authorization|cookie|session|bearer|api[_-]?key)(?:$|[_-])/i;
const obj=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const keys=(x,allow)=>Object.keys(x).every(k=>allow.includes(k));
const id=x=>typeof x==='string'&&/^[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}$/.test(x)&&!x.includes('..');
const sha=x=>typeof x==='string'&&/^[a-f0-9]{40}$/i.test(x);
const txt=x=>typeof x==='string'&&x.length>0&&x.length<=512&&!/[\u0000-\u001f]/.test(x);
const hold=code=>Object.freeze({schema:SCHEMA,state:'HOLD',hold_code:code,
 runtime_installed_verified:false,host_authenticated:false,
 lease_verified:false,dbr_readback_verified:false,native_admitted:false,
 capability_installed:false,canonical_mutation:false,source_bytes_copied:0});
function unsafe(x,depth=0,seen=new Set()){
 if(depth>7)return true;
 if(!x||typeof x!=='object')return false;
 if(seen.has(x)||Object.keys(x).length>100||(Array.isArray(x)&&x.length>128))return true;
 seen.add(x);
 for(const [k,v] of Object.entries(x)){
  if(SECRET.test(k)||unsafe(v,depth+1,seen))return true;
 }
 seen.delete(x);return false;
}
function statusShape(s,slot){
 return obj(s)&&keys(s,STATUS_KEYS)&&
 s.schema==='LIGHTSPEED-RUNTIME-PRODUCTIZATION-STATUS/0.1'&&
 s.authority==='status-only'&&s.slot===slot&&sha(s.source_head)&&
 typeof s.managed_marker==='boolean'&&typeof s.configured==='boolean'&&
 typeof s.installed==='boolean'&&txt(s.managed_root)&&txt(s.slot_root)&&
 txt(s.python)&&Array.isArray(s.recent_receipts)&&s.recent_receipts.length<=20&&
 s.recent_receipts.every(txt)&&
 (s.profile==null||['core','api','data','validation','dev','desktop'].includes(s.profile));
}
function startupShape(p){
 if(!obj(p)||!keys(p,STARTUP_KEYS)||!txt(p.root)||
  !obj(p.source_files)||!obj(p.global_options)||!obj(p.floors)||
  Object.keys(p.floors).length!==8||
  Object.keys(p.floors).some(k=>!Object.hasOwn(FLOOR_IDS,k)))return false;
 for(const [name,canonical_id] of Object.entries(FLOOR_IDS)){
  const f=p.floors[name];
  if(!obj(f)||f.floor!==name||f.canonical_id!==canonical_id||
    typeof f.enabled!=='boolean'||typeof f.autostart!=='boolean')return false;
 }
 return typeof p.global_options.first_run_complete==='boolean'&&
  typeof p.global_options.show_splash_screen==='boolean'&&
  Number.isSafeInteger(p.global_options.max_concurrent_jobs)&&
  p.global_options.max_concurrent_jobs>=1&&
  Object.values(p.source_files).every(txt);
}
/** Syntax-only crosswalk; even a positive installed flag is NOT a host receipt. */
export function reviewNativeRuntimeReadback(input){
 if(!obj(input)||!obj(input.bootstrap_review)||!obj(input.runtime_status)||
  !obj(input.startup_profile)||!obj(input.request)||unsafe(input)||
  !keys(input,['bootstrap_review','runtime_status','startup_profile','request']))
  return hold('INVALID_OR_SENSITIVE_ENVELOPE');
 const {bootstrap_review:b,runtime_status:s,startup_profile:p,request:r}=input;
 if(b.schema!=='CGX-LS-UNIFIED-BOOTSTRAP-REVIEW/0.1'||
  b.state!=='HOST_NEGATIVE_TESTS_REQUIRED'||
  b.candidate_filespace!=='LS.cgx'||b.parent_filespace!=='EMASSC.cgx'||
  b.parent_ccc!=='Cognigrex.cgx:/ccc'||!id(b.candidate_object_id)||
  !id(b.capability_id)||!sha(b.load_source_revision)||
  b.runtime_owner!=='lightspeed_runtime.runtime_productization'||
  b.startup_owner!=='lightspeed_runtime.startup_options'||
  !sha(b.bootstrap_source_head)||!sha(b.bootstrap_source_blob)||
  ['native_admitted','capability_installed','host_authenticated',
   'lease_verified','dbr_readback_verified','canonical_mutation',
   'ls_go_enabled'].some(k=>b[k]!==false)||b.source_bytes_copied!==0)
  return hold('BOOTSTRAP_REVIEW_NOT_QUALIFIED');
 if(!obj(r)||!keys(r,REQUEST_KEYS)||r.family!=='LS.cgx'||
  r.object_id!==b.candidate_object_id||r.capability_id!==b.capability_id||
  r.source_revision!==b.load_source_revision||!id(r.slot)||
  r.intent!=='review'||r.execution_requested!==false||
  r.install_requested!==false||r.canonical_mutation_requested!==false)
  return hold('REQUEST_SCOPE_MISMATCH');
 if(!statusShape(s,r.slot))return hold('RUNTIME_STATUS_SHAPE_INVALID');
 if(!startupShape(p))return hold('STARTUP_PROFILE_SHAPE_INVALID');
 return Object.freeze({schema:SCHEMA,state:'AUTHENTICATED_HOST_READBACK_REQUIRED',
  candidate_filespace:'LS.cgx',candidate_object_id:b.candidate_object_id,
  capability_id:b.capability_id,source_revision:b.load_source_revision,
  runtime_status_shape_checked:true,startup_profile_shape_checked:true,
  runtime_installed_verified:false,host_authenticated:false,
  lease_verified:false,dbr_readback_verified:false,native_admitted:false,
  capability_installed:false,canonical_mutation:false,source_bytes_copied:0,
  required_host_checks:Object.freeze([
   'authenticate live Python/Windows host and owner ACL',
   'read current startup settings from canonical operator root',
   'read managed runtime status and validate current source and slot',
   'reject stale marker, missing interpreter, mismatched profile and forged receipt',
   'run issue #158 static privacy and issue #161 two-node negatives as applicable',
   'verify scoped signed lease, RootAuthority and independent DBR readback'
  ])});
}
