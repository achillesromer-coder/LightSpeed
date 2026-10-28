/** LOAD.cgx online registry query / scoped hydration planner.
 * This module never performs provider I/O, installation, mutation or publication.
 * The native host must independently check authenticated rights and DBR.
 */
export const SCHEMA = "LOAD-ALEXANDRIA-SOURCE-REGISTRY-PROJECTION/0.1";
const KEY = /^[a-z0-9][a-z0-9_.:/-]{0,199}$/i;
const SHA = /^[0-9a-f]{40}$/;
const allowedCats = new Set(["conversion_source","format_adapter","toolkit","selector","filespace_action","ccc_route","function_family"]);
const isObj = o => o !== null && typeof o === "object" && !Array.isArray(o);
const safeTerm = x => typeof x === "string" && x.length > 0 && x.length <= 200 && !/[\u0000-\u001f]/.test(x);
export function validateRegistry(registry) {
 if(!isObj(registry) || registry.schema !== SCHEMA || registry.state !== "GIT_SOURCE_ONLY_NOT_CANONICAL") throw Error("UNTRUSTED_REGISTRY");
 if(!Array.isArray(registry.records) || !Array.isArray(registry.frontier) || !isObj(registry.source_registries)) throw Error("INVALID_REGISTRY");
 if(registry.summary?.native_accepted !== 0 || registry.summary?.native_host_verified !== false || registry.summary?.source_bodies_copied !== 0) throw Error("UNSUPPORTED_AUTHORITY_CLAIM");
 const seen=new Set();
 for (const [p,info] of Object.entries(registry.source_registries)){
  if(!p.startsWith("cgx/") && !p.startsWith("plugins/"))throw Error("UNEXPECTED_SOURCE_REGISTRY");
  if(!SHA.test(info.git_blob))throw Error("UNVERIFIED_GIT_BLOB");
 }
 for(const r of registry.records){
  if(!isObj(r)||!allowedCats.has(r.category)||!safeTerm(r.source_key)||!KEY.test(r.source_key))throw Error("INVALID_RECORD");
  const id=r.category+"/"+r.source_key;
  if(seen.has(id))throw Error("DUPLICATE_REGISTRY_KEY:"+id);
  seen.add(id);
  if(!Object.hasOwn(registry.source_registries,r.source_registry)||!SHA.test(r.source_git_blob)||registry.source_registries[r.source_registry].git_blob!==r.source_git_blob)throw Error("SOURCE_PROOF_MISMATCH");
  if(r.category==="ccc_route"){
   if(!Array.isArray(r.selector_sources)||!r.selector_sources.length||!isObj(r.route_source_proofs)||
      new Set(r.selector_sources).size!==r.selector_sources.length||
      Object.keys(r.route_source_proofs).length!==r.selector_sources.length)
    throw Error("CCC_ROUTE_PROVENANCE_MISMATCH");
   for(const selector of r.selector_sources){
    const p='plugins/packages/'+selector+'/references/capabilities.json';
    const proof=r.route_source_proofs[selector];
    if(!isObj(proof)||proof.source_registry!==p||!isObj(registry.source_registries[p])||
       proof.git_blob!==registry.source_registries[p].git_blob)
     throw Error("CCC_ROUTE_PROVENANCE_MISMATCH");
   }
   if(!r.selector_sources.some(selector=>r.route_source_proofs[selector].source_registry===r.source_registry))
    throw Error("CCC_ROUTE_PROVENANCE_MISMATCH");
  }
  if(r.native_absorbed===true||r.installed_online===true)throw Error("UNVERIFIED_INSTALLATION");
 }
 return {valid:true,source_registry_count:Object.keys(registry.source_registries).length,reference_count:seen.size,frontier_count:registry.frontier.length};
}
const compact = r => ({
 category:r.category, source_key:r.source_key, display:r.display, source_registry:r.source_registry,
 git_blob:r.source_git_blob, state:r.admission, domain:r.owner_domain??null,
 candidate_object_id:r.candidate_object_id??null, source_target:r.source_target??null,
 adapter_state:r.implementation_declared??null, toolkit_binding:r.binding??null,
 selectors:r.selector_sources??null
});
export function searchLoad(registry,{query="",category=null,domain=null,limit=25}={}){
 validateRegistry(registry);
 if(typeof query!=="string"||query.length>120||!Number.isSafeInteger(limit)||limit<1||limit>100||!(!category||allowedCats.has(category)))throw Error("INVALID_QUERY");
 const term=query.toLocaleLowerCase();
 let matches=registry.records.filter(r=>(!category||r.category===category)&&(!domain||r.owner_domain===domain)&&
  (r.source_key.toLocaleLowerCase().includes(term)||r.display.toLocaleLowerCase().includes(term)));
 return {status:"SOURCE_INDEX_ONLY",total:matches.length,matches:matches.slice(0,limit).map(compact)};
}
export function resolveLoad(registry,{category,sourceKey}={}){
 validateRegistry(registry);
 if(!allowedCats.has(category)||!safeTerm(sourceKey))throw Error("INVALID_RESOLVE");
 const exact=registry.records.filter(x=>x.category===category && x.source_key===sourceKey);
 if(exact.length!==1) return {status:exact.length?"AMBIGUOUS":"NOT_FOUND",count:exact.length};
 const r=exact[0];const conflicts=registry.frontier.filter(f=>f.source_key===r.source_key||
  f.candidate_object_id===r.candidate_object_id && r.candidate_object_id!=null && f.reason==="MULTIPLE_MAPPING_SAME_SEMANTIC_ID");
 return {status:conflicts.length?"FRONTIER_REVIEW":"REFERENCE_ONLY",record:compact(r),conflicts,
  native_object_id:null,canonical_writes:0,install_executed:false};
}
export function planScopedLoad(registry,{fileSpace,owner,objectId=null,kind="all",offline=true,include=null}={}){
 const v=validateRegistry(registry);
 if(!safeTerm(fileSpace)||!safeTerm(owner))throw Error("INVALID_TARGET");
 if(objectId!=null&&!safeTerm(objectId))throw Error("INVALID_OBJECT_ID");
 if(include!=null&&!Array.isArray(include))throw Error("INVALID_SELECTOR");
 // Universal LOAD remains searchable; child-equipping references only its own source mappings.
 // Do not derive semantic ownership from arbitrary filename substrings.
 const domainByFileSpace={"Romer.cgx":"romer","Eco.cgx":"eco","EMASSC.cgx":"emassc","LS.cgx":"lightspeed"};
 const scopedDomain=Object.hasOwn(domainByFileSpace,fileSpace)?domainByFileSpace[fileSpace]:null;
 const permittedCrossFamily=fileSpace==="Cognigrex.cgx"||fileSpace==="LOAD.cgx";
 const selected=registry.records.filter(r=>(!include||include.includes(r.category))&&
   (r.category!=="conversion_source" || permittedCrossFamily || (scopedDomain!==null&&r.owner_domain===scopedDomain)));
 const frontier=new Set(registry.frontier.flatMap(f=>f.mapping_refs??[]));
 const blocked=selected.filter(r=>frontier.has(r.source_key)).map(r=>r.source_key);
 return {schema:"LOAD-SCOPED-FILESPACE-PLAN/0.1",state:objectId?"HOST_PREFLIGHT_REQUIRED":"EXACT_ID_REQUIRED",
  target:{fileSpace,owner,objectId},kind,offline_minimum:offline!==false,source_references:selected.length,
  source_metadata_only:true,blocked_mapping_ids:blocked,
  registry_count:v.source_registry_count,external_fetch:false,created_object_ids:0,
  source_bodies_copied:0,ccc_installed:false,dbr_mutated:false,
  requires:["current accepted object and source-lineage identity","scope owner/ACL/rights","alias collision check",
            "signed host/lease binding","independent DBR and receiver readback"]};
}
