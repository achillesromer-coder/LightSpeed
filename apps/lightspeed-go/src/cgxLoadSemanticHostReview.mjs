/**
 * Neo LS.cgx crosswalk for LOAD PR #205 semantic viewport / qualified operator
 * proposals. Source review ONLY: no LOAD import, transport, source ingestion,
 * host lease, numerical solver, CCC installation or DBR mutation.
 * Do not interpret a caller-supplied planner result as authenticated authority.
 */
export const SCHEMA='CGX-LS-LOAD-SEMANTIC-HOST-REVIEW/0.1';
const LIMITS=Object.freeze({
 max_nodes:64,max_hops:4,max_cross_domains:3,max_cross_edges:64,
 max_evidence_refs:64,max_compute_ms:5000,max_ops_per_second:100,
 max_transfer_bytes:0,
});
const ID=/^[a-zA-Z0-9][a-zA-Z0-9._:/-]{0,199}$/;
const SECRET=/(?:^|[_-])(secret|token|password|credential|private[_-]?key|authorization|cookie|session|bearer|api[_-]?key)(?:$|[_-])/i;
const obj=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const id=x=>typeof x==='string'&&ID.test(x)&&!x.includes('..');
const qualifiedText=x=>typeof x==='string'&&x.trim().length>0&&x.length<=256&&
 !/[\u0000-\u001f]/.test(x);
const falseKeys=(o,keys)=>keys.every(k=>o[k]===false);
const hold=code=>Object.freeze({schema:SCHEMA,state:'HOLD',hold_code:code,
 native_admitted:false,capability_installed:false,host_authenticated:false,
 lease_verified:false,dbr_readback_verified:false,solver_invoked:false,
 rendered:false,hydration_performed:false,canonical_mutation:false,
 network_fetch:false,source_bytes_copied:0});
function unsafe(x,depth=0,seen=new Set()){
 if(depth>7)return true;
 if(x===null||typeof x!=='object')return false;
 if(seen.has(x))return true;
 seen.add(x);
 if(Object.keys(x).length>100||(Array.isArray(x)&&x.length>256))return true;
 for(const [k,v] of Object.entries(x)){
  if(SECRET.test(k)||unsafe(v,depth+1,seen))return true;
 }
 seen.delete(x);return false;
}
const budgetKeys=Object.keys(LIMITS);
function checkBudgets(spread,ceiling){
 if(!obj(spread.budgets)||!obj(ceiling))return false;
 for(const k of budgetKeys){
  const n=spread.budgets[k],c=ceiling[k];
  if(!Number.isSafeInteger(n)||!Number.isSafeInteger(c)||
     n<0||c<0||n>c||c>LIMITS[k])return false;
 }
 return spread.budgets.max_nodes>0&&spread.budgets.max_ops_per_second>0&&
  spread.max_planned_operations===Math.floor(spread.budgets.max_compute_ms*
   spread.budgets.max_ops_per_second/1000);
}
/**
 * Only a bounded proposal. Authentic host MUST re-resolve all identities,
 * rights, ACL, version/ABI, lease and DBR before any action.
 */
export function reviewLoadSemanticHost(input){
 if(!obj(input)||!obj(input.hydration_review)||!obj(input.spread)||
    !obj(input.request)||unsafe(input))return hold('INVALID_OR_SENSITIVE_ENVELOPE');
 if(Object.hasOwn(input,'host_claim')||Object.hasOwn(input,'lease')||
    Object.hasOwn(input,'dbr_receipt'))return hold('HOST_ASSERTION_NOT_EVIDENCE');
 const h=input.hydration_review,s=input.spread,r=input.request;
 if(h.schema!=='CGX-LS-LOAD-HOST-HYDRATION-REVIEW/0.1'||
    h.state!=='HOST_HANDSHAKE_REQUIRED'||h.target_filespace!=='LS.cgx'||
    h.parent_filespace!=='EMASSC.cgx'||h.parent_ccc!=='Cognigrex.cgx:/ccc'||
    !id(h.candidate_object_id)||!id(h.capability_id)||
    !/^[0-9a-f]{40}$/i.test(h.source_revision||'')||
    !falseKeys(h,['native_admitted','capability_installed','host_authenticated',
      'owner_lease_verified','dbr_readback_verified','hydration_performed',
      'network_fetch','canonical_mutation','source_proof_independently_verified',
      'source_rights_verified'])||h.source_bytes_copied!==0)
    return hold('HYDRATION_SOURCE_REVIEW_UNQUALIFIED');
 if(r.target_filespace!=='LS.cgx'||r.parent_filespace!=='EMASSC.cgx'||
    r.parent_ccc!=='Cognigrex.cgx:/ccc'||r.object_id!==h.candidate_object_id||
    r.focus_id!==r.object_id||r.capability_id!==h.capability_id||
    !['viewport','operator'].includes(r.mode)||
    !falseKeys(r,['network_permission','execution_requested','install_requested',
      'publish_requested','canonical_mutation_requested'])||
    r.max_transfer_bytes!==0)
    return hold('REQUEST_SCOPE_OR_IDENTITY_MISMATCH');
 if(s.schema!=='LOAD-SEMANTIC-SPREAD-PLAN/0.1'||s.status!=='REVIEW_ONLY'||
    s.focus_id!==r.focus_id||!Array.isArray(s.objects)||s.objects.length<1||
    s.objects.length>LIMITS.max_nodes||!s.objects.some(o=>obj(o)&&o.object_id===r.focus_id)||
    !Array.isArray(s.edges)||!Array.isArray(s.frontier)||
    s.actual_compute_ms!==null||s.actual_ops_per_second!==null||
    s.requested_ceiling_only!==true||s.network_fetch!==false||
    s.rendered!==false||s.canonical_mutation!==false||
    s.hydration_complete!==false)
    return hold('SEMANTIC_SPREAD_NOT_REVIEW_ONLY');
 if(!checkBudgets(s,r.budget_ceiling))return hold('INDEPENDENT_BUDGET_EXCEEDED');
 // Actual inclusion cannot exceed the declared independent node ceiling.
 if(s.objects.length>s.budgets.max_nodes)return hold('INDEPENDENT_BUDGET_EXCEEDED');
 // A source planner's selected objects are not a host ACL proof.
 if(s.objects.some(o=>!obj(o)||!id(o.object_id)||!id(o.domain))||
    new Set(s.objects.map(o=>o.object_id)).size!==s.objects.length||
    s.edges.length>LIMITS.max_nodes*LIMITS.max_nodes)
    return hold('UNQUALIFIED_OR_COLLIDING_OBJECTS');
 const byId=new Map(s.objects.map(o=>[o.object_id,o]));
 const domains=new Set(s.objects.map(o=>o.domain));
 if(domains.size-1>s.budgets.max_cross_domains)
   return hold('INDEPENDENT_BUDGET_EXCEEDED');
 let evidence=0;
 for(const o of s.objects){
  if(!Array.isArray(o.source_refs)||o.source_refs.some(ref=>
     typeof ref!=='string'||ref.length===0||ref.length>256||/[\u0000-\u001f]/.test(ref)))
    return hold('UNQUALIFIED_EVIDENCE_REFERENCES');
  evidence+=o.source_refs.length;
 }
 if(!Number.isSafeInteger(s.source_ref_count)||s.source_ref_count!==evidence)
   return hold('EVIDENCE_COUNT_MISMATCH');
 if(evidence>s.budgets.max_evidence_refs)
   return hold('INDEPENDENT_BUDGET_EXCEEDED');
 let crossEdges=0;const edgeKeys=new Set();
 for(const e of s.edges){
  if(!obj(e)||!id(e.from)||!id(e.to)||!id(e.relation)||
     !byId.has(e.from)||!byId.has(e.to))
    return hold('UNQUALIFIED_OR_COLLIDING_EDGES');
  const key=JSON.stringify([e.from,e.to,e.relation]);
  if(edgeKeys.has(key))return hold('UNQUALIFIED_OR_COLLIDING_EDGES');
  edgeKeys.add(key);
  if(byId.get(e.from).domain!==byId.get(e.to).domain)crossEdges++;
 }
 if(crossEdges>s.budgets.max_cross_edges)
   return hold('INDEPENDENT_BUDGET_EXCEEDED');
 // Independent directed reachability and shortest-hop ceiling; the source
 // planner's max_hops declaration is not proof of actual selected depth.
 const adjacency=new Map(s.objects.map(o=>[o.object_id,[]]));
 for(const e of s.edges)adjacency.get(e.from).push(e.to);
 const hops=new Map([[r.focus_id,0]]),queue=[r.focus_id];
 for(let i=0;i<queue.length;i++){
  const from=queue[i],nextHop=hops.get(from)+1;
  for(const to of adjacency.get(from)){
   if(hops.has(to))continue;
   hops.set(to,nextHop);queue.push(to);
  }
 }
 if(hops.size!==s.objects.length)return hold('UNQUALIFIED_OR_COLLIDING_EDGES');
 if([...hops.values()].some(h=>h>s.budgets.max_hops))
   return hold('INDEPENDENT_BUDGET_EXCEEDED');
 const v=input.viewport_plan;
 if(r.mode==='viewport'){
  if(!obj(v)||v.schema!=='LOAD-VIEWPORT-SWITCH-PLAN/0.1'||
     v.identity!==r.focus_id||!['document','3d','chat','graph','interactive','matrix'].includes(v.to)||
     v.to!==r.view||v.state!=='VIEW_PLAN_READY'||
     !Array.isArray(v.selected_object_ids)||
     v.selected_object_ids.length!==s.objects.length||
     v.selected_object_ids.some((selected,i)=>selected!==s.objects[i].object_id)||
     !falseKeys(v,['network_fetch','rendered','interactive_execution','semantic_mutation','public_release']))
     return hold('VIEWPORT_NOT_SOURCE_QUALIFIED');
  // The LOAD planner cannot mark a source-unavailable focus as VIEW_PLAN_READY.
  // Independently match its focus evidence and geometry provenance, not just IDs.
  const focus=byId.get(r.focus_id);
  if(focus.source_available!==true||focus.source_refs.length===0||
     !Array.isArray(v.source_refs)||v.source_refs.length!==focus.source_refs.length||
     v.source_refs.some((ref,i)=>ref!==focus.source_refs[i]))
     return hold('VIEWPORT_NOT_SOURCE_QUALIFIED');
  if(v.to==='3d'&&(!obj(focus.geometry)||
     !qualifiedText(focus.geometry.source_ref)||!qualifiedText(focus.geometry.frame)||
     !qualifiedText(focus.geometry.units)||v.geometry_ref!==focus.geometry.source_ref))
     return hold('VIEWPORT_NOT_SOURCE_QUALIFIED');
 }else if(v!==undefined&&v!==null)return hold('UNEXPECTED_VIEWPORT_PLAN');
 const op=input.operator_plan;
 if(r.mode==='operator'){
  if(!obj(op)||op.schema!=='LOAD-QUALIFIED-OPERATOR-PLAN/0.1'||
     op.status!=='SOURCE_ONLY_NO_EXECUTION'||op.computation_executed!==false||
     op.numeric_result!==null||op.object_ids_minted!==0||
     !Array.isArray(op.operator_candidates)||op.operator_candidates.length<1||
     op.operator_candidates.length>10)
     return hold('OPERATOR_NOT_SOURCE_QUALIFIED');
  const routes=new Set();
  for(const c of op.operator_candidates){
   if(!obj(c)||!id(c.route_key)||routes.has(c.route_key)||
      c.state!=='EXPLICIT_TYPED_OPERATOR_CANDIDATE'||
      c.solver_invoked!==false||c.results_generated!==false||
      !Array.isArray(c.blockers)||
      !c.blockers.includes('HOST_CAPABILITY_LEASE_AND_DB_R_READBACK_REQUIRED'))
      return hold('DUPLICATE_OR_UNQUALIFIED_OPERATOR');
   routes.add(c.route_key);
  }
 }else if(op!==undefined&&op!==null)return hold('UNEXPECTED_OPERATOR_PLAN');
 return Object.freeze({
  schema:SCHEMA,state:'HOST_REVALIDATION_REQUIRED',
  target_filespace:'LS.cgx',parent_filespace:'EMASSC.cgx',
  parent_ccc:'Cognigrex.cgx:/ccc',candidate_object_id:r.object_id,
  capability_id:r.capability_id,mode:r.mode,
  source_revision:h.source_revision.toLowerCase(),
  planned_objects:s.objects.length,planned_edges:s.edges.length,
  max_planned_operations:s.max_planned_operations,
  budget_ceiling:Object.freeze(Object.fromEntries(budgetKeys.map(k=>[k,r.budget_ceiling[k]]))),
  source_proof_independently_verified:false,rights_verified:false,
  native_admitted:false,capability_installed:false,host_authenticated:false,
  lease_verified:false,dbr_readback_verified:false,solver_invoked:false,
  rendered:false,hydration_performed:false,canonical_mutation:false,
  network_fetch:false,source_bytes_copied:0,
  required_host_checks:Object.freeze([
   'authenticated exact-source and ABI/version readback',
   'native parent and unique Object_ID/alias resolution',
   'current owner ACL and source rights',
   'independent graph facet/edge/evidence ACL and budget enforcement',
   'signed scoped host lease and independently accepted DBR readback',
   'qualified solver method, units, frame, epoch and measured usage if applicable'
  ]),
 });
}
