/**
 * Neo LS.cgx crosswalk for unified bootstrap PR #206 and the reviewed LOAD
 * semantic envelope. Pure source-review validation: never a native host proof.
 * Source pins are selectors, not signatures or installation receipts.
 */
export const SCHEMA='CGX-LS-UNIFIED-BOOTSTRAP-REVIEW/0.1';
const HEAD='34f45718c13a1667bdb49fb6aea6736f4bf703eb';
const BLOB='dde0600c354799dbb428183c83ece7403b933b45';
const FIELDS=['native_admitted','capability_installed','host_authenticated',
 'lease_verified','dbr_readback_verified','solver_invoked','rendered',
 'hydration_performed','canonical_mutation','network_fetch'];
const STEPS=['discover','resume','identity','sources','load','tools','runtime',
 'ls_go','handshake','verify','handoff'];
const obj=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const ident=x=>typeof x==='string'&&/^[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}$/.test(x)&&!x.includes('..');
const held=code=>Object.freeze({schema:SCHEMA,state:'HOLD',hold_code:code,
 native_admitted:false,capability_installed:false,host_authenticated:false,
 lease_verified:false,dbr_readback_verified:false,canonical_mutation:false,
 source_bytes_copied:0});
const sensitive=/(?:^|[_-])(secret|token|password|credential|private[_-]?key|authorization|cookie|session|bearer|api[_-]?key)(?:$|[_-])/i;
function unsafe(v,depth=0,seen=new Set()){
 if(depth>7)return true;
 if(!v||typeof v!=='object')return false;
 if(seen.has(v)||Object.keys(v).length>100)return true;
 seen.add(v);
 for(const [k,x] of Object.entries(v))if(sensitive.test(k)||unsafe(x,depth+1,seen))return true;
 seen.delete(v);return false;
}
export function reviewUnifiedBootstrapBinding(input){
 if(!obj(input)||!obj(input.source_pin)||!obj(input.bootstrap_plan)||
    !obj(input.semantic_review)||!obj(input.request)||unsafe(input))
    return held('INVALID_OR_SENSITIVE_ENVELOPE');
 if(['host_claim','signed_lease','dbr_receipt','native_receipt','host_transport']
    .some(k=>Object.hasOwn(input,k)))return held('UNTRUSTED_HOST_ASSERTION');
 const {source_pin:p,bootstrap_plan:b,semantic_review:s,request:r}=input;
 if(p.repository!=='achillesromer-coder/LightSpeed'||p.pr!==206||
    p.head_sha!==HEAD||p.bootstrap_blob_sha!==BLOB||
    p.provider_verified!==false||p.native_admitted!==false)
    return held('BOOTSTRAP_SOURCE_PIN_UNQUALIFIED');
 if(b.schema!=='CGX-UNIFIED-BOOTSTRAP-PLAN/0.1'||b.state!=='REVIEW_ONLY'||
    b.family!=='LS.cgx'||b.existing_runtime?.status_owner!=='lightspeed_runtime.runtime_productization'||
    b.existing_runtime?.settings_owner!=='lightspeed_runtime.startup_options'||
    b.library?.name!=='LOAD.cgx'||b.library?.bind!=='EXISTING_IDENTITY_ONLY'||
    b.library?.install!==false||b.library?.network_hydration!==false||
    b.ls_go?.enabled!==false||b.ls_go?.actual_toggle_write!==false||
    b.ls_go?.separate_product!=='UniSpace'||b.duplicate_wizard_authority!==false||
    b.independent_host_acceptance!==false||b.runtime_installed!==false||
    b.source_ingested!==false||b.canonical_accepted!==false||
    b.ls_go_enabled!==false||b.published!==false||b.website_deployed!==false||
    !Array.isArray(b.steps)||b.steps.length!==STEPS.length||
    b.steps.some((x,i)=>!obj(x)||x.id!==STEPS[i]||x.auto_run!==false||
      x.canonical_mutation!==false))
    return held('BOOTSTRAP_NOT_SOURCE_SAFE');
 if(s.schema!=='CGX-LS-LOAD-SEMANTIC-HOST-REVIEW/0.1'||
    s.state!=='HOST_REVALIDATION_REQUIRED'||s.target_filespace!=='LS.cgx'||
    s.parent_filespace!=='EMASSC.cgx'||s.parent_ccc!=='Cognigrex.cgx:/ccc'||
    !ident(s.candidate_object_id)||!ident(s.capability_id)||
    !/^[a-f0-9]{40}$/i.test(s.source_revision||'')||
    FIELDS.some(k=>s[k]!==false)||s.source_bytes_copied!==0||
    s.source_proof_independently_verified!==false||s.rights_verified!==false)
    return held('SEMANTIC_HOST_REVIEW_UNQUALIFIED');
 if(r.family!=='LS.cgx'||r.parent_filespace!=='EMASSC.cgx'||
    r.parent_ccc!=='Cognigrex.cgx:/ccc'||r.object_id!==s.candidate_object_id||
    r.capability_id!==s.capability_id||r.source_revision!==s.source_revision||
    r.intent!=='review'||r.execution_requested!==false||
    r.install_requested!==false||r.publish_requested!==false||
    r.network_permission!==false||r.canonical_mutation_requested!==false||
    r.max_transfer_bytes!==0)
    return held('CROSSWALK_SCOPE_OR_IDENTITY_MISMATCH');
 return Object.freeze({schema:SCHEMA,state:'HOST_NEGATIVE_TESTS_REQUIRED',
   candidate_filespace:'LS.cgx',parent_filespace:'EMASSC.cgx',
   parent_ccc:'Cognigrex.cgx:/ccc',candidate_object_id:r.object_id,
   capability_id:r.capability_id,bootstrap_source_head:HEAD,
   bootstrap_source_blob:BLOB,load_source_revision:s.source_revision,
   runtime_owner:b.existing_runtime.status_owner,
   startup_owner:b.existing_runtime.settings_owner,
   ls_go_requested:b.ls_go.requested===true,ls_go_enabled:false,
   native_admitted:false,capability_installed:false,host_authenticated:false,
   lease_verified:false,dbr_readback_verified:false,canonical_mutation:false,
   network_fetch:false,source_bytes_copied:0,
   required_host_checks:Object.freeze([
     'independent Git source and rights verification',
     'current accepted parent and child Object_ID plus ACL',
     'native startup and managed runtime status readback',
     'issue #158 unauthenticated static asset negative test',
     'issue #161 distinct two-node negative/positive acceptance if requested',
     'signed scoped host lease and independent DBR readback'
   ])});
}
