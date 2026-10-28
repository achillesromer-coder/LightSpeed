/**
 * UniSpace LOAD.cgx minimal Alexandria library lens (source-review projection).
 * LOAD.cgx is an alias, not a new canonical parent or an accepted Object_ID.
 * No network, file IO, authentication, source hydration, execution or publication.
 * All caller evidence/permissions are UNTRUSTED planning inputs.
 */
const SCHEMA='UNISPACE-CGX-LOAD-LENS-PLAN/0.1';
const HEX40=/^[a-f0-9]{40}$/i;
const SAFE_SPACE=/^[A-Za-z][A-Za-z0-9_.-]*\.cgx$/;
const LEVELS=['H0','H1','H2','H3','H4'];
const SECTIONS=Object.freeze({
  H0:'identity_placeholder',
  H1:'typed_edges_placeholder',
  H2:'provenance_and_rights_placeholder',
  H3:'qualified_capabilities_placeholder'
});
const hold=code=>Object.freeze({
  schema:SCHEMA,state:'HOLD',hold_code:code,alias:'LOAD.cgx',
  native_admitted:false,hydrated:false,execution_performed:false,
  private_data_included:false,public_publish_authorized:false,canonical_mutation:false
});
const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
const forbidden=['token','authorization','cookie','source_bytes','source_locator',
  'private_path','public_path','asset_path','view_url','upload_url','lease','dbr_root'];
const safeObject=o=>o&&typeof o==='object'&&!Array.isArray(o);
export function projectUniSpaceLoadLens(input) {
  if(!safeObject(input))return hold('INVALID_REQUEST');
  if([input,input.client_permissions,input.source_status,input.context_plan]
      .some(o=>safeObject(o)&&forbidden.some(k=>own(o,k))))
    return hold('INLINE_SECRET_OR_PRIVATE_ROUTE');
  const a=input.load_contract;
  if(!safeObject(a)||a.schema!=='LOAD-ALEXANDRIA-ACTIVATION/0.1'||
     a.status!=='SOURCE_REVIEW_NOT_ADMITTED'||a.alias!=='LOAD.cgx'||
     a.parent_filespace!=='Cognigrex.cgx'||a.canonical_object_id!==null||
     a.accepted_parent_object_id!==null||a.canonical_mutation!==false||
     a.network_fetch!=='DENY_UNTIL_HOST_AUTHORIZED')
    return hold('LOAD_ALIAS_NOT_SOURCE_REVIEW');
  const p=input.context_plan, id=input.requested_object_id, space=input.destination_filespace;
  if(typeof id!=='string'||!id||id.length>128||id.startsWith('cgx:domain:')||
     id==='cgx:root:cognigrex'||typeof space!=='string'||!SAFE_SPACE.test(space)||
     !safeObject(p)||p.schema!=='UNISPACE-CGX-HOST-CONTEXT-GATE/0.1'||
     p.state!=='PLAN_ONLY_NOT_HYDRATED'||p.object_id!==id||p.filespace!==space||
     !HEX40.test(p.source_lineage_git_blob_sha||'')||
     !HEX40.test(p.source_registry_git_blob_sha||'')||
     p.native_admitted!==false||p.canonical_mutation!==false||
     p.execution_performed!==false||p.private_hydration_authorized!==false||
     p.public_publish_authorized!==false||
     p.host_context_readback_authenticated!==false||
     p.source_registry_independently_verified!==false)
    return hold('EXACT_OBJECT_CHILD_CONTEXT_UNVERIFIED');
  const c=input.client_permissions;
  if(!safeObject(c)||c.mode!=='review_only'||c.revoked!==false||
     !Array.isArray(c.allowed_object_ids)||c.allowed_object_ids.length!==1||
     c.allowed_object_ids[0]!==id||
     !Array.isArray(c.allowed_filespaces)||c.allowed_filespaces.length!==1||
     c.allowed_filespaces[0]!==space)
    return hold('CLIENT_SCOPE_DENIED');
  const s=input.source_status;
  if(!safeObject(s)||s.collision!=='no_conflict_reported')
    return hold('IDENTITY_COLLISION_OR_UNKNOWN');
  if(s.rights!=='cleared_for_review')
    return hold('SOURCE_RIGHTS_HOLD');
  if(!['creative','scientific','mixed','unknown'].includes(s.evidence_class))
    return hold('PROOF_CLASS_UNQUALIFIED');
  const h=input.requested_hydration;
  if(!LEVELS.includes(h))return hold('UNKNOWN_HYDRATION_LEVEL');
  if(h==='H4')return hold('H4_REQUIRES_INDEPENDENT_HOST_LEASE_AND_DBR');
  if(input.requested_layer!=='R0')return hold('R1_R3_REQUIRE_NATIVE_RECEIPTS');
  if(typeof input.offline!=='boolean')return hold('OFFLINE_MODE_REQUIRED');
  if(h==='H3'&&s.evidence_class==='unknown')
    return hold('CAPABILITY_PROOF_CLASS_UNKNOWN');
  // H1-H3 are only placeholders for future host-authorised hydration.
  // Offline is strictly H0; never serve cached private edges or locators.
  const planned=input.offline?'H0':h;
  const maxBytes=input.offline?0:Math.min(
    Number.isSafeInteger(input.max_bytes)&&input.max_bytes>0?input.max_bytes:65536,1048576);
  return Object.freeze({
    schema:SCHEMA,state:'PLAN_ONLY_NOT_HYDRATED',alias:'LOAD.cgx',
    parent_filespace:'Cognigrex.cgx',object_id:id,filespace:space,
    requested_hydration:h,planned_hydration:planned,
    offline_degraded:input.offline&&h!=='H0',
    display_sections:Object.freeze(LEVELS.slice(0,LEVELS.indexOf(planned)+1)
      .filter(x=>x!=='H4').map(x=>SECTIONS[x])),
    evidence_class:s.evidence_class,
    r_layer:'R0_REVIEW_PLAN',max_transfer_bytes:maxBytes,
    client_scope_independently_authenticated:false,
    source_rights_independently_verified:false,
    collision_independently_resolved:false,
    host_context_readback_authenticated:false,
    source_provenance_included:false,private_data_included:false,
    hydrated:false,native_admitted:false,execution_performed:false,
    public_publish_authorized:false,canonical_mutation:false,
    geometry_selector:'optional_non_authoritative_dodecahedral_view',
    output_surfaces:Object.freeze(['browser','phone','desktop']),
    accessibility:Object.freeze(['semantic_labels','keyboard_navigation','reduced_motion','high_contrast']),
    next_gate:'EXISTING_AUTHENTICATED_CGX_RESOLVER_RIGHTS_COLLISION_DBR_AND_PRIVATE_ACL_TESTS',
    claim_boundary:'Caller permission and rights flags are not host authentication or independent proof; no LOAD carrier or source was read.'
  });
}
