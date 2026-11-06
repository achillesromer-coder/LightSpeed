/**
 * UniSpace source-review LOAD viewport inspector contract.
 * Pure planning: NO provider reads, rendering, authentication, network, DBR, or publication.
 * All supplied policies, Object_IDs, rights and source refs are untrusted until host readback.
 * LOAD is an Alexandria entry alias under Cognigrex.cgx, never a new parent.
 */
export const INSPECTOR_SCHEMA = 'UNISPACE-LOAD-VIEWPORT-INSPECTOR-PLAN/0.1';
const VIEWS = new Set(['document', '3d', 'chat', 'graph', 'interactive', 'matrix']);
const DEPTHS = new Set(['glance', 'standard', 'deep', 'audit', 'raw']);
const LIMITS = Object.freeze({max_nodes:512,max_hops:6,max_cross_domains:8,max_cross_edges:256,max_evidence_refs:256,max_compute_ms:120000,max_ops_per_second:1000,max_transfer_bytes:60*1024*1024});
const KEYS = new Set([...Object.keys(LIMITS), 'reasoning_depth']);
const SAFE_ID = /^[A-Za-z0-9][A-Za-z0-9:_-]{0,127}$/;
const SAFE_SPACE = /^[A-Za-z][A-Za-z0-9_.-]*\.cgx$/;
const BAD_KEYS = new Set(['token','authorization','cookie','secret','source_locator','source_bytes','source_url','private_path','public_path','asset_path','asset_url','carrier_path','upload_url','dbr_root','lease']);
const own = (o,k)=>Object.prototype.hasOwnProperty.call(o,k);
const record = x=>x!==null && typeof x==='object' && !Array.isArray(x);
const safe = x=>typeof x==='string' && SAFE_ID.test(x);
const hold = code=>Object.freeze({schema:INSPECTOR_SCHEMA,state:'HOLD',hold_code:code,alias:'LOAD.cgx',native_admitted:false,host_authenticated:false,rendered:false,network_fetch:false,canonical_mutation:false,public_release:false});
function forbidden(x, depth=0, seen=new Set()) {
  if(!x || typeof x!=='object')return false;
  if(depth>8 || seen.has(x))return true;
  seen.add(x);
  for(const [k,v] of Object.entries(x)){
    if(BAD_KEYS.has(k.toLowerCase()) || forbidden(v,depth+1,seen))return true;
  }
  seen.delete(x);return false;
}
function validBudgets(b) {
  if(!record(b) || !DEPTHS.has(b.reasoning_depth))return false;
  if(Object.keys(b).some(k=>!KEYS.has(k)&&!['device_hydration','execution_depth'].includes(k)))return false;
  if(b.execution_depth!=='inspect')return false;
  for(const [key,max] of Object.entries(LIMITS)){
    if(!Number.isSafeInteger(b[key]) || b[key]<0 || b[key]>max)return false;
  }
  return b.max_nodes>=1 && b.max_ops_per_second>=1;
}
/** Inspector planning is not permission grant or host hydration. */
export function planUniSpaceLoadViewportInspector(input) {
  if(!record(input) || forbidden(input))return hold('INVALID_OR_PRIVATE_INPUT');
  const {context_plan:c,lens_plan:l,spread_plan:s,viewport_plan:v,client_permissions:p,novel_plan:n=null,requested_controls:t=null,offline=false}=input;
  if(!record(c)||c.schema!=='UNISPACE-CGX-HOST-CONTEXT-GATE/0.1'||c.state!=='PLAN_ONLY_NOT_HYDRATED'||
     c.native_admitted!==false||c.host_context_readback_authenticated!==false||c.private_hydration_authorized!==false||
     c.public_publish_authorized!==false||c.canonical_mutation!==false||c.execution_performed!==false||
     !safe(c.object_id)||c.object_id.startsWith('cgx:domain:')||c.object_id==='cgx:root:cognigrex'||!SAFE_SPACE.test(c.filespace||''))return hold('EXACT_CONTEXT_REQUIRED');
  if(!record(l)||l.schema!=='UNISPACE-CGX-LOAD-LENS-PLAN/0.1'||l.state!=='PLAN_ONLY_NOT_HYDRATED'||
     l.alias!=='LOAD.cgx'||l.parent_filespace!=='Cognigrex.cgx'||l.object_id!==c.object_id||l.filespace!==c.filespace||
     l.hydrated!==false||l.native_admitted!==false||l.canonical_mutation!==false||l.execution_performed!==false||
     l.public_publish_authorized!==false||l.host_context_readback_authenticated!==false||
     !['creative','scientific','mixed','unknown'].includes(l.evidence_class)||
     !['H0','H1','H2','H3'].includes(l.planned_hydration))return hold('LOAD_LENS_BOUNDARY_MISMATCH');
  if(!record(p)||p.mode!=='review_only'||p.revoked!==false||!Array.isArray(p.allowed_object_ids)||
     !Array.isArray(p.allowed_filespaces)||p.allowed_filespaces.length!==1||p.allowed_filespaces[0]!==c.filespace||
     !Array.isArray(p.allowed_source_ids)||!Array.isArray(p.allowed_domains)||
     !p.allowed_object_ids.includes(c.object_id)||p.allowed_object_ids.some(x=>!safe(x))||
     p.allowed_source_ids.some(x=>!safe(x))||p.allowed_domains.some(x=>!safe(x))||
     new Set(p.allowed_object_ids).size!==p.allowed_object_ids.length)return hold('CLIENT_SCOPE_DENIED');
  if(!record(s)||s.schema!=='LOAD-SEMANTIC-SPREAD-PLAN/0.1'||s.status!=='REVIEW_ONLY'||
     s.focus_id!==c.object_id||s.network_fetch!==false||s.rendered!==false||
     s.canonical_mutation!==false||s.hydration_complete!==false||!validBudgets(s.budgets)||
     !Array.isArray(s.objects)||s.objects.length<1||s.objects.length>s.budgets.max_nodes||
     !Array.isArray(s.edges)||s.edges.length>10000)return hold('UNTRUSTED_SEMANTIC_SPREAD');
  const ids=new Set(), domains=new Set(), sources=new Set();
  for(const o of s.objects){
    if(!record(o)||!safe(o.object_id)||!safe(o.domain)||ids.has(o.object_id)||
       !p.allowed_object_ids.includes(o.object_id)||!p.allowed_domains.includes(o.domain)||
       !Array.isArray(o.source_refs)||o.source_refs.some(x=>!safe(x)||!p.allowed_source_ids.includes(x)))
      return hold('UNAUTHORIZED_HALO_OR_SOURCE');
    ids.add(o.object_id);domains.add(o.domain);
    for(const ref of o.source_refs)sources.add(ref);
  }
  if(!ids.has(c.object_id)||sources.size>s.budgets.max_evidence_refs||
     domains.size-1>s.budgets.max_cross_domains)return hold('HALO_BUDGET_OR_FOCUS_MISMATCH');
  const focus=s.objects.find(x=>x.object_id===c.object_id);
  if(!focus || !safe(focus.source_ceiling)||!p.allowed_domains.includes(focus.domain))return hold('FOCUS_EVIDENCE_UNQUALIFIED');
  if(s.edges.some(e=>!record(e)||!ids.has(e.from)||!ids.has(e.to)||!safe(e.relation)))
    return hold('EDGE_SCOPE_MISMATCH');
  if(!record(v)||v.schema!=='LOAD-VIEWPORT-SWITCH-PLAN/0.1'||!VIEWS.has(v.to)||
     v.identity!==c.object_id||!Array.isArray(v.selected_object_ids)||
     v.selected_object_ids.length!==ids.size||v.selected_object_ids.some(x=>!ids.has(x))||
     v.network_fetch!==false||v.rendered!==false||v.interactive_execution!==false||
     v.semantic_mutation!==false||v.public_release!==false||
     v.evidence_ceiling!==focus.source_ceiling||
     !Array.isArray(v.source_refs)||v.source_refs.length!==focus.source_refs.length||
     v.source_refs.some((x,i)=>x!==focus.source_refs[i]))return hold('VIEW_CEILING_OR_ID_MISMATCH');
  const geom=record(focus.geometry)?focus.geometry:null;
  const qualifiedGeometry=!!(geom && safe(geom.source_ref) &&
     p.allowed_source_ids.includes(geom.source_ref) && safe(geom.frame) && safe(geom.units));
  if(v.geometry_ref!==(geom?.source_ref??null))return hold('GEOMETRY_SOURCE_MISMATCH');
  if(v.to==='3d' && !qualifiedGeometry && v.state!=='FRONTIER_GEOMETRY_UNQUALIFIED')return hold('FALSE_GEOMETRY_READINESS');
  if(v.to==='3d' && qualifiedGeometry && v.state!=='VIEW_PLAN_READY')return hold('GEOMETRY_PLAN_INCONSISTENT');
  if(v.to!=='3d' && !['VIEW_PLAN_READY','FRONTIER_SOURCE_UNAVAILABLE'].includes(v.state))return hold('UNEXPECTED_VIEW_STATE');
  if(n!==null && (!record(n)||n.schema!=='LOAD-NOVEL-TO-KNOWN-PLAN/0.1'||n.domain!==focus.domain||
      !['SOURCE_IDENTITY_CANDIDATE','SEMANTIC_MATCH_REVIEW','FRONTIER_NEW'].includes(n.status)||
      n.native_admission!==false||n.created_object_ids!==0||n.verified_object_id!==null||
      !Array.isArray(n.required)))return hold('UNTRUSTED_NOVEL_MATCH');
  if(typeof offline!=='boolean'||(offline&&l.planned_hydration!=='H0'))return hold('OFFLINE_H0_REQUIRED');
  if(t!==null && (!record(t)||Object.keys(t).some(k=>!KEYS.has(k))))return hold('UNSUPPORTED_CONTROL');
  const next={...s.budgets,...(t??{})};
  if(!validBudgets(next))return hold('CONTROL_LIMIT_EXCEEDED');
  const pending=Object.entries(t??{}).some(([k,value])=>s.budgets[k]!==value);
  const frontier=['HOST_ACL_NOT_VERIFIED','SOURCE_RIGHTS_NOT_INDEPENDENTLY_VERIFIED','NATIVE_DBR_NOT_ACCEPTED'];
  if(v.to==='3d'&&!qualifiedGeometry)frontier.push('GEOMETRY_FRAME_UNITS_OR_SOURCE_MISSING');
  if(n?.status==='FRONTIER_NEW')frontier.push('NOVEL_SOURCE_UNRESOLVED');
  if(offline)frontier.push('OFFLINE_H0_ONLY');
  return Object.freeze({
    schema:INSPECTOR_SCHEMA,state:pending?'REPLAN_REQUIRED':'SOURCE_REVIEW_ONLY',
    parent_filespace:'Cognigrex.cgx',alias:'LOAD.cgx',object_id:c.object_id,filespace:c.filespace,
    view:v.to,requested_view_state:v.state,evidence_class:l.evidence_class,
    evidence_ceiling_claimed:focus.source_ceiling,
    halo:offline?null:Object.freeze({selected_object_ids:[...ids],edge_count:s.edges.length,domain_count:domains.size,
      permitted_source_ref_count_claimed:sources.size}),
    novel_match:offline?null:n?Object.freeze({status:n.status,gap_categories:['source_identity_version','units_geometry_time','rights_acl','native_dbr'] }):null,
    current_controls:offline?null:Object.freeze({...s.budgets}),
    proposed_controls:offline?null:Object.freeze(next),pending_replan:pending,
    hydration:offline?'H0_OFFLINE_METADATA_ONLY':l.planned_hydration,
    frontier:Object.freeze(frontier),
    display_source_locators:false,display_private_assets:false,source_rights_independently_verified:false,
    client_permissions_independently_authenticated:false,host_authenticated:false,
    geometry_rendered:false,rendered:false,network_fetch:false,native_admitted:false,
    canonical_mutation:false,public_release:false,execution_performed:false,
    next_gate:'AUTHENTICATED_HOST_EXACT_ID_RIGHTS_ACL_AND_DBR_READBACK',
    claim_boundary:'Source-review inspector descriptor, not a rendered, permissioned or deployed UniSpace interface.'
  });
}
