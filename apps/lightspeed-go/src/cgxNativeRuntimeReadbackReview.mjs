/**
 * Neo LS.cgx review of the EXISTING Python runtime status and startup-options
 * output shapes. Inputs are caller-supplied and UNTRUSTED. This function
 * cannot authenticate a host, verify installation, accept a DBR, or run setup.
 */
export const SCHEMA='CGX-LS-NATIVE-RUNTIME-READBACK-REVIEW/0.1';
const BOOTSTRAP_HEAD='f331ce56a70018550b92b9b4ce9dbebbf05a719d';
const BOOTSTRAP_BLOB='0d9bb63fa5d300e96150589f6bb01666f0bd8442';
const FLOOR_IDS=Object.freeze({
 Trinity:'Z+3_Trinity',Neo:'Z+2_Neo',Architect:'Z+1_Architect',
 TheConstruct:'Z0_TheConstruct',Morpheus:'Z-1_Morpheus',
 Oracle:'Z-2_Oracle',Smith:'Z-3_Smith',Merovingian:'Z-4_Merovingian'
});
const STATUS_KEYS=['schema','slot','source_head','managed_root','slot_root',
 'managed_marker','configured','profile','installed','python',
 'recent_receipts','authority'];
const STARTUP_KEYS=['root','source_files','global_options','floors'];
// Source: lightspeed_runtime.startup_options.read_startup_options (Python).
// Validate its optional fields without treating caller JSON as host evidence.
const GLOBAL_BOOLEAN_KEYS=['first_run_complete','show_splash_screen',
 'z_floor_dropdown_enabled','ollama_auto_start','web_server_auto_start',
 'db_auto_backup','db_vacuum_on_startup'];
const GLOBAL_KEYS=[...GLOBAL_BOOLEAN_KEYS,'max_concurrent_jobs','holospace_entry_policy'];
const FLOOR_KEYS=['floor','canonical_id','enabled','autostart',
 'port','responsibility','description'];
const REQUEST_KEYS=['family','object_id','capability_id','source_revision',
 'slot','intent','execution_requested','install_requested',
 'canonical_mutation_requested'];
// Exact output envelope from cgxUnifiedBootstrapReview.mjs; reject invented authority.
const BOOTSTRAP_KEYS=['schema','state','candidate_filespace','parent_filespace',
 'parent_ccc','candidate_object_id','capability_id','bootstrap_source_head',
 'bootstrap_source_blob','load_source_revision','runtime_owner','startup_owner',
 'ls_go_requested','ls_go_enabled','native_admitted','capability_installed',
 'host_authenticated','lease_verified','dbr_readback_verified',
 'canonical_mutation','network_fetch','source_bytes_copied',
 'required_host_checks'];
const SECRET=/(?:^|[_-])(secret|token|password|credential|private[_-]?key|authorization|cookie|session|bearer|api[_-]?key)(?:$|[_-])/i;
const obj=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const keys=(x,allow)=>Object.keys(x).every(k=>allow.includes(k));
const id=x=>typeof x==='string'&&/^[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}$/.test(x)&&!x.includes('..');
// Match runtime_productization.SLOT_RE exactly; an Object_ID is not a slot.
const slot=x=>typeof x==='string'&&/^[A-Za-z0-9][A-Za-z0-9_.-]{0,47}$/.test(x);
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
// Lexical consistency only. This does NOT attest that a path exists on a host.
function absolutePath(value){
 if(!txt(value))return null;
 // POSIX backslashes are literal filename bytes, not directory separators.
 // Reject rather than collapsing distinct paths into a forged match.
 if(value.startsWith('/')&&value.includes('\\'))return null;
 const p=value.replaceAll('\\','/');
 if(p.startsWith('//')||p.includes('//'))return null;
 const windows=/^[A-Za-z]:\//.test(p);
 if(!windows&&!p.startsWith('/'))return null;
 const segments=p.split('/').slice(1);
 if(segments.some(s=>s===''||s==='.'||s==='..'))return null;
 // Windows path aliases and alternate data streams must not qualify as receipt paths.
 // This is lexical rejection only; it does not prove canonical filesystem identity.
 // Win32 DOS device basenames are reserved even when followed by an extension.
 const winDevice=/^(?:CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³]|CONIN\$|CONOUT\$)(?:\.|$)/i;
 if(windows&&segments.some(s=>/[<>:"|?*]/.test(s)||/[. ]$/.test(s)||winDevice.test(s)))return null;
 return windows?p.toLowerCase():p;
}
// Python runtime_productization uses UTC strftime("%Y%m%dT%H%M%SZ").
 // Reject calendar-impossible receipt labels before any host attestation.
function validUTCReceiptStamp(stamp){
 if(!/^\d{8}T\d{6}Z$/.test(stamp))return false;
 const year=Number(stamp.slice(0,4)),month=Number(stamp.slice(4,6));
 const day=Number(stamp.slice(6,8)),hour=Number(stamp.slice(9,11));
 const minute=Number(stamp.slice(11,13)),second=Number(stamp.slice(13,15));
 const leap=year%4===0&&(year%100!==0||year%400===0);
 const days=[31,leap?29:28,31,30,31,30,31,31,30,31,30,31];
 return year>=1&&year<=9999&&month>=1&&month<=12&&
  day>=1&&day<=days[month-1]&&hour<=23&&minute<=59&&second<=59;
}
function statusPaths(s,slotName){
 const root=absolutePath(s.managed_root);
 const slotRoot=absolutePath(s.slot_root);
 const python=absolutePath(s.python);
 if(!root||!slotRoot||!python)return false;
 const win=root.length>=3&&root[1]===':'&&root[2]==='/';
 const name=win?slotName.toLowerCase():slotName;
 if(slotRoot!==root+'/'+name)return false;
 if(python!==slotRoot+'/'+(win?'venv/scripts/python.exe':'venv/Scripts/python.exe'))return false;
 const prefix=root+'/_receipts/'+name+'-';
 return s.recent_receipts.every(path=>{
  const p=absolutePath(path);
  if(p===null||!p.startsWith(prefix))return false;
  const match=/^(?:configure|rollback|install(?:-installer)?|update(?:-installer)?)-(\d{8}T\d{6}Z)\.json$/i.exec(p.slice(prefix.length));
  return match!==null&&validUTCReceiptStamp(match[1].toUpperCase());
 });
}
function statusShape(s,slot){
 return obj(s)&&keys(s,STATUS_KEYS)&&
 s.schema==='LIGHTSPEED-RUNTIME-PRODUCTIZATION-STATUS/0.1'&&
 s.authority==='status-only'&&s.slot===slot&&sha(s.source_head)&&
 typeof s.managed_marker==='boolean'&&typeof s.configured==='boolean'&&
 typeof s.installed==='boolean'&&txt(s.managed_root)&&txt(s.slot_root)&&
 txt(s.python)&&Array.isArray(s.recent_receipts)&&s.recent_receipts.length<=20&&
 s.recent_receipts.every(txt)&&statusPaths(s,slot)&&
 (s.profile==null||['core','api','data','validation','dev','desktop'].includes(s.profile));
}
// The existing startup_options._config_paths map, not arbitrary caller paths.
// Lexical comparison only: no host filesystem identity or existence proof.
const SOURCE_PATHS=Object.freeze({
 settings:'config/settings.json',lightspeed:'config/lightspeed_config.json',
 unified:'config/unified_config.json',
 host_runtime_policy:'config/host_runtime_policy.json',
 workspace_lanes:'config/workspace_lanes.json',
 launch_control:'config/launch_control.json',
 floor_stage_population:'Z Axis/Z-3_Smith/data/staging/floor_stage_population.json'
});
function sourceFilesShape(p){
 const root=absolutePath(p.root);
 if(!root||!obj(p.source_files)||
  Object.keys(p.source_files).length!==Object.keys(SOURCE_PATHS).length||
  !keys(p.source_files,Object.keys(SOURCE_PATHS)))return false;
 const win=root.length>=3&&root[1]===':'&&root[2]==='/';
 return Object.entries(SOURCE_PATHS).every(([name,relative])=>{
  const path=absolutePath(p.source_files[name]);
  return path!==null&&path===root+'/'+(win?relative.toLowerCase():relative);
 });
}
function startupShape(p){
 if(!obj(p)||!keys(p,STARTUP_KEYS)||!sourceFilesShape(p)||
  !obj(p.global_options)||!obj(p.floors)||
  Object.keys(p.floors).length!==8||
  Object.keys(p.floors).some(k=>!Object.hasOwn(FLOOR_IDS,k))||
  !keys(p.global_options,GLOBAL_KEYS)||
  !GLOBAL_BOOLEAN_KEYS.every(k=>!Object.hasOwn(p.global_options,k)||
   typeof p.global_options[k]==='boolean')||
  (Object.hasOwn(p.global_options,'holospace_entry_policy')&&
   !txt(p.global_options.holospace_entry_policy)))return false;
 for(const [name,canonical_id] of Object.entries(FLOOR_IDS)){
  const f=p.floors[name];
  if(!obj(f)||!keys(f,FLOOR_KEYS)||f.floor!==name||
    f.canonical_id!==canonical_id||typeof f.enabled!=='boolean'||
    typeof f.autostart!=='boolean'||
    (Object.hasOwn(f,'port')&&!(f.port==null||f.port===''||
      (Number.isInteger(f.port)&&f.port>=0&&f.port<=65535)||
      (typeof f.port==='string'&&/^[0-9]{1,5}$/.test(f.port)&&
       Number(f.port)<=65535)))||
    ['responsibility','description'].some(k=>Object.hasOwn(f,k)&&
      (typeof f[k]!=='string'||f[k].length>512||
       Array.from(f[k]).some(ch=>ch.charCodeAt(0)<32))))return false;
 }
 return typeof p.global_options.first_run_complete==='boolean'&&
  typeof p.global_options.show_splash_screen==='boolean'&&
  Number.isSafeInteger(p.global_options.max_concurrent_jobs)&&
  p.global_options.max_concurrent_jobs>=1&&
  p.global_options.max_concurrent_jobs<=64&&
  Object.values(p.source_files).every(txt);
}
/** Syntax-only crosswalk; even a positive installed flag is NOT a host receipt. */
export function reviewNativeRuntimeReadback(input){
 if(!obj(input)||!obj(input.bootstrap_review)||!obj(input.runtime_status)||
  !obj(input.startup_profile)||!obj(input.request)||unsafe(input)||
  !keys(input,['bootstrap_review','runtime_status','startup_profile','request']))
  return hold('INVALID_OR_SENSITIVE_ENVELOPE');
 const {bootstrap_review:b,runtime_status:s,startup_profile:p,request:r}=input;
 if(!keys(b,BOOTSTRAP_KEYS)||typeof b.ls_go_requested!=='boolean'||
  b.network_fetch!==false||!Array.isArray(b.required_host_checks)||
  b.required_host_checks.length<1||b.required_host_checks.length>20||
  !b.required_host_checks.every(txt)||
  b.schema!=='CGX-LS-UNIFIED-BOOTSTRAP-REVIEW/0.1'||
  b.state!=='HOST_NEGATIVE_TESTS_REQUIRED'||
  b.candidate_filespace!=='LS.cgx'||b.parent_filespace!=='EMASSC.cgx'||
  b.parent_ccc!=='Cognigrex.cgx:/ccc'||!id(b.candidate_object_id)||
  !id(b.capability_id)||!sha(b.load_source_revision)||
  b.runtime_owner!=='lightspeed_runtime.runtime_productization'||
  b.startup_owner!=='lightspeed_runtime.startup_options'||
  b.bootstrap_source_head!==BOOTSTRAP_HEAD||b.bootstrap_source_blob!==BOOTSTRAP_BLOB||
  ['native_admitted','capability_installed','host_authenticated',
   'lease_verified','dbr_readback_verified','canonical_mutation',
   'ls_go_enabled'].some(k=>b[k]!==false)||b.source_bytes_copied!==0)
  return hold('BOOTSTRAP_REVIEW_NOT_QUALIFIED');
 if(!obj(r)||!keys(r,REQUEST_KEYS)||r.family!=='LS.cgx'||
  r.object_id!==b.candidate_object_id||r.capability_id!==b.capability_id||
  r.source_revision!==b.load_source_revision||!slot(r.slot)||
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
