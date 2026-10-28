/** Source-only typed novel-to-known and qualified solver routing for LOAD.cgx.
 * Zero numeric solving, DBR writes, source acquisition or actual tool execution.
 */
import {validateRegistry} from './loadOnlineRegistry.mjs';
export const KNOWN_SCHEMA="LOAD-QUALIFIED-KNOWN-REUSE/0.1";
const good=x=>typeof x==="string"&&x.trim().length>0&&x.length<=256&&!/[\u0000-\u001f]/.test(x);
const obj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const arr=x=>Array.isArray(x)&&x.every(good);
const dimEqual=(a,b)=>{
 if(!obj(a)||!obj(b))return false;
 const ka=Object.keys(a).sort(),kb=Object.keys(b).sort();
 return ka.length===kb.length&&ka.every((k,i)=>k===kb[i]&&a[k]===b[k]);
};
function validConcept(c){
 if(!obj(c)||!good(c.semantic_type)||!obj(c.dimensions)||!arr(c.source_refs))throw Error("INVALID_SEMANTIC_CONCEPT");
 if(c.object_id!=null&&!good(c.object_id))throw Error("INVALID_OBJECT_ID");
 for(const [k,v] of Object.entries(c.dimensions))if(!good(k)||!good(v))throw Error("INVALID_DIMENSIONS");
}
export function planKnownAlignment({novel,known_objects,authorised_object_ids,authorised_source_ids,max_candidates=20}={}){
 validConcept(novel);
 if(!Array.isArray(known_objects)||known_objects.length>5000||!arr(authorised_object_ids)||!arr(authorised_source_ids)||
  !Number.isSafeInteger(max_candidates)||max_candidates<1||max_candidates>100)throw Error("INVALID_ALIGNMENT_SCOPE");
 const ids=new Set(authorised_object_ids),srcs=new Set(authorised_source_ids),seen=new Set(),candidates=[];
 const targetRefs=novel.source_refs.filter(s=>srcs.has(s));
 for(const k of known_objects){
  validConcept(k);
  if(!good(k.object_id)||!ids.has(k.object_id))continue;
  if(seen.has(k.object_id))throw Error("DUPLICATE_KNOWN_OBJECT_ID");
  seen.add(k.object_id);
  if(k.semantic_type!==novel.semantic_type)continue;
  const checks=[];
  if(!dimEqual(k.dimensions,novel.dimensions))checks.push("INCOMPATIBLE_DIMENSIONS");
  if(Object.keys(novel.dimensions).length>0){
   if(!obj(novel.units)||!obj(k.units)||!Object.keys(novel.dimensions).every(f=>good(novel.units[f])&&good(k.units[f])))checks.push("UNITS_UNDECLARED");
   else if(!Object.keys(novel.dimensions).every(f=>novel.units[f]===k.units[f]))checks.push("UNIT_CONVERSION_REQUIRED");
  }
  if(k.frame!==novel.frame)checks.push("FRAME_TRANSFORM_OR_DEFINITION_REQUIRED");
  if(k.configuration!==novel.configuration)checks.push("CONFIGURATION_VARIANT");
  if(k.epoch!==novel.epoch)checks.push("TIME_VARIANT");
  const kRefs=k.source_refs.filter(s=>srcs.has(s));
  if(!targetRefs.length||!kRefs.length)checks.push("EVIDENCE_GAP");
  else if(!kRefs.some(s=>targetRefs.includes(s)))checks.push("SOURCE_LINEAGE_DISJOINT");
  // A repeated Object_ID label is a claim, never proof; independent source lines
  // cannot be collapsed into one R0 identity without qualified reconciliation.
  const exactId=novel.object_id&&novel.object_id===k.object_id;
  const state=checks.length?"REVIEW_DIFFERENCE":exactId?"SAME_ID_CLAIM_REQUIRES_PROOF":"TYPED_ALIGNMENT_CANDIDATE";
  candidates.push({known_object_id:k.object_id,state,checks,permitted_known_evidence:kRefs,
    semantic_type:k.semantic_type,auto_merge:false,existing_object_authority_verified:false});
 }
 candidates.sort((a,b)=>a.checks.length-b.checks.length||a.known_object_id.localeCompare(b.known_object_id));
 return {schema:KNOWN_SCHEMA,status:"SOURCE_REVIEW_ONLY",semantic_type:novel.semantic_type,
  matched_candidates:candidates.slice(0,max_candidates),visible_candidate_count:candidates.length,
  missing_candidate_coverage:candidates.length>max_candidates,novel_permitted_source_refs:targetRefs,
  objects_minted:0,semantic_writes:0,empirical_solution_verified:false,
  unresolved:["meaning and source-independent validation","current accepted Object_ID and owner authority","config/epoch/unit/frame context","source rights"]};
}
/** Reuse only explicitly typed CCC route declarations whose route keys exist in current source registry.
 * Note: registry presence does NOT verify installed host tooling or mathematical correctness.
 */
export function planQualifiedOperator({registry,problem,bindings,authorised_source_ids=[],selector=null}={}){
 validateRegistry(registry);
 if(!obj(registry)||registry.state!=="GIT_SOURCE_ONLY_NOT_CANONICAL"||!Array.isArray(registry.records)||!obj(problem)||
  !good(problem.semantic_type)||!obj(problem.dimensions)||!arr(problem.source_refs)||!Array.isArray(bindings)||
  bindings.length>500||!arr(authorised_source_ids)||(selector!==null&&!good(selector)))throw Error("INVALID_OPERATOR_REQUEST");
 const permitted=new Set(authorised_source_ids),sourceRefs=problem.source_refs.filter(x=>permitted.has(x));
 const routes=new Map(registry.records.filter(x=>x.category==="ccc_route"&&x.admission==="SOURCE_REGISTRY_ONLY").map(x=>[x.source_key,x]));
 const selected=[];
 for(const b of bindings){
  if(!obj(b)||!good(b.route_key)||!good(b.input_type)||!obj(b.required_dimensions))throw Error("INVALID_OPERATOR_BINDING");
  if(!routes.has(b.route_key))continue;
  if(b.input_type!==problem.semantic_type||!dimEqual(b.required_dimensions,problem.dimensions))continue;
  const blockers=[];
  // A selector label is only a source-catalogue declaration, never a verified host ACL.
  if(selector===null)blockers.push("SELECTOR_SCOPE_UNDECLARED");
  else if(!Array.isArray(routes.get(b.route_key).selector_sources)||!routes.get(b.route_key).selector_sources.includes(selector))
   blockers.push("SELECTOR_ROUTE_NOT_DECLARED");
  if(!sourceRefs.length)blockers.push("EVIDENCE_SOURCE_REQUIRED");
  if(Object.keys(problem.dimensions).length>0){
   if(!obj(problem.units)||!Object.keys(problem.dimensions).every(f=>good(problem.units[f])))blockers.push("UNITS_UNDECLARED");
   else if(!obj(b.required_units)||!Object.keys(b.required_dimensions).every(f=>good(b.required_units[f])))
    blockers.push("METHOD_UNITS_UNDECLARED");
   else if(!Object.keys(b.required_dimensions).every(f=>b.required_units[f]===problem.units[f]))
    blockers.push("UNIT_CONVERSION_METHOD_REQUIRED");
  }
  if(b.frame && b.frame!==problem.frame)blockers.push("FRAME_TRANSFORMATION_REQUIRED");
  if(b.epoch_required&&!good(problem.epoch))blockers.push("EPOCH_REQUIRED");
  if(b.configuration_required&&!good(problem.configuration))blockers.push("CONFIGURATION_REQUIRED");
  if(!good(b.qualified_method_source))blockers.push("INDEPENDENT_METHOD_SOURCE_REQUIRED");
  else if(!permitted.has(b.qualified_method_source))blockers.push("METHOD_SOURCE_NOT_AUTHORISED");
  blockers.push("HOST_CAPABILITY_LEASE_AND_DB_R_READBACK_REQUIRED");
  selected.push({route_key:b.route_key,state:"EXPLICIT_TYPED_OPERATOR_CANDIDATE",blockers,
    solver_invoked:false,results_generated:false});
 }
 return {schema:"LOAD-QUALIFIED-OPERATOR-PLAN/0.1",status:"SOURCE_ONLY_NO_EXECUTION",
  semantic_type:problem.semantic_type,operator_candidates:selected,
  source_references:sourceRefs,model_validated:false,computation_executed:false,
  reinforcement:"Independent test/measurement/falsifier and source provenance must be evaluated after an authenticated solver run.",
  numeric_result:null,object_ids_minted:0};
}
