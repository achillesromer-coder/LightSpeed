/**
 * UniSpace LOAD/CCC command-surface descriptor for ONE review-only object.
 * Pure source-review projection. Never binds event handlers, authenticates,
 * fetches source, installs a capability, hydrates or publishes an asset.
 * Existing host must independently resolve Object_ID, child ACL and DBR.
 */
export const LOAD_COMMAND_SURFACE_SCHEMA='UNISPACE-LOAD-COMMAND-SURFACE/0.1';
const CHILDREN=new Set(['Romer.cgx','Eco.cgx','EMASSC.cgx','LS.cgx']);
const SURFACES=new Set(['context-menu','long-press','command-palette','ccc-launch']);
const VIEWS=new Set(['document','3d','chat','graph','interactive','matrix']);
const ID=/^[A-Za-z0-9][A-Za-z0-9:_-]{0,127}$/;
const ACTIONS=Object.freeze({
 'filespace':['alexandria.open','alexandria.resolve','load.attach','load.hydrate','ccc.discover','ccc.install','load.switch_view','load.match_novel','load.tune_context'],
 'object':['alexandria.resolve','alexandria.sources','ccc.discover','load.switch_view','load.match_novel','load.tune_context']
});
const LABELS=Object.freeze({
 'alexandria.open':'Explore Alexandria',
 'alexandria.resolve':'Resolve with Alexandria',
 'alexandria.sources':'Inspect source provenance',
 'load.attach':'Equip FileSpace with LOAD',
 'load.hydrate':'Hydrate library references',
 'ccc.discover':'Discover CCC capabilities',
 'ccc.install':'Install CCC capability (preflight)',
 'load.switch_view':'Switch semantic view',
 'load.match_novel':'Match novel knowledge',
 'load.tune_context':'Tune knowledge and compute budget'
});
const BAD=new Set(['token','authorization','cookie','password','secret','access_key','source_url','source_locator','source_bytes','private_path','public_path','asset_url','asset_path','carrier_path','upload_url','endpoint','internal_locator','private_payload','raw_payload','lease','dbr_root','state_root']);
const record=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const safe=x=>typeof x==='string'&&ID.test(x);
function forbidden(x,depth=0,seen=new Set()){
 if(!x||typeof x!=='object')return false;
 if(depth>9||seen.has(x))return true;
 seen.add(x);
 for(const [k,v] of Object.entries(x)){
  if(BAD.has(k.toLowerCase())||forbidden(v,depth+1,seen))return true;
 }
 seen.delete(x);return false;
}
const hold=code=>Object.freeze({
 schema:LOAD_COMMAND_SURFACE_SCHEMA,state:'HOLD',hold_code:code,
 native_admitted:false,host_authenticated:false,public_release:false,
 source_bytes_transferred:0,network_fetch:false,execution_performed:false,canonical_mutation:false
});
export function planUniSpaceLoadCommandSurface(input){
 if(!record(input)||forbidden(input))return hold('INVALID_OR_PRIVATE_INPUT');
 const {context_plan:c,handoff_plan:h,client_permissions:p,surface='context-menu',
  target_kind='object',requested_action=null,offline=false}=input;
 if(!record(c)||c.schema!=='UNISPACE-CGX-HOST-CONTEXT-GATE/0.1'||
    c.state!=='PLAN_ONLY_NOT_HYDRATED'||c.requested_layer!=='R0'||
    !safe(c.object_id)||c.object_id.startsWith('cgx:domain:')||
    c.object_id==='cgx:root:cognigrex'||!CHILDREN.has(c.filespace)||
    c.native_admitted!==false||c.host_context_readback_authenticated!==false||
    c.private_hydration_authorized!==false||c.public_publish_authorized!==false||
    c.canonical_mutation!==false||c.execution_performed!==false)
  return hold('EXACT_REVIEW_CONTEXT_REQUIRED');
 if(!record(p)||p.mode!=='review_only'||p.revoked!==false||
    !Array.isArray(p.allowed_object_ids)||p.allowed_object_ids.length!==1||
    p.allowed_object_ids[0]!==c.object_id||
    !Array.isArray(p.allowed_filespaces)||p.allowed_filespaces.length!==1||
    p.allowed_filespaces[0]!==c.filespace)
  return hold('EXACT_CLIENT_SCOPE_REQUIRED');
 if(!record(h)||h.schema!=='UNISPACE-CGX-SMART-SETUP-HANDOFF/0.1'||
    h.state!=='SOURCE_REVIEW_ONLY'||h.parent_filespace!=='Cognigrex.cgx'||
    h.candidate_object_id!==c.object_id||h.filespace!==c.filespace||
    !VIEWS.has(h.selected_view)||!['creative','scientific','mixed','unknown'].includes(h.evidence_class)||
    !record(h.inventory)||h.inventory.load!=='ALIAS_REFERENCE_ONLY_NOT_ACTIVATED'||
    h.inventory.ccc_installed!=='UNVERIFIED'||h.inventory.runtime_installed!=='UNVERIFIED'||
    h.native_admitted!==false||h.host_authenticated!==false||
    h.installed!==false||h.network_fetch!==false||h.canonical_mutation!==false||
    h.execution_performed!==false||h.public_release!==false)
  return hold('UNTRUSTED_HANDOFF_OR_CROSS_FAMILY');
 if(!SURFACES.has(surface)||!Object.hasOwn(ACTIONS,target_kind)||
    (requested_action!==null&&(!Object.hasOwn(LABELS,requested_action)||
     !ACTIONS[target_kind].includes(requested_action)))||
    typeof offline!=='boolean')
  return hold('UNKNOWN_SURFACE_TARGET_OR_ACTION');
 if(offline ? h.selected_hydration!=='H0_OFFLINE_METADATA_ONLY':
    h.selected_hydration==='H0_OFFLINE_METADATA_ONLY')
  return hold('OFFLINE_HYDRATION_MISMATCH');
 let ids=[...ACTIONS[target_kind]];
 if(surface==='ccc-launch')ids=ids.filter(x=>x.startsWith('ccc.'));
 if(offline)ids=ids.filter(x=>x==='alexandria.open');
 if(requested_action!==null&&!ids.includes(requested_action))
  return hold('ACTION_NOT_AVAILABLE_IN_THIS_SCOPE');
 const actions=ids.map(id=>Object.freeze({
  id,label:LABELS[id],enabled:false,mode:'HOST_PREFLIGHT_REQUIRED',
  action_authorized:false,keyboard_accessible:true,
  invocation:surface,callback_bound:false
 }));
 return Object.freeze({
  schema:LOAD_COMMAND_SURFACE_SCHEMA,state:'SOURCE_REVIEW_ONLY',
  parent_filespace:'Cognigrex.cgx',filespace:c.filespace,
  candidate_object_id:c.object_id,identity_status:'NOT_NATIVE_ACCEPTED',
  alias:'LOAD.cgx',alias_status:'REFERENCE_ONLY_NOT_ACTIVATED',
  evidence_class:h.evidence_class,selected_view:h.selected_view,
  requested_action,invocation_surface:surface,target_kind,
  actions:Object.freeze(actions),
  hydration:offline?'H0_OFFLINE_METADATA_ONLY':'NO_HYDRATION',
  levels:Object.freeze({
   H0:'CANDIDATE_IDENTITY_ONLY',
   H1:offline?'NOT_CACHED':'FRONTIER_EDGES_UNVERIFIED',
   H2:'FRONTIER_SOURCE_RIGHTS_UNVERIFIED',
   H3:'FRONTIER_CAPABILITY_REGISTRATION_UNVERIFIED',
   H4:'DENIED_PERMISSIONED_EXECUTION_NOT_AVAILABLE'
  }),
  geometry:h.selected_view==='3d'?'FRONTIER_FRAME_UNITS_AND_SOURCE_NOT_ATTESTED':'NOT_REQUESTED',
  ccc_installed:'UNVERIFIED',grex_ls_go:'SEPARATE_PRIVATE_PRODUCT_OFF_UNVERIFIED',
  accessibility:Object.freeze({keyboard:true,screen_reader_labels:true,mobile_long_press:true}),
  holds:Object.freeze(['EXACT_HOST_OBJECT_ACL_DBR_READBACK','ISSUE_158_ANONYMOUS_REVOKED_AND_DIST_ASSET_TESTS','ISSUE_161_DISTINCT_NODE_ACCEPTANCE']),
  native_admitted:false,host_authenticated:false,public_release:false,
  source_bytes_transferred:0,network_fetch:false,execution_performed:false,
  canonical_mutation:false,asset_urls_returned:false,handlers_bound:false,
  next_gate:'AUTHENTICATED_HOST_POLICY_AND_NEGATIVE_HTTP_READBACK',
  claim_boundary:'Source-review command descriptor only; no live menu, host session, installation, hydration or deployment.'
 });
}
