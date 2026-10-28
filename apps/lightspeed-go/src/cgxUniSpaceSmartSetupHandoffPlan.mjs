/**
 * UniSpace Smart Setup handoff: review-only projection of the existing CGX
 * object-context, LOAD viewport and unified LightSpeed setup planners.
 * No host call, credentials, root creation, install, hydration or publication.
 * This module never grants authority from a browser-supplied receipt.
 */
export const SMART_HANDOFF_SCHEMA='UNISPACE-CGX-SMART-SETUP-HANDOFF/0.1';
const MODES=new Set(['first-run','resume','repair','upgrade']);
const DEVICES=new Set(['desktop','browser','mobile']);
const CHILDREN=new Set(['Romer.cgx','Eco.cgx','EMASSC.cgx','LS.cgx']);
const ACTIONS=new Set(['smart_setup.open','smart_setup.resume','smart_setup.repair','smart_setup.upgrade','load.attach','ccc.discover']);
const ID=/^[A-Za-z0-9][A-Za-z0-9:_-]{0,127}$/;
const BAD=new Set(['token','authorization','cookie','secret','password','source_locator','source_url','source_bytes','private_path','public_path','asset_path','asset_url','carrier_path','upload_url','lease','dbr_root','state_root','access_key']);
const obj=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const hold=code=>Object.freeze({schema:SMART_HANDOFF_SCHEMA,state:'HOLD',reason:code,host_authenticated:false,installed:false,native_admitted:false,network_fetch:false,canonical_mutation:false,public_release:false});
function hasPrivateFields(x,depth=0,seen=new Set()){
  if(!x||typeof x!=='object')return false;
  if(depth>9||seen.has(x))return true;
  seen.add(x);
  for(const [key,value] of Object.entries(x)){
    if(BAD.has(key.toLowerCase())||hasPrivateFields(value,depth+1,seen))return true;
  }
  seen.delete(x);return false;
}
export function planUniSpaceSmartSetupHandoff(input){
  if(!obj(input)||hasPrivateFields(input))return hold('INVALID_OR_PRIVATE_INPUT');
  const {context_plan:c,inspector_plan:i,setup_plan:s,client_permissions:p,requested_action='smart_setup.open',offline=false}=input;
  if(!obj(c)||c.schema!=='UNISPACE-CGX-HOST-CONTEXT-GATE/0.1'||
     c.state!=='PLAN_ONLY_NOT_HYDRATED'||c.requested_layer!=='R0'||
     c.native_admitted!==false||c.host_context_readback_authenticated!==false||
     c.private_hydration_authorized!==false||c.public_publish_authorized!==false||
     c.canonical_mutation!==false||c.execution_performed!==false||
     !ID.test(c.object_id||'')||c.object_id.startsWith('cgx:domain:')||
     c.object_id==='cgx:root:cognigrex'||!CHILDREN.has(c.filespace))
    return hold('EXACT_R0_CHILD_CONTEXT_REQUIRED');
  if(!obj(p)||p.mode!=='review_only'||p.revoked!==false||
     !Array.isArray(p.allowed_object_ids)||p.allowed_object_ids.length!==1||
     p.allowed_object_ids[0]!==c.object_id||
     !Array.isArray(p.allowed_filespaces)||p.allowed_filespaces.length!==1||
     p.allowed_filespaces[0]!==c.filespace)
    return hold('CLIENT_SCOPE_DENIED');
  if(!obj(i)||i.schema!=='UNISPACE-LOAD-VIEWPORT-INSPECTOR-PLAN/0.1'||
     !['SOURCE_REVIEW_ONLY','REPLAN_REQUIRED'].includes(i.state)||
     i.object_id!==c.object_id||i.filespace!==c.filespace||
     i.parent_filespace!=='Cognigrex.cgx'||i.alias!=='LOAD.cgx'||
     i.native_admitted!==false||i.host_authenticated!==false||
     i.rendered!==false||i.network_fetch!==false||i.canonical_mutation!==false||
     i.public_release!==false||i.execution_performed!==false||
     !['creative','scientific','mixed','unknown'].includes(i.evidence_class))
    return hold('INSPECTOR_BINDING_OR_PROOF_MISMATCH');
  if(!obj(s)||s.schema!=='CGX-UNIFIED-BOOTSTRAP-PLAN/0.1'||s.state!=='REVIEW_ONLY'||
     s.family!==c.filespace||!MODES.has(s.mode)||!DEVICES.has(s.device)||
     s.canonical_accepted!==false||s.runtime_installed!==false||
     s.source_ingested!==false||s.independent_host_acceptance!==false||
     s.published!==false||s.website_deployed!==false||
     !obj(s.library)||s.library.name!=='LOAD.cgx'||s.library.bind!=='EXISTING_IDENTITY_ONLY'||
     s.library.install!==false||s.library.network_hydration!==false||
     !obj(s.ls_go)||s.ls_go.product!=='Grex-scoped LS GO'||
     s.ls_go.separate_product!=='UniSpace'||s.ls_go.enabled!==false||
     s.ls_go.actual_toggle_write!==false||
     !Array.isArray(s.steps)||s.steps.length!==11||
     s.steps.some(x=>!obj(x)||x.canonical_mutation!==false||x.auto_run!==false))
    return hold('UNTRUSTED_SETUP_PLAN_OR_CROSS_PRODUCT_MISMATCH');
  if(!ACTIONS.has(requested_action)||typeof offline!=='boolean')
    return hold('UNKNOWN_ACTION_OR_DEVICE_STATE');
  const expected={'smart_setup.resume':'resume','smart_setup.repair':'repair','smart_setup.upgrade':'upgrade'};
  if(expected[requested_action]&&s.mode!==expected[requested_action])
    return hold('ACTION_MODE_MISMATCH');
  if(offline&&(s.offline_minimum!==true||i.hydration!=='H0_OFFLINE_METADATA_ONLY'))
    return hold('OFFLINE_H0_ONLY');
  if(!offline&&i.hydration==='H0_OFFLINE_METADATA_ONLY')
    return hold('OFFLINE_MODE_MISMATCH');
  const notices=['NATIVE_HOST_ROOT_ACL_DBR_NOT_INDEPENDENTLY_VERIFIED','ISSUE_158_PRIVATE_ASSET_HTTP_NEGATIVES_REQUIRED','ISSUE_161_DISTINCT_NODE_PROOF_REQUIRED','LOAD_OBJECT_ID_AND_RIGHTS_UNRESOLVED'];
  if(s.mode!=='first-run')notices.push('PREVIOUS_RECEIPT_REQUIRES_CURRENT_HOST_RECHECK');
  if(i.state==='REPLAN_REQUIRED')notices.push('VIEWPORT_CONTROLS_REPLAN_REQUIRED');
  return Object.freeze({
    schema:SMART_HANDOFF_SCHEMA,state:'SOURCE_REVIEW_ONLY',
    parent_filespace:'Cognigrex.cgx',filespace:c.filespace,
    candidate_object_id:c.object_id,identity_status:'CANDIDATE_NOT_NATIVE_ACCEPTED',
    evidence_class:i.evidence_class,source_proof:'SOURCE_REVIEW_ONLY',
    selected_view:i.view,selected_hydration:offline?'H0_OFFLINE_METADATA_ONLY':i.hydration,
    setup_mode:s.mode,device:s.device,requested_action,
    products:Object.freeze({unispace:'SEPARATE_PRODUCT_NOT_DEPLOYED',
      grex_ls_go:'PRIVATE_OPERATOR_OFF_UNVERIFIED'}),
    inventory:Object.freeze({load:'ALIAS_REFERENCE_ONLY_NOT_ACTIVATED',
      ccc_registered:'UNVERIFIED',ccc_installed:'UNVERIFIED',
      runtime_installed:'UNVERIFIED',got:'OPTIONAL_SOURCE_UNRESOLVED'}),
    setup_sections:Object.freeze(['welcome','identity','library','capabilities','runtime','grexgo','handshake','finish']),
    actions:Object.freeze(['alexandria.open','alexandria.resolve','load.attach','load.hydrate','ccc.discover','ccc.install','load.switch_view','load.match_novel','load.tune_context'].map(id=>({id,mode:'PREFLIGHT_ONLY',enabled:false}))),
    notices:Object.freeze(notices),host_authenticated:false,installed:false,
    native_admitted:false,network_fetch:false,canonical_mutation:false,
    execution_performed:false,public_release:false,source_bytes_transferred:0,
    next_gate:'HOST_EXACT_ID_RIGHTS_LEASE_DBR_AND_158_161_NEGATIVE_READBACK',
    claim_boundary:'Source-review UniSpace setup descriptor; no owner-session connection, installation or live product.'
  });
}
