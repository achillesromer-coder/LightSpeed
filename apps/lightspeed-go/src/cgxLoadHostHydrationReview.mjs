/**
 * Neo/LS.cgx bridge for LOAD.cgx review envelopes. Source-only; never a host handshake.
 * The LOAD PR and LS GO PR are separate: this validates an explicitly pinned, caller-
 * supplied projection without importing LOAD as an installed module or fetching R0.
 * A host must independently verify Git blobs, accepted Object_ID, owner ACL, rights,
 * signed lease, native S92-compatible EMBED semantics and DBR readback before apply.
 */
export const LOAD_HOST_REVIEW_SCHEMA = 'CGX-LS-LOAD-HOST-HYDRATION-REVIEW/0.1';
const HEX40=/^[0-9a-f]{40}$/i, HEX64=/^[0-9a-f]{64}$/i;
const SAFE=/^[a-zA-Z0-9][a-zA-Z0-9._:/-]{0,199}$/;
const SECRET=/(?:^|[_-])(secret|token|password|credential|private[_-]?key|authorization|cookie|session|bearer|api[_-]?key)(?:$|[_-])/i;
const record=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const safe=x=>typeof x==='string'&&SAFE.test(x)&&!x.includes('..');
const hold=code=>Object.freeze({schema:LOAD_HOST_REVIEW_SCHEMA,state:'HOLD',hold_code:code,
 native_admitted:false,capability_installed:false,host_authenticated:false,
 owner_lease_verified:false,dbr_readback_verified:false,hydration_performed:false,
 network_fetch:false,canonical_mutation:false,source_bytes_copied:0});
function unsafe(x,depth=0,seen=new Set()){
 if(depth>6)return true;
 if(x===null||typeof x!=='object')return false;
 if(seen.has(x))return true;
 seen.add(x);
 const keys=Object.keys(x);
 if(keys.length>64)return true;
 for(const k of keys)if(SECRET.test(k)||unsafe(x[k],depth+1,seen))return true;
 seen.delete(x);return false;
}
const allFalse=(x,keys)=>keys.every(k=>x[k]===false);
const equality=(...values)=>values.every(x=>x===values[0]);
/**
 * @param {object} input - untrusted source-review envelopes, never a host proof.
 * @returns {object} a bounded metadata handshake *proposal*, not an execution grant.
 */
export function reviewCgxLoadHostHydration(input){
 if(!record(input)||!record(input.source_pin)||!record(input.mapping)||
    !record(input.feature_plan)||!record(input.scoped_plan)||
    !record(input.ccc_preflight)||!record(input.request))return hold('INVALID_ENVELOPES');
 if(unsafe(input))return hold('SENSITIVE_OR_UNBOUNDED_INPUT');
 const {source_pin:p,mapping:m,feature_plan:f,scoped_plan:s,ccc_preflight:c,request:r}=input;
 if(p.schema!=='LOAD-ALEXANDRIA-SOURCE-REGISTRY-PROJECTION/0.1'||
    p.state!=='GIT_SOURCE_ONLY_NOT_CANONICAL'||p.repository!=='achillesromer-coder/LightSpeed'||
    !HEX40.test(p.revision||'')||!HEX40.test(p.registry_blob||'')||
    p.native_accepted!==0||p.native_host_verified!==false||
    p.source_bodies_copied!==0)return hold('LOAD_SOURCE_PROOF_NOT_QUALIFIED');
 if(m.category!=='filespace_action'||m.source_key!=='load.hydrate'||
    m.source_registry!=='cgx/load_minimum/filespace_feature_registry.json'||
    !HEX40.test(m.source_git_blob||'')||
    m.admission!=='SOURCE_REGISTRY_ONLY'||m.installed_online!==false||
    !HEX40.test(r.expected_source_registry_blob||'')||
    m.source_git_blob.toLowerCase()!==r.expected_source_registry_blob.toLowerCase()||
    !HEX40.test(r.expected_load_registry_blob||'')||
    p.registry_blob.toLowerCase()!==r.expected_load_registry_blob.toLowerCase()||
    !HEX40.test(r.expected_load_revision||'')||
    p.revision.toLowerCase()!==r.expected_load_revision.toLowerCase())
    return hold('SOURCE_MAPPING_OR_PIN_MISMATCH');
 if(f.schema!=='CGX-UNISPACE-FILESPACE-FEATURE-PLAN/0.1'||
    f.action!=='load.hydrate'||f.status!=='REVIEW_ONLY'||
    !record(f.target)||f.target.kind!=='filespace'||
    f.target.fileSpace!=='LS.cgx'||f.target.parentFileSpace!=='EMASSC.cgx'||
    !safe(f.target.owner)||!safe(f.target.objectId)||
    !['minimal','offline'].includes(f.requestedHydration)||
    !['TRACK','REFERENCE'].includes(f.requestedMode)||
    !Number.isSafeInteger(f.sourceByteCount)||f.sourceByteCount!==0||
    !Array.isArray(f.blockers)||f.blockers.length!==0||
    !allFalse(f,['sourceCopied','canonicalMutation','networkFetch','install','execute','publish']))
    return hold('FEATURE_PLAN_NOT_SOURCE_SAFE');
 if(s.schema!=='LOAD-SCOPED-FILESPACE-PLAN/0.1'||
    s.state!=='HOST_PREFLIGHT_REQUIRED'||!record(s.target)||
    !equality(s.target.fileSpace,f.target.fileSpace,'LS.cgx')||
    !equality(s.target.owner,f.target.owner)||
    !equality(s.target.objectId,f.target.objectId)||
    s.source_metadata_only!==true||s.external_fetch!==false||
    s.source_bodies_copied!==0||s.created_object_ids!==0||
    s.ccc_installed!==false||s.dbr_mutated!==false)
    return hold('SCOPED_HYDRATION_PLAN_INVALID');
 if(c.schema!=='CGX-CCC-MOBILE-SOURCE-GATE/0.1'||c.state!=='PLAN_ONLY'||
    c.filespace!=='LS.cgx'||c.parent_filespace!=='EMASSC.cgx'||
    c.ccc_location!=='Cognigrex.cgx:/ccc'||
    c.candidate_abi!=='CGX-CCC-METADATA-PLAN/0.1'||
    !/^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/.test(c.candidate_version||'')||
    !safe(c.capability_id)||!HEX40.test(c.source_revision||'')||
    !HEX40.test(c.source_git_blob_sha||'')||!HEX64.test(c.source_content_sha256||'')||
    !allFalse(c,['source_registry_independently_verified','source_rights_verified',
      'abi_conformance_verified','owner_authorized','provider_readback_authenticated',
      'native_admitted','capability_installed','execution_performed','canonical_mutation',
      'public_publish_authorized']))
    return hold('CCC_REVIEW_GATE_INVALID');
 if(r.mode!=='metadata_only'||r.requested_hydration!=='minimal'||
    r.operation!=='load.hydrate'||r.owner!==f.target.owner||
    r.object_id!==f.target.objectId||r.capability_id!==c.capability_id||
    !Number.isSafeInteger(r.max_transfer_bytes)||r.max_transfer_bytes<0||
    r.max_transfer_bytes>60*1024*1024||
    r.max_transfer_bytes!==0||
    r.network_permission!==false||r.execution_requested!==false||
    r.install_requested!==false||r.publish_requested!==false||
    r.canonical_mutation_requested!==false)
    return hold('REQUEST_EXCEEDS_REVIEW_SCOPE');
 // A caller-provided host assertion is never a verified host lease or DBR.
 if(input.host_claim!==undefined&&input.host_claim!==null){
  if(!record(input.host_claim)||unsafe(input.host_claim)||
     input.host_claim.object_id!==r.object_id||
     input.host_claim.capability_id!==r.capability_id||
     input.host_claim.load_revision!==p.revision)
    return hold('UNTRUSTED_OR_MISMATCHED_HOST_CLAIM');
 }
 return Object.freeze({
  schema:LOAD_HOST_REVIEW_SCHEMA,state:'HOST_HANDSHAKE_REQUIRED',
  target_filespace:'LS.cgx',parent_filespace:'EMASSC.cgx',
  parent_ccc:'Cognigrex.cgx:/ccc',candidate_object_id:r.object_id,
  source_key:m.source_key,source_registry_blob:p.registry_blob.toLowerCase(),
  source_mapping_blob:m.source_git_blob.toLowerCase(),
  source_revision:p.revision.toLowerCase(),capability_id:c.capability_id,
  requested_hydration:'minimal',requested_composition:f.requestedMode,
  source_proof_independently_verified:false,source_rights_verified:false,
  native_admitted:false,capability_installed:false,host_authenticated:false,
  owner_lease_verified:false,dbr_readback_verified:false,hydration_performed:false,
  network_fetch:false,canonical_mutation:false,source_bytes_copied:0,
  required_host_checks:Object.freeze([
   'authenticated provider exact revision/blob readback',
   'current accepted S92/parent Object_ID and alias collision resolution',
   'source licence/rights and target owner ACL',
   'native CCC version/ABI and capability registration',
   'signed host lease and permitted scope; independent DBR and receiver readback'
  ]),
 });
}
