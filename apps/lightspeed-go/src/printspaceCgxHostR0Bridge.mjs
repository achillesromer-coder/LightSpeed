/**
 * PrintSpace CGX 80-facet FileSpace -> EXISTING UniSpace R0/LOAD review gates.
 * This is a Node-side metadata adapter. No network, source bytes, credentials,
 * private LOAD/H1-H4, real machine control, rights approval or native DBR.
 * Caller-supplied SHA pointers / rights are candidates, not trusted readback.
 */
import {createHash} from 'node:crypto';
import {projectCgxHostObjectContextGate} from './cgxHostObjectContextGate.mjs';
import {projectUniSpaceLoadLens} from './cgxLoadLibraryLensPlan.mjs';

export const SCHEMA = 'CGX-PRINTSPACE-UNISPACE-R0-CROSSWALK/0.1';
const SRC = 'CGX-PRINTSPACE-UNISPACE-HOST-R0-PREFLIGHT/0.1';
const HEX = /^sha256:[0-9a-f]{64}$/;
const HEX64 = /^[0-9a-f]{64}$/;
const BAD = new Set(['token','password','cookie','authorization','secret',
  'api_key','source_bytes','cad_source_bytes','material_source_bytes',
  'source_locator','private_path','file_path','url','lease','dbr_root',
  'source_registry','source_url','asset_path','asset_url','private_payload',
  'signed_dbr','native_dbr_receipt','session_token',
  'machine_command','toolpath','gcode','signed_licence']);
const obj = x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
function canonical(value, depth=0){
  if(depth>16)throw Error('CANONICAL_DEPTH');
  if(Array.isArray(value))return value.map(v=>canonical(v,depth+1));
  if(obj(value)){
    const out={};for(const k of Object.keys(value).sort()){
      if(BAD.has(k.toLowerCase()))throw Error('PRIVATE_AUTHORITY_INPUT');
      out[k]=canonical(value[k],depth+1);
    }
    return out;
  }
  if(value===null||typeof value==='string'||typeof value==='boolean'
     ||(typeof value==='number'&&Number.isSafeInteger(value)))return value;
  throw Error('NONCANONICAL_INPUT');
}
const hash=value=>createHash('sha256').update(JSON.stringify(canonical(value)),'utf8').digest('hex');
const hold=(reason)=>Object.freeze({schema:SCHEMA,state:'HOLD',hold_code:reason,
  native_admitted:false,source_rights_independently_verified:false,
  host_context_readback_authenticated:false,source_bytes_hydrated:0,
  network_fetch:false,execution_performed:false,machine_authorised:false,
  native_dbr_written:false,public_publish_authorized:false,
  mint_authorised:false,commercial_release_authorised:false});

export function reviewPrintspaceHostR0(input, trustPins){
  if(!obj(input)||!obj(trustPins))return hold('MISSING_REQUEST_OR_OUT_OF_BAND_PINS');
  if(Object.keys(input).sort().join(',') !== ['plan','product_id','context_response',
    'lineage_candidates','load_contract','client_permissions','source_status'].sort().join(','))
    return hold('UNEXPECTED_OR_UNKNOWN_HOST_INPUT');
  const {plan,product_id,context_response,lineage_candidates,
    load_contract,client_permissions,source_status} = input;
  try{
    // The pins must come from a separately supplied review configuration;
    // never treat matching client data as independently authenticated.
    const pinned=canonical(trustPins);
    if(Object.keys(pinned).join(',') !==
       ['bundle_sha256','plan_sha256','product_facet_sha256'].sort().join(',') ||
       !HEX.test(pinned.bundle_sha256)||!HEX.test(pinned.product_facet_sha256)||
       !HEX64.test(pinned.plan_sha256))return hold('TRUST_PIN_FORMAT');
    if(!obj(plan)||plan.schema!==SRC||plan.state!=='R0_CANDIDATE_REVIEW_NOT_ADMITTED'
       ||!Array.isArray(plan.r0_cases)||plan.r0_cases.length!==3||
       plan.native_admitted!==false||plan.trusted_host_authenticated!==false||
       plan.native_dbr_written!==false||plan.machine_authorised!==false||
       plan.source_bytes_hydrated!==0||plan.mint_authorised!==false||
       plan.commercial_release_authorised!==false||
       plan.host_child_filespace!=='Romer.cgx'||
       plan.parent_namespace!=='Cognigrex.cgx')return hold('UNTRUSTED_SOURCE_PLAN');
    const noHash={...plan};delete noHash.plan_sha256;
    if(hash(noHash)!==plan.plan_sha256||plan.plan_sha256!==pinned.plan_sha256||
       plan.root_bundle_sha256!==pinned.bundle_sha256)
      return hold('SOURCE_PLAN_TAMPER_OR_PIN_MISMATCH');
    if(typeof product_id!=='string')return hold('PRODUCT_SCOPE_MISSING');
    const rows=plan.r0_cases.filter(x=>x.product_id===product_id);
    if(rows.length!==1)return hold('PRODUCT_SCOPE_NOT_EXACT');
    const item=rows[0];
    if(item.product_facet_sha256!==pinned.product_facet_sha256 ||
       item.bundle_sha256!==pinned.bundle_sha256||
       item.product_alias!=='product/'+product_id||
       item.host_context_request_ready!==true||
       item.native_object_admitted!==false||
       item.source_lineage_independently_verified!==false||
       item.source_rights_independently_verified!==false||
       item.r_layer!=='R0'||item.hydration!=='H0'||
       item.destination_filespace!=='Romer.cgx'||
       item.parent_filespace!=='Cognigrex.cgx'||
       JSON.stringify(item.child_domain)!==JSON.stringify({semantic_object_id:'cgx:domain:romer',filespace:'Romer.cgx',domain:'romer'}))
      return hold('PRODUCT_FACET_OR_CHILD_MISMATCH');
    if(!Array.isArray(lineage_candidates)||lineage_candidates.length!==1||
       lineage_candidates[0]?.semantic_object_id!==item.candidate_object_id||
       lineage_candidates[0]?.twin_id!==item.twin_id_candidate)
      return hold('HOST_LINEAGE_COLLISION_OR_MISMATCH');
    // Sanity-check all supplied objects for private fields and excessive size,
    // but never return untrusted host response (may contain private paths).
    for(const x of [input,trustPins]){
      const json=JSON.stringify(canonical(x));
      if(json.length>65536) return hold('INPUT_SIZE_BUDGET');
    }
    const context=projectCgxHostObjectContextGate({
      requested_object_id:item.candidate_object_id,requested_layer:'R0',
      expected_child:item.child_domain,
      context_response,lineage_candidates,
      lineage_git_blob_sha:item.lineage_git_blob_sha_candidate,
      registry_git_blob_sha:item.registry_git_blob_sha_candidate,
    });
    if(context.state!=='PLAN_ONLY_NOT_HYDRATED')return hold('HOST_CONTEXT_'+context.hold_code);
    const lens=projectUniSpaceLoadLens({
      load_contract,requested_object_id:item.candidate_object_id,
      destination_filespace:'Romer.cgx',context_plan:context,
      client_permissions,source_status,
      requested_layer:'R0',requested_hydration:'H0',offline:true,
    });
    if(lens.state!=='PLAN_ONLY_NOT_HYDRATED')return hold('LOAD_R0_'+lens.hold_code);
    return Object.freeze({schema:SCHEMA,state:'PLAN_ONLY_NOT_HYDRATED',
      product_id,product_facet_sha256:item.product_facet_sha256,
      bundle_sha256:plan.root_bundle_sha256,plan_sha256:plan.plan_sha256,
      object_id:item.candidate_object_id,filespace:'Romer.cgx',
      requested_layer:'R0',planned_hydration:'H0',
      host_context_schema:context.schema,load_review_schema:lens.schema,
      source_registry_sha_candidate:item.registry_git_blob_sha_candidate,
      source_lineage_sha_candidate:item.lineage_git_blob_sha_candidate,
      native_admitted:false,source_rights_independently_verified:false,
      host_context_readback_authenticated:false,source_bytes_hydrated:0,
      network_fetch:false,execution_performed:false,machine_authorised:false,
      native_dbr_written:false,public_publish_authorized:false,
      mint_authorised:false,commercial_release_authorised:false,
      next_gate:'INDEPENDENT_HOST_READBACK_RIGHTS_ACL_ID_COLLISION_AND_DB_RECEIPT',
    });
  }catch(_){return hold('INVALID_PRIVATE_OR_NONCANONICAL_INPUT')}
}