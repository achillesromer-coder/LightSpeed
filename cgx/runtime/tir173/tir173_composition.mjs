import {validateDictionary,normaliseRole,makeCapsule,projectLenses,encodeBinaryTransport,decodeBinaryTransport,TIRError} from './tir173_core.mjs';
const must=(c,code)=>{if(!c)throw new TIRError(code);};
/** The same semantic node is projected at different scales; unknown detail is not imputed. */
export function buildSparseGraph(dictionary,{objects=[],edges=[]}={}) {
  validateDictionary(dictionary);must(Array.isArray(objects)&&objects.length<=173&&Array.isArray(edges)&&edges.length<=2048,'GRAPH_BOUNDS');
  const nodes=new Map(), paths=new Set();
  for(const c of objects){projectLenses(dictionary,c);must(!nodes.has(c.object_ref),'DUPLICATE_OBJECT_ID');
   const p=c.local_path.join('/');must(!paths.has(p),'DUPLICATE_LOCAL_ADDRESS');paths.add(p);nodes.set(c.object_ref,c);}
  const rels=[];
  for(const e of edges){must(e&&['part_of','adjacent_to','interacts_with','derived_from','references','mirrors','supports','contradicts'].includes(e.predicate),'RELATION_NOT_REGISTERED');must(nodes.has(e.from)&&nodes.has(e.to),'DANGLING_GRAPH_EDGE');must(e.from!==e.to,'SELF_EDGE_NOT_AUTHORIZED');rels.push({...e});}
  // Containment must be acyclic; cross-relations may be recursive.
  const contain=rels.filter(e=>e.predicate==='part_of');
  const next=new Map();for(const e of contain) {const arr=next.get(e.from)||[];arr.push(e.to);next.set(e.from,arr);}
  const visit=(id,stack=new Set(),done=new Set())=>{if(stack.has(id))throw new TIRError('CONTAINMENT_CYCLE');if(done.has(id))return;stack.add(id);for(const child of next.get(id)||[])visit(child,stack,done);stack.delete(id);done.add(id);};
  const done=new Set();for(const id of nodes.keys())visit(id,new Set(),done);
  return {schema:'cgx.tir173.graph/0.2',nodes:[...nodes.values()],edges:rels,
   projection:'REVIEW_ONLY',source_dictionary_sha256:dictionary.source_sha256,automatic_execution:false};
}
export function dualScale(graph,objectRef,{coarse='summary',fine='evidence'}={}) {
 const n=graph.nodes.find(o=>o.object_ref===objectRef);must(n,'OBJECT_NOT_IN_GRAPH');
 const coarseVal=n.scale_lenses.coarse,fineVal=n.scale_lenses.fine;
 return {object_ref:objectRef,coarse:{lens:coarse,status:coarseVal?.status||'NO_DATA',value:coarseVal?.value??null},
 fine:{lens:fine,status:fineVal?.status||'NO_DATA',value:fineVal?.status==='HYDRATED'?fineVal.value:null},
 gap:{missing_detail:fineVal?.status!=='HYDRATED',inference_requires_source:true},
 identity_preserved:true};
}
/** Adapts existing Neo review AST. Does not reinterpret trinary UI strings as geometric identities. */
export function bridgeNeoPlan(dictionary,plan){
 validateDictionary(dictionary);must(plan?.schema==='cgx.geometry.ast/0.1'&&plan.effects_performed===false&&plan.authority_transfer===false&&plan.status==='DRY_RUN_REVIEW_ONLY','NEO_PLAN_AUTHORITY');
 const shape=plan.slot??plan.left;must(typeof shape==='string','NEO_PLAN_NO_ROLE');const slot=normaliseRole(shape);
 const node=makeCapsule(dictionary,{path:[slot],shape:slot,label:dictionary.roles[slot-1].name,object_ref:`review:neo:${slot}`,source_ref:'review:source',frame:'local',unit:'m',magnitude:1,
   state:{basis:'review:orientation',trit:0,validity:'UNRESOLVED'},fine:{level:1,status:'UNRESOLVED'},coarse:{level:0,status:'REFERENCE_ONLY'}});
 return {schema:'cgx.tir173.bridge/0.2',legacy_schema:plan.schema,legacy_kind:plan.kind,capsule:node,
  source_dictionary_sha256:dictionary.source_sha256,promotion_allowed:false,source_hydrated:false};
}
export function compileShapeRecipe(dictionary,command) {
 validateDictionary(dictionary);must(typeof command==='string'&&command.length<200,'RECIPE_BOUNDS');
 const s=command.trim();let m=/^shape\s+(T173:\d{3})(?:\s+at\s+([1-8]))?$/i.exec(s);
 if(m){let i=normaliseRole(m[1]);return {schema:'cgx.tir173.recipe/0.2',operator:'select',shape_role:i,depth:Number(m[2]||1),state:'PLAN_ONLY',native_execution:false};}
 m=/^compose\s+(T173:\d{3})\s+(part_of|adjacent_to|interacts_with|mirrors|references)\s+(T173:\d{3})(?:\s+at\s+([1-8]))?$/i.exec(s);
 if(m){let left=normaliseRole(m[1]),right=normaliseRole(m[3]);return {schema:'cgx.tir173.recipe/0.2',operator:'compose',left_shape_role:left,right_shape_role:right,typed_relation:m[2],same_role_instances:left===right,depth:Number(m[4]||1),state:'PLAN_ONLY',native_execution:false,source_data_required:true};}
 throw new TIRError('NO_TYPED_RECIPE_MATCH');
}
export function projectSynchronized(dictionary,capsule,graph=null){const r=projectLenses(dictionary,capsule);if(graph)r.human.relation_count=graph.edges.length;const bytes=encodeBinaryTransport(capsule);
 const restored=decodeBinaryTransport(bytes);must(JSON.stringify(restored)===JSON.stringify(capsule),'ROUNDTRIP_FAILED');
 return {...r,transport:{bytes:bytes.length,hex_prefix:Array.from(bytes.slice(0,48),b=>b.toString(16).padStart(2,'0')).join(''),exact_roundtrip:true}};
}