/** UniSpace private source-aware LOAD inspector projection (review only).
 * Pure adapter over existing LOAD planners. Never treats caller ACL declarations as
 * host authentication, source envelopes as provider receipts, or R3 as admission.
 */
import {planKnowledgeSpread,planViewportSwitch} from './loadSemanticViewport.mjs';
export const INSPECTOR_SCHEMA='UNISPACE-LOAD-SOURCE-INSPECTOR/0.1';
const good=x=>typeof x==='string'&&x.trim().length>0&&x.length<=256&&!/[\u0000-\u001f]/.test(x);
const object=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
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
  if(!object(e)||!good(e.source_id)||!refSet.has(e.source_id)||!permitted.has(e.source_id))continue;
  if(seen.has(e.source_id)){conflicts.add(e.source_id);continue;}
  seen.add(e.source_id);
  // C33: caller-supplied revocation/supersession evidence is a veto, never a grant.
  // Missing or non-ACTIVE rights state is a Frontier veto, never an R3 grant.
  const rightsActive=e.rights_state==='ACTIVE';
  const notRevoked=e.revoked!==true&&e.rights_revoked!==true&&
   !Object.hasOwn(e,'revoked_at')&&!Object.hasOwn(e,'superseded_by');
  const valid=rightsActive&&notRevoked&&sha(e.sha256)&&good(e.version)&&good(e.owner)&&rights.has(e.rights)&&e.rights!=='UNKNOWN'&&e.rights!=='LICENSE_RESTRICTED'&&proofClasses.has(e.proof_class);
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
  h0:{object_id:focus_id,owner:good(focus.owner)?focus.owner:null,accepted:false},
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
