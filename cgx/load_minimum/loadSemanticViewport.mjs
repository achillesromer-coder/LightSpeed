/**
 * LOAD / Alexandria semantic knowledge-spread and viewport planning.
 * Source-only, deterministic, nonexecuting: no I/O, network, DBR, token or renderer calls.
 * A host MUST independently enforce current policy and authoritative Object_ID state.
 */
import {validateRegistry} from './loadOnlineRegistry.mjs';
export const SPREAD_SCHEMA = "LOAD-SEMANTIC-SPREAD-PLAN/0.1";
export const NOVEL_SCHEMA = "LOAD-NOVEL-TO-KNOWN-PLAN/0.1";
const DENY = "DENIED";
const DEPTHS=new Set(["glance","standard","deep","audit","raw"]);
const HYDRATION=new Set(["projection-lite","reader","editor","workstation","distributed"]);
const EXEC=new Set(["inspect","propose","simulate","execute","build","publish"]);
const MAX={max_nodes:512,max_hops:6,max_cross_domains:8,max_cross_edges:256,max_evidence_refs:256,max_compute_ms:120000,max_ops_per_second:1000,max_transfer_bytes:60*1024*1024};
const DEFAULT={reasoning_depth:"standard",device_hydration:"reader",execution_depth:"inspect",max_nodes:16,max_hops:2,max_cross_domains:1,max_cross_edges:4,max_evidence_refs:32,max_compute_ms:2000,max_ops_per_second:50,max_transfer_bytes:1024*1024};
const VIEWS={
 document:{lens:"active-object-inspector",projection:"document-section"},
 "3d":{lens:"twin-3d",projection:"geometry-twin"},
 chat:{lens:"chat-generative",projection:"natural-language-interface"},
 graph:{lens:"topology-graph",projection:"typed-relations"},
 interactive:{lens:"hybrid-canonical-cells",projection:"read-only-controls"},
 matrix:{lens:"matrix",projection:"traceability"}
};
// Shared read-only UI view mapping; not an authenticated renderer or capability.
export function getRegisteredViewIntent(view){
 return Object.hasOwn(VIEWS,view)?Object.freeze({...VIEWS[view]}):null;
}
const good=s=>typeof s==="string" && s.trim().length>0 && s.length<=256 && !/[\u0000-\u001f]/.test(s);
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const ints=(list)=>Array.isArray(list)&&list.every(good);
const clean=x=>typeof x==="string"?x.trim():x;
function budget(input={}){
 if(!obj(input))throw Error("INVALID_BUDGET");
 const b={...DEFAULT,...input};
 if(!DEPTHS.has(b.reasoning_depth)||!HYDRATION.has(b.device_hydration)||!EXEC.has(b.execution_depth))throw Error("UNSUPPORTED_DEPTH");
 for(const [k,cap] of Object.entries(MAX)){
  if(!Number.isSafeInteger(b[k])||b[k]<0||b[k]>cap||(k==="max_nodes"&&b[k]<1)||(k==="max_ops_per_second"&&b[k]<1))throw Error("BUDGET_EXCEEDED:"+k);
 }
 return b;
}
function authorized(access){
 if(!obj(access)||!ints(access.authorized_object_ids)||!ints(access.authorized_source_ids))throw Error("EXPLICIT_AUTHORIZATION_REQUIRED");
 return {ids:new Set(access.authorized_object_ids),sources:new Set(access.authorized_source_ids)};
}
function graphNodes(nodes){
 if(!Array.isArray(nodes)||nodes.length>10000)throw Error("INVALID_GRAPH");
 const map=new Map();
 for(const n of nodes){
  if(!obj(n)||!good(n.object_id)||!good(n.domain)||!Array.isArray(n.edges)||!Array.isArray(n.source_refs))throw Error("INVALID_NODE");
  if(map.has(n.object_id))throw Error("COLLIDING_GRAPH_ID");
  if(!n.edges.every(e=>obj(e)&&good(e.to)&&good(e.relation)))throw Error("INVALID_TYPED_EDGE");
  if(!n.source_refs.every(good))throw Error("INVALID_SOURCE_REFERENCE");
  map.set(n.object_id,n);
 }
 return map;
}
const edgePriority=relation=>relation==="PART_OF"?0:relation==="HAS_CHILD"?1:relation==="EVIDENCED_BY"?2:3;
export function planKnowledgeSpread({nodes,focus_id,access,budgets={}}={}){
 const b=budget(budgets), a=authorized(access), graph=graphNodes(nodes);
 if(!good(focus_id)||!a.ids.has(focus_id))return {status:DENY,reason:"FOCUS_NOT_AUTHORIZED"};
 const focus=graph.get(focus_id);
 if(!focus)return {status:"NOT_FOUND",reason:"FOCUS_NOT_IN_GRAPH"};
 const included=[],viewEdges=[],seen=new Set(),frontier=[],queue=[{id:focus_id,hop:0}];
 const visitedDomains=new Set([focus.domain]);let crossCount=0,evidenceCount=0;
 while(queue.length&&included.length<b.max_nodes){
  const {id,hop}=queue.shift();if(seen.has(id))continue;
  const n=graph.get(id);if(!n||!a.ids.has(id))continue;
  if(n.domain!==focus.domain&&!visitedDomains.has(n.domain)){
   if(visitedDomains.size-1>=b.max_cross_domains)continue;
   visitedDomains.add(n.domain);
  }
  seen.add(id);
  const refs=n.source_refs.filter(ref=>a.sources.has(ref)).slice(0,Math.max(0,b.max_evidence_refs-evidenceCount));
  evidenceCount+=refs.length;
  const summary={object_id:n.object_id,domain:n.domain,kind:good(n.kind)?n.kind:"unknown",
   epistemic_state:good(n.epistemic_state)?n.epistemic_state:"unknown",
   source_refs:refs,source_ceiling:n.evidence_ceiling??"unverified",
   source_available:refs.length>0,geometry: null};
  // An ACL grant for a source does not prove that source belongs to this
  // object. Never project geometry from a permitted but unbound R0 reference.
  if(obj(n.geometry)&&good(n.geometry.source_ref)&&n.source_refs.includes(n.geometry.source_ref)&&a.sources.has(n.geometry.source_ref)){
   summary.geometry={source_ref:n.geometry.source_ref,frame:good(n.geometry.frame)?n.geometry.frame:null,
   units:good(n.geometry.units)?n.geometry.units:null,geometry_kind:n.geometry.geometry_kind??"source-linked"};
  }
  included.push(summary);
  if(hop>=b.max_hops)continue;
  const sorted=[...n.edges].sort((x,y)=>edgePriority(x.relation)-edgePriority(y.relation)||x.to.localeCompare(y.to)||x.relation.localeCompare(y.relation));
  for(const e of sorted){
   const child=graph.get(e.to);
   if(!child||!a.ids.has(e.to))continue; // do not leak inaccessible identity or counts
   if(child.domain!==focus.domain){
    if(b.max_cross_domains===0)continue;
    if(!visitedDomains.has(child.domain)&&visitedDomains.size-1>=b.max_cross_domains)continue;
    if(crossCount>=b.max_cross_edges)continue;
    crossCount++;
   }
   viewEdges.push({from:id,to:e.to,relation:e.relation});
   if(!seen.has(e.to)&&!queue.some(q=>q.id===e.to))queue.push({id:e.to,hop:hop+1});
  }
 }
 if(queue.length)frontier.push({reason:"BUDGET_LIMITED",omitted_count:"NOT_REVEALED"});
 return {schema:SPREAD_SCHEMA,status:"REVIEW_ONLY",focus_id,objects:included,edges:viewEdges.filter(e=>seen.has(e.from)&&seen.has(e.to)),
   budgets:b,frontier,source_ref_count:evidenceCount,domains_visited:[...visitedDomains],
   max_planned_operations:Math.floor(b.max_compute_ms*b.max_ops_per_second/1000),
   actual_compute_ms:null,actual_ops_per_second:null,requested_ceiling_only:true,
   network_fetch:false,rendered:false,canonical_mutation:false,hydration_complete:false};
}
/** Switches views of the same object identity and selected subgraph. Does not render them. */
export function planViewportSwitch({spread,to,from=null}={}){
 if(!obj(spread)||spread.schema!==SPREAD_SCHEMA||spread.status!=="REVIEW_ONLY"||!Array.isArray(spread.objects))throw Error("UNTRUSTED_SPREAD");
 if(!Object.hasOwn(VIEWS,to)||(from!==null&&!Object.hasOwn(VIEWS,from)))throw Error("UNKNOWN_VIEW");
 const focus=spread.objects.find(x=>x.object_id===spread.focus_id);
 if(!focus)throw Error("MISSING_FOCUS");
 const def=VIEWS[to];let state="VIEW_PLAN_READY";const requirements=[];
 if(!focus.source_available){state="FRONTIER_SOURCE_UNAVAILABLE";requirements.push("permitted R0/R1 source reference");}
 if(to==="3d"){
  if(!focus.geometry||!focus.geometry.frame||!focus.geometry.units){
   state="FRONTIER_GEOMETRY_UNQUALIFIED";
   requirements.push("geometry source + calibrated coordinate frame + units");
  }else{
   // A source-linked frame/units is a *candidate*, not a verified metric
   // world state. The browser cannot validate issuer, ephemeris, native DBR,
   // physical scale or owner acceptance. Even a caller-supplied "verified"
   // flag must not elevate a science asset (#209).
   state="SOURCE_LINKED_3D_REVIEW_ONLY";
   requirements.push("independent source bytes/hash/rights, epoch/time-scale/origin and metric model validation");
   requirements.push("native signed root, scoped ACL/lease, DBR and actual host readback");
   requirements.push("keep artistic glyph magnification and camera transforms separate from world metric coordinates");
  }
 }
 if(to==="interactive")requirements.push("host verified interaction capability and permissions for anything beyond read-only");
 if(to==="chat")requirements.push("model/provider capability and token budget separately verified");
 return {schema:"LOAD-VIEWPORT-SWITCH-PLAN/0.1",state,identity:spread.focus_id,
  from,to,registered_lens:def.lens,projection:def.projection,
  selected_object_ids:spread.objects.map(x=>x.object_id),source_refs:focus.source_refs,
  geometry_ref:focus.geometry?.source_ref??null,
  evidence_ceiling:focus.source_ceiling,requirements,
  independent_budget:spread.budgets,network_fetch:false,rendered:false,interactive_execution:false,
  // No client-side review plan can assert scientific, physical or host proof.
  metric_geometry_verified:false,physical_world_coordinates_exportable:false,
  scientific_authority:"HOLD_UNVERIFIED",native_admitted:false,host_handshake_verified:false,
  geometry_display_mode:to==="3d"?"NONMETRIC_SOURCE_REVIEW":"NOT_APPLICABLE",
  metric_scale:null,artistic_glyph_scale:null,camera_transform:null,
  semantic_mutation:false,public_release:false};
}
/** Novel source proposals can match an exact registered source or similar candidate,
 * never inventing Object_IDs or treating a name match as empirical evidence.
 */
export function planNovelMatching(registry,{source_hash=null,source_id=null,domain,source_name=null}={}){
 validateRegistry(registry);
 if(!good(domain)||(source_id!=null&&!good(source_id))||(source_name!=null&&!good(source_name))||
    (source_hash!=null && !/^[0-9a-f]{64}$/i.test(source_hash)))throw Error("INVALID_SOURCE");
 const mappings=registry.records.filter(r=>r.category==="conversion_source"&&r.owner_domain===domain);
 const byId=source_id?mappings.filter(r=>r.source_drive_id===source_id):[];
 const byHash=source_hash?mappings.filter(r=>r.source_sha256===source_hash):[];
 // When both identifiers are supplied, they must agree on the SAME source mapping.
 const exact=source_id&&source_hash?byId.filter(r=>r.source_sha256===source_hash):source_id?byId:byHash;
 const identityConflict=Boolean(source_id&&source_hash&&!exact.length&&(byId.length||byHash.length));
 const named=!identityConflict&&source_name?mappings.filter(r=>r.display.toLocaleLowerCase()===source_name.toLocaleLowerCase()&&!exact.includes(r)):[];
 return {schema:NOVEL_SCHEMA,status:identityConflict?"SOURCE_IDENTITY_CONFLICT":exact.length?"SOURCE_IDENTITY_CANDIDATE":named.length?"SEMANTIC_MATCH_REVIEW":"FRONTIER_NEW",
  conflict_mapping_ids:identityConflict?[...new Set([...byId,...byHash].map(r=>r.source_key))]:[],
  domain,source_matches:exact.map(r=>({mapping_id:r.source_key,candidate_object_id:r.candidate_object_id,source_registry:r.source_registry})),
  lexical_matches:named.map(r=>({mapping_id:r.source_key,candidate_object_id:r.candidate_object_id})),
  verified_object_id:null,created_object_ids:0,native_admission:false,
  required:["original source and version","type/units/time/configuration comparison","semantic difference and loss ledger","rights and owner authority","native RootAuthority/DBR acceptance"],
  note:"A matching native source or filename is not sufficient to prove semantic identity, truth or installed capability."};
}


/**
 * UniSpace private source-review inspector, derived from one LOAD spread.
 * This is a browser presentation contract, NOT a native Object_ID resolver.
 * Neither spread ACL claims nor caller receipts prove signed host authority.
 */
export const UNISPACE_INSPECTOR_SCHEMA='CGX-UNISPACE-PRIVATE-EVIDENCE-INSPECTOR/0.1';
const familyScope=Object.freeze({
 eco:{fileSpace:'Eco.cgx',parent:'Cognigrex.cgx'},
 romer:{fileSpace:'Romer.cgx',parent:'Cognigrex.cgx'},
 emassc:{fileSpace:'EMASSC.cgx',parent:'Cognigrex.cgx'},
 ls:{fileSpace:'LS.cgx',parent:'EMASSC.cgx'}
});
export function planUniSpaceEvidenceInspector({spread,target,view='document',surface=null}={}){
 const deny=reason=>({schema:UNISPACE_INSPECTOR_SCHEMA,state:'DENIED',reason,
  sourceBytesRead:false,hostVerified:false,publicRelease:false,mayExecute:false,
  canonicalMutation:false});
 if(surface!=='private')return deny('PRIVATE_INSPECTOR_SURFACE_REQUIRED');
 if(!obj(spread)||spread.schema!==SPREAD_SCHEMA||spread.status!=='REVIEW_ONLY'||
    !Array.isArray(spread.objects)||!Array.isArray(spread.edges)||
    !good(spread.focus_id)||!obj(target))return deny('UNTRUSTED_SPREAD_OR_TARGET');
 const focus=spread.objects.find(n=>n.object_id===spread.focus_id);
 if(!focus||spread.objects.filter(n=>n.object_id===spread.focus_id).length!==1)
  return deny('FOCUS_ID_NOT_UNIQUE');
 const scope=familyScope[focus.domain];
 if(!scope||target.objectId!==spread.focus_id||target.domain!==focus.domain||
    target.fileSpace!==scope.fileSpace||target.parentFileSpace!==scope.parent||
    target.rootFileSpace!=='Cognigrex.cgx')
  return deny('EXACT_CHILD_SCOPE_MISMATCH');
 if(!Array.isArray(focus.source_refs)||!focus.source_refs.every(good)||
    typeof focus.source_available!=='boolean'||!good(focus.source_ceiling))
  return deny('UNTRUSTED_FOCUS_EVIDENCE');
 if(!spread.objects.every(n=>obj(n)&&good(n.object_id)&&good(n.domain))||
    new Set(spread.objects.map(n=>n.object_id)).size!==spread.objects.length)
  return deny('UNTRUSTED_SPREAD_IDENTITIES');
 // Use existing viewport planner. Never bypass its geometry and proof holds.
 let viewport;
 try{viewport=planViewportSwitch({spread,to:view});}
 catch{return deny('INVALID_VIEWPORT_PROJECTION');}
 const includedIds=new Set(spread.objects.map(n=>n.object_id));
 if(spread.edges.some(e=>!obj(e)||!includedIds.has(e.from)||!includedIds.has(e.to)||
    !good(e.relation)))return deny('UNTRUSTED_EDGE_SCOPE');
 const edges=spread.edges.filter(e=>e.from===spread.focus_id||e.to===spread.focus_id);
 const sources=[...new Set(focus.source_refs)];
 const frontier=[];
 if(!sources.length)frontier.push('PERMITTED_R0_SOURCE_MISSING');
 if(view==='3d'&&viewport.state==='FRONTIER_GEOMETRY_UNQUALIFIED')
  frontier.push('QUALIFIED_GEOMETRY_MISSING');
 frontier.push('SOURCE_RIGHTS_AND_REVISION_NOT_PROVIDER_VERIFIED');
 frontier.push('CURRENT_NATIVE_OBJECT_ID_ROOT_ACL_LEASE_DBR_NOT_VERIFIED');
 frontier.push('ACTUAL_BROWSER_AND_HOST_READBACK_NOT_VERIFIED');
 return {
  schema:UNISPACE_INSPECTOR_SCHEMA,state:'PRIVATE_SOURCE_REVIEW_ONLY',
  family:'Cognigrex.cgx',child_file_space:scope.fileSpace,
  parent_file_space:scope.parent,selected_object_id:spread.focus_id,
  selected_domain:focus.domain,view:viewport.to,view_state:viewport.state,
  evidence_ceiling:'CALLER_SOURCE_CLAIMS_ONLY',
  hydration:'H0_H2_SPARSE_REVIEW',
  layers:{
   H0:{state:'CLAIMED_EXACT_ID_NOT_NATIVE_VERIFIED'},
   H1:{state:'AUTHORISED_SPREAD_CLAIM_ONLY',edge_count:edges.length},
   H2:{state:sources.length?'PERMITTED_SOURCE_REFS_CLAIMED':'FRONTIER_SOURCE_UNAVAILABLE',source_count:sources.length},
   H3:{state:'CCC_CAPABILITIES_NOT_NATIVE_VERIFIED'},
   H4:{state:'HOST_EXECUTION_NOT_AUTHORISED'}
  },
  source_refs:sources,selected_edges:edges,
  frontier,next_step:'RESOLVE_NATIVE_OBJECT_RIGHTS_AND_SIGNED_HOST_DBR_WITH_INDEPENDENT_READBACK',
  sourceBytesRead:false,rightsVerified:false,hostVerified:false,
  nativeAdmitted:false,rendered:false,mayExecute:false,publicRelease:false,
  canonicalMutation:false
 };
}
