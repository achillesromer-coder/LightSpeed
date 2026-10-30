/** UniSpace private source-aware LOAD inspector projection (review only).
 * Pure adapter over existing LOAD planners. Never treats caller ACL declarations as
 * host authentication, source envelopes as provider receipts, or R3 as admission.
 */
import {planKnowledgeSpread,planViewportSwitch} from './loadSemanticViewport.mjs';
export const INSPECTOR_SCHEMA='UNISPACE-LOAD-SOURCE-INSPECTOR/0.1';
const good=x=>typeof x==='string'&&x.trim().length>0&&x.length<=256&&!/[\u0000-\u001f]/.test(x);
const object=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
// Opaque identities, authority scopes and graph edges must not contain Unicode
// directional/default-ignorable controls or alternate-normalisation spellings.
// This is a source-review guard, not an authoritative CGX Object_ID resolver.
const unambiguous=s=>good(s)&&s===s.normalize('NFC')&&!/[\p{Default_Ignorable_Code_Point}\p{Cc}]/u.test(s);
const safeNode=n=>object(n)&&unambiguous(n.object_id)&&unambiguous(n.domain)&&
 unambiguous(n.file_space)&&Array.isArray(n.source_refs)&&n.source_refs.every(unambiguous)&&
 Array.isArray(n.edges)&&n.edges.every(e=>object(e)&&unambiguous(e.to)&&unambiguous(e.relation));
const sha=x=>typeof x==='string'&&/^[0-9a-f]{64}$/i.test(x);
const rights=new Set(['PUBLIC_SAFE','OWNER_PRIVATE','LICENSE_RESTRICTED','UNKNOWN']);
const proofClasses=new Set(['creative','scientific','engineering','historical','operational']);
// A known Grex domain must never be presented under another child's FileSpace.
// This is a review boundary, not an authoritative namespace resolver.
const knownChildSpaces=Object.freeze({eco:'Eco.cgx',romer:'Romer.cgx',emassc:'EMASSC.cgx',ls:'LS.cgx'});
// Reserved Grex FileSpaces are bidirectional: an unknown/aliased domain cannot
// claim an established child's namespace, even with caller-supplied ACL arrays.
const reservedChildSpaces=Object.freeze(Object.fromEntries(Object.entries(knownChildSpaces).map(([domain,space])=>[space,domain])));
const childSpaceMatches=n=>object(n)&&good(n.domain)&&good(n.file_space)&&
 (Object.hasOwn(knownChildSpaces,n.domain)?knownChildSpaces[n.domain]===n.file_space:
  !Object.hasOwn(reservedChildSpaces,n.file_space));
const hold=(reason)=>({schema:INSPECTOR_SCHEMA,status:'DENIED',reason,canonical_mutation:false,public_release:false});

/** Builds one bounded FileSpace inspector plan, never an authenticated view. */
export function planUniSpaceSourceInspector({nodes,focus_id,access,file_space,view='document',budgets={},source_envelopes=[],surface=null,offline=false}={}){
 // Fail closed unless the caller explicitly selects the private review surface.
 // This is not host authentication: #158 still requires real session/ACL checks.
 if(surface!=='private')return hold('PRIVATE_INSPECTOR_SURFACE_REQUIRED');
 if(typeof offline!=='boolean')return hold('INVALID_OFFLINE_MODE');
 if(!good(file_space)||!good(focus_id)||!Array.isArray(nodes)||!object(budgets)||!Array.isArray(source_envelopes)||source_envelopes.length>512)
  return hold('INVALID_INSPECTOR_SCOPE');
 if(!object(access)||!Array.isArray(access.authorized_source_ids)||!Array.isArray(access.authorized_object_ids))
  return hold('EXPLICIT_SCOPE_REQUIRED');
 if(!unambiguous(file_space)||!unambiguous(focus_id)||
  !access.authorized_object_ids.every(unambiguous)||!access.authorized_source_ids.every(unambiguous)||
  !nodes.every(safeNode))return hold('AMBIGUOUS_IDENTITY_OR_SCOPE');
 // An exact child FileSpace is required. Display labels, parent aliases and paths
 // must not silently select a different domain's FileSpace.
 const selected=nodes.filter(n=>object(n)&&n.object_id===focus_id);
 if(selected.length!==1||selected[0].file_space!==file_space)return hold('FILESPACE_OR_ID_UNRESOLVED');
 if(!childSpaceMatches(selected[0]))
  return hold('FILESPACE_OR_ID_UNRESOLVED');
 // Offline state has no authoritative rights-revocation, root or session check.
 // Permit only a metadata-only H0 projection of the exact caller-scoped identity:
 // no cached source hashes, sibling graph, capabilities or R3 promotion.
 if(offline){
  if(!new Set(['document','3d','chat','graph','interactive','matrix']).has(view))
   return hold('INVALID_GRAPH_VIEW_OR_BUDGET');
  if(!access.authorized_object_ids.includes(focus_id))
   return hold('OBJECT_SCOPE_NOT_AUTHORIZED');
  return {schema:INSPECTOR_SCHEMA,status:'SOURCE_REVIEW_ONLY',
   selected_file_space:file_space,identity:focus_id,view,
   h0:{object_id:focus_id,owner:null,accepted:false},
   h1:{edges:[],object_ids:[focus_id],cross_domain_enabled:false},
   h2:{source_claims:[],source_proof:'OFFLINE_UNVERIFIED',proof_classes:[]},
   h3:{qualified_capabilities:[],catalogue_discovery_only:false},
   h4:{permissioned_execution:'HOST_DENIED_UNTIL_INDEPENDENT_ROOT_LEASE_DBR',installed:false},
   viewport:{state:'FRONTIER',lens:null,projection:'metadata-only',geometry_ref:null,
    metric_authority:'NOT_VERIFIED',frontier:['OFFLINE_AUTHORITY_AND_REVOCATION_UNVERIFIED'],rendered:false},
   budgets:{max_nodes:1,max_hops:0,max_transfer_bytes:0},
   admission_stage:'R2_REVIEW_FRONTIER',source_bytes_copied:false,network_fetch:false,
   host_authenticated:false,provider_readback:false,canonical_mutation:false,public_release:false,
   offline_fallback:'H0_ONLY_UNVERIFIED_METADATA'};
 }
 // The planner validates untrusted graph, view and budget input by throwing.
 // A user-facing inspector must convert those failures into a non-disclosing HOLD.
 let spread,switchPlan;
 try {
  spread=planKnowledgeSpread({nodes,focus_id,access,budgets:{max_cross_domains:0,max_cross_edges:0,...budgets}});
  if(spread.status!=='REVIEW_ONLY')return hold('OBJECT_SCOPE_NOT_AUTHORIZED');
  // Cross-Grex traversal must preserve each child's own FileSpace, even when
  // caller-supplied object/source ACL arrays include that sibling. Never
  // render a Romer/Eco/EMASSC/LS object under a spoofed child namespace.
  const byId=new Map(nodes.map(n=>[n.object_id,n]));
  if(spread.objects.some(o=>{
   const n=byId.get(o.object_id);
   return !childSpaceMatches(n);
  }))return hold('CHILD_FILESPACE_SCOPE_CONFLICT');
  switchPlan=planViewportSwitch({spread,to:view});
 } catch {
  return hold('INVALID_GRAPH_VIEW_OR_BUDGET');
 }
 const focus=selected[0];
 const permitted=new Set(access.authorized_source_ids);
 const refSet=new Set(spread.objects.find(n=>n.object_id===focus_id)?.source_refs??[]);
 const claims=[];const seen=new Set();const conflicts=new Set();
 for(const e of source_envelopes){
  if(!object(e)||!unambiguous(e.source_id)||!refSet.has(e.source_id)||!permitted.has(e.source_id))continue;
  if(seen.has(e.source_id)){conflicts.add(e.source_id);continue;}
  seen.add(e.source_id);
  // C33: caller-supplied revocation/supersession evidence is a veto, never a grant.
  // Missing or non-ACTIVE rights state is a Frontier veto, never an R3 grant.
  const rightsActive=e.rights_state==='ACTIVE';
  const notRevoked=e.revoked!==true&&e.rights_revoked!==true&&
   !Object.hasOwn(e,'revoked_at')&&!Object.hasOwn(e,'superseded_by');
  const valid=rightsActive&&notRevoked&&sha(e.sha256)&&unambiguous(e.version)&&unambiguous(e.owner)&&rights.has(e.rights)&&e.rights!=='UNKNOWN'&&e.rights!=='LICENSE_RESTRICTED'&&proofClasses.has(e.proof_class);
  claims.push({source_id:e.source_id,sha256:valid?e.sha256.toLowerCase():null,
   version:valid?e.version:null,owner:valid?e.owner:null,
   rights:valid?e.rights:'UNRESOLVED',proof_class:valid?e.proof_class:'unclassified',
   qualification:valid?'DECLARED_NOT_PROVIDER_VERIFIED':
    (!rightsActive||!notRevoked?'FRONTIER_RIGHTS_REVOKED_OR_UNRESOLVED':'FRONTIER_SOURCE_QUALIFICATION')});
 }
 for(const claim of claims)if(conflicts.has(claim.source_id)){claim.qualification='FRONTIER_COLLIDING_SOURCE';claim.sha256=null;}
 // Do not mark an R3 candidate if any focus evidence was filtered by ACL or budget.
 // Never return the withheld identifiers or counts to the presentation layer.
 const requiredRefs=new Set(Array.isArray(focus.source_refs)?focus.source_refs:[]);
 const fullEvidenceScope=requiredRefs.size===refSet.size&&[...requiredRefs].every(id=>refSet.has(id));
 const allQualified=fullEvidenceScope&&refSet.size>0&&claims.length===refSet.size&&claims.every(c=>c.qualification==='DECLARED_NOT_PROVIDER_VERIFIED');
 const geometryQualified=view!=='3d'||Boolean(switchPlan.geometry_ref&&claims.some(c=>c.source_id===switchPlan.geometry_ref&&c.sha256));
 // #209 scientific-asset stop-ship: this adapter has caller declarations only.
 // Even plausible units/frame/hash or caller-supplied "verified" flags cannot
 // establish one physical metric model, independent numeric proof or host DBR.
 // A future verified native reader must supply a separately authenticated
 // geometry receipt; this review-only adapter must not fabricate that route.
 const metricGeometryUnverified=view==='3d';
 const frontier=[];
 if(metricGeometryUnverified)frontier.push('METRIC_GEOMETRY_PROVIDER_AND_INDEPENDENT_VALIDATION_REQUIRED');
 if(!allQualified)frontier.push('SOURCE_VERSION_HASH_OWNER_RIGHTS_OR_CLASS_UNRESOLVED');
 if(!geometryQualified)frontier.push('GEOMETRY_SOURCE_PROOF_UNRESOLVED');
 if(switchPlan.state.startsWith('FRONTIER'))frontier.push(switchPlan.state);
 const viewCandidate=frontier.length===0;
 return {schema:INSPECTOR_SCHEMA,status:'SOURCE_REVIEW_ONLY',
  selected_file_space:file_space,identity:focus_id,view,
  h0:{object_id:focus_id,owner:unambiguous(focus.owner)?focus.owner:null,accepted:false},
  h1:{edges:spread.edges,object_ids:spread.objects.map(n=>n.object_id),cross_domain_enabled:spread.budgets.max_cross_domains>0},
  h2:{source_claims:claims,source_proof:'CALLER_DECLARATIONS_ONLY',proof_classes:[...new Set(claims.map(c=>c.proof_class))]},
  h3:{qualified_capabilities:[],catalogue_discovery_only:true},
  h4:{permissioned_execution:'HOST_DENIED_UNTIL_INDEPENDENT_ROOT_LEASE_DBR',installed:false},
  viewport:{state:viewCandidate?'R3_PRIVATE_VIEW_CANDIDATE':'FRONTIER',lens:switchPlan.registered_lens,
   projection:switchPlan.projection,geometry_ref:geometryQualified&&!metricGeometryUnverified?switchPlan.geometry_ref:null,
   metric_authority:'NOT_VERIFIED',
   frontier,rendered:false},
  budgets:spread.budgets,admission_stage:viewCandidate?'R3_VIEW_PROPOSAL':'R2_REVIEW_FRONTIER',
  source_bytes_copied:false,network_fetch:false,host_authenticated:false,provider_readback:false,
  canonical_mutation:false,public_release:false,offline_fallback:'H0_H2_DECLARED_METADATA_ONLY'};
}


/**
 * UniSpace operator cockpit: one private, non-executing progress projection.
 * Consumes an inspector plan, NOT a native receipt. This must never elevate
 * caller claims into accepted Object_ID, root, rights, host or deployment proof.
 * Private UI source-review only; never embed in a public Vite/static route.
 */
export const OPERATOR_COCKPIT_SCHEMA='UNISPACE-PRIVATE-OPERATOR-STATUS/0.1';
const cockpitDeny=reason=>({
 schema:OPERATOR_COCKPIT_SCHEMA,state:'DENIED',reason,
 native_admitted:false,host_authenticated:false,provider_readback:false,
 deployed:false,live_verified:false,owner_accepted:false,
 released:false,may_execute:false,canonical_mutation:false
});
export function planUniSpaceOperatorCockpit({
 surface=null,selection=null,inspector=null,offline=false,hostReceipt=null
}={}){
 if(surface!=='private')return cockpitDeny('PRIVATE_OPERATOR_SURFACE_REQUIRED');
 if(typeof offline!=='boolean'||!object(selection)||!object(inspector))
  return cockpitDeny('INVALID_COCKPIT_INPUT');
 if(!unambiguous(selection.object_id)||!unambiguous(selection.file_space)||
    !unambiguous(selection.domain)||selection.parent_file_space!=='Cognigrex.cgx'||
    !Object.hasOwn(knownChildSpaces,selection.domain)||
    knownChildSpaces[selection.domain]!==selection.file_space)
  return cockpitDeny('EXACT_CHILD_IDENTITY_REQUIRED');
 if(inspector.schema!==INSPECTOR_SCHEMA||
    inspector.status!=='SOURCE_REVIEW_ONLY'||
    inspector.identity!==selection.object_id||
    inspector.selected_file_space!==selection.file_space||
    !object(inspector.h0)||inspector.h0.object_id!==selection.object_id||
    !object(inspector.h1)||!Array.isArray(inspector.h1.object_ids)||
    !inspector.h1.object_ids.includes(selection.object_id)||
    !object(inspector.h2)||!Array.isArray(inspector.h2.source_claims)||
    !object(inspector.h4)||!object(inspector.viewport))
  return cockpitDeny('INSPECTOR_SELECTION_OR_SCHEMA_MISMATCH');
 // The only accepted input is a review-only projection, with all authority
 // fields still false. A "verified" flag on a caller/hostReceipt is never a
 // native verification and is deliberately not read or copied into output.
 if(inspector.h0.accepted!==false||inspector.h4.installed!==false||
    inspector.host_authenticated!==false||inspector.provider_readback!==false||
    inspector.canonical_mutation!==false||inspector.public_release!==false||
    inspector.source_bytes_copied!==false||inspector.network_fetch!==false||
    inspector.viewport.rendered!==false)
  return cockpitDeny('UNTRUSTED_ELEVATED_REVIEW_PLAN');
 const offlinePlan=inspector.h2.source_proof==='OFFLINE_UNVERIFIED'&&
    inspector.admission_stage==='R2_REVIEW_FRONTIER'&&
    inspector.viewport.state==='FRONTIER';
 const onlinePlan=inspector.h2.source_proof==='CALLER_DECLARATIONS_ONLY'&&(
    (inspector.admission_stage==='R3_VIEW_PROPOSAL'&&
      inspector.viewport.state==='R3_PRIVATE_VIEW_CANDIDATE')||
    (inspector.admission_stage==='R2_REVIEW_FRONTIER'&&
      inspector.viewport.state==='FRONTIER'));
 if(offline?!offlinePlan:!onlinePlan)
  return cockpitDeny('REVIEW_EVIDENCE_STAGE_CONFLICT');
 // #209/#158: the caller can hand in a fabricated inspector object. The
 // source-only inspector never qualifies metric 3D as R3; neither may this
 // operator projection. A conflicting Frontier/metric badge is also a veto.
 // A forged review projection cannot relabel a metric scene as a document,
 // invent an unregistered viewport intent, or smuggle an unqualified geometry
 // reference into a non-metric R3 proposal. The host remains authoritative.
 if(!offline&&inspector.admission_stage==='R3_VIEW_PROPOSAL'&&
    (!new Set(['document','chat','graph','interactive','matrix']).has(inspector.view)||
     !(inspector.viewport.geometry_ref===null||
       (unambiguous(inspector.viewport.geometry_ref)&&
        inspector.h2.source_claims.some(c=>c?.source_id===inspector.viewport.geometry_ref&&
         c.qualification==='DECLARED_NOT_PROVIDER_VERIFIED')))||
     inspector.viewport.metric_authority!=='NOT_VERIFIED'||
     !Array.isArray(inspector.viewport.frontier)||inspector.viewport.frontier.length!==0))
  return cockpitDeny('UNVERIFIED_METRIC_VIEW_CANNOT_BE_R3');
 // R3 is only a caller-declared proposal. Even at that low ceiling, a
 // forged inspector must not advertise a qualified document/graph/chat view
 // with zero, revoked, malformed, duplicate or contradictory R0 claims.
 // This validates internal review consistency, NOT provider authenticity.
 if(!offline&&inspector.admission_stage==='R3_VIEW_PROPOSAL'){
  const claims=inspector.h2.source_claims;
  const classes=inspector.h2.proof_classes;
  const unique=new Set(claims.map(c=>c?.source_id));
  const qualified=claims.length>0&&unique.size===claims.length&&
   Array.isArray(classes)&&classes.length>0&&
   classes.length===new Set(classes).size&&
   claims.every(c=>object(c)&&unambiguous(c.source_id)&&sha(c.sha256)&&
    unambiguous(c.version)&&unambiguous(c.owner)&&
    (c.rights==='PUBLIC_SAFE'||c.rights==='OWNER_PRIVATE')&&
    proofClasses.has(c.proof_class)&&classes.includes(c.proof_class)&&
    c.qualification==='DECLARED_NOT_PROVIDER_VERIFIED')&&
   classes.every(cls=>claims.some(c=>c.proof_class===cls));
  if(!qualified)return cockpitDeny('R3_SOURCE_PROOF_CLAIMS_UNQUALIFIED');
 }
 const candidate=!offline&&inspector.admission_stage==='R3_VIEW_PROPOSAL';
 const blockers=[
  'SOURCE_ORIGINAL_REVISION_HASH_RIGHTS_NOT_PROVIDER_VERIFIED',
  'CURRENT_NATIVE_ROOT_OBJECT_ID_ACL_LEASE_DBR_NOT_READ_BACK',
  'UNAUTHENTICATED_REVOKED_VALID_HOST_NEGATIVE_TESTS_REQUIRED',
  'PRIVATE_HOST_AND_BROWSER_READBACK_REQUIRED',
  'OWNER_ACCEPTANCE_AND_PUBLIC_RELEASE_NOT_GRANTED'
 ];
 if(offline)blockers.unshift('OFFLINE_AUTHORITY_AND_RIGHTS_REVOCATION_UNKNOWN');
 if(!candidate&&!offline)blockers.unshift('VIEW_EVIDENCE_FRONTIER');
 // Do not echo source IDs, digests, private graph edges, rights declarations,
 // raw host receipts or remote addresses. A native host must independently
 // validate any future proof, then return a separate trusted projection.
 return {
  schema:OPERATOR_COCKPIT_SCHEMA,state:'SOURCE_REVIEW_ONLY',
  identity:selection.object_id,file_space:selection.file_space,
  parent_file_space:'Cognigrex.cgx',domain:selection.domain,
  presentation_stage:offline?'H0_OFFLINE_UNVERIFIED':
    candidate?'R3_VIEW_PROPOSAL':'R2_REVIEW_FRONTIER',
  view:offline?'metadata-only':inspector.view,
  source_evidence:'UNVERIFIED_CALLER_REVIEW',
  source_rights:'NOT_PROVIDER_VERIFIED',
  root_authority:'NOT_NATIVE_VERIFIED',
  host_connection:'NOT_AUTHENTICATED',
  cross_platform_sync:'NOT_VERIFIED',
  workflow:[
   {stage:'DISCOVERED',status:'CALLER_DECLARED'},
   {stage:'QUALIFIED',status:'HOLD_PROVIDER_PROOF'},
   {stage:'STAGED',status:'SOURCE_REVIEW_ONLY'},
   {stage:'TESTED',status:'NOT_RUNTIME_VERIFIED'},
   {stage:'ADMITTED',status:'HOLD'},
   {stage:'DEPLOYED',status:'HOLD'},
   {stage:'LIVE_VERIFIED',status:'HOLD'},
   {stage:'OWNER_ACCEPTED',status:'HOLD'},
   {stage:'RELEASED',status:'HOLD'}
  ],
  blockers,
  next_step:offline?'CONNECT_AUTHENTICATED_PRIVATE_PROVIDER':
    candidate?'REQUEST_INDEPENDENT_NATIVE_ROOT_LEASE_ACL_DBR_AND_READBACK':
      'QUALIFY_SOURCE_AND_VIEW_EVIDENCE',
  metrics:{latency_ms:null,metric_fidelity:null,transfer_bytes:null},
  host_receipt_accepted:false,source_bytes_read:false,rendered:false,
  native_admitted:false,host_authenticated:false,provider_readback:false,
  deployed:false,live_verified:false,owner_accepted:false,released:false,
  may_execute:false,canonical_mutation:false
 };
}
