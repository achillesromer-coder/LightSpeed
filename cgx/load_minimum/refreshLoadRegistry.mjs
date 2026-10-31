#!/usr/bin/env node
/** Rebuild LOAD source-only registry by reference from existing checked-out CGX registries.
 * No provider fetch, native mutation, execution or publishing.
 * --check: detect drift; --write: explicitly refresh the REVIEW JSON only.
 */
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const OUTPUT='cgx/load_minimum/online_registry_projection_2026-10-28.json';
const SELECTORS=['achilles','neo','athene','raphael','cognigrex','romer-grex','eco-grex','emassc','lightspeed'];
const [P0,P1,P2,P3,P4]=[
'cgx/domain_templates/first_file_conversion_registry.json',
'cgx/domain_templates/source_format_adapter_registry.json',
'cgx/domain_templates/toolkit_registry.json',
'cgx/domain_templates/plugin_selector_registry.json',
'cgx/load_minimum/filespace_feature_registry.json',
];
const sourcePaths=[P0,P1,P2,P3,P4,...SELECTORS.map(x=>'plugins/packages/'+x+'/references/capabilities.json')];
const file=p=>readFileSync(resolve(ROOT,p));
const blob=b=>createHash('sha1').update(Buffer.from('blob '+b.length+'\0')).update(b).digest('hex');
const data=Object.fromEntries(sourcePaths.map(p=>{const bytes=file(p);return [p,{sha:blob(bytes),body:JSON.parse(bytes.toString('utf8'))}]}));
const entries=[],frontier=[];
const add=(category,source_key,display,p,extra={})=>{
 if(!source_key)throw Error('missing source key: '+p);
 entries.push({category,source_key,display:String(display||source_key),source_registry:p,source_git_blob:data[p].sha,...extra});
};
for(const x of data[P0].body.mappings)add('conversion_source',x.mapping_id,x.source_name,P0,{
 candidate_object_id:x.semantic_object_id??null,source_drive_id:x.source_drive_id??null,
 source_sha256:x.source_sha256??null,source_media_type:x.media_type??null,owner_domain:x.domain??null,
 source_target:x.semantic_target??null,source_granularity:'NATIVE_SOURCE_REFERENCE',
 admission:'SOURCE_REGISTRY_ONLY',native_absorbed:false,source_rights:'NOT_RECHECKED',role:'SOURCE_MAPPING',
 evidence_ceiling:x.evidence_ceiling??null
});
for(const x of data[P1].body.adapters)add('format_adapter',x.adapter_id,x.adapter_id,P1,{
 extensions:x.extensions??[],projection_kinds:x.projection_kinds??[],implementation_declared:x.admission_state??'UNVERIFIED',
 admission:'SOURCE_REGISTRY_ONLY',live_provider_verified:false
});
for(const x of data[P2].body.toolkits)add('toolkit',x.id,x.id,P2,{
 capabilities:x.capabilities??[],kind:x.kind??null,binding:x.binding??null,
 registry_state:x.state??'NOT_SPECIFIED',admission:'SOURCE_REGISTRY_ONLY',installed_online:false
});
for(const [k,x] of Object.entries(data[P3].body.selectors))add('selector',k,k,P3,{
 kind:x.kind??null,owner_domain:x.domain??x.default_domain??null,admission:'SOURCE_REGISTRY_ONLY',installed_online:false
});
for(const [k,x] of Object.entries(data[P4].body.actions))add('filespace_action',k,x.label,P4,{
 targets:x.targets,mode:x.mode,admission:'SOURCE_REGISTRY_ONLY',installed_online:false
});
const routes=new Map(),routeCounts={};
for(const name of SELECTORS){
 const p='plugins/packages/'+name+'/references/capabilities.json';
 const part=data[p].body.routes??{};routeCounts[name]=Object.keys(part).length;
 for(const [k,x] of Object.entries(part)){
  const signature=JSON.stringify({state:x.state??null,kind:x.kind??null,handler:x.handler??null,uses:x.uses??[],read_only:x.ro??null});
  if(!routes.has(k))routes.set(k,[]);
  routes.get(k).push({selector:name,signature});
 }
}
for(const [k,values] of [...routes.entries()].sort((a,b)=>a[0].localeCompare(b[0]))){
 const count=new Set(values.map(x=>x.signature)).size;
 const selector_sources=values.map(x=>x.selector);
 const primarySelector=selector_sources.includes('cognigrex')?'cognigrex':selector_sources[0];
 const primary='plugins/packages/'+primarySelector+'/references/capabilities.json';
 const route_source_proofs=Object.fromEntries(selector_sources.map(selector=>{
  const source_registry='plugins/packages/'+selector+'/references/capabilities.json';
  return [selector,{source_registry,git_blob:data[source_registry].sha}];
 }));
 add('ccc_route',k,k,primary,{
  route_source_proofs,selector_sources,route_signatures:count,
  admission:count===1?'SOURCE_REGISTRY_ONLY':'FRONTIER_CONFLICT',installed_online:false,provider_readback:false
 });
 if(count>1)frontier.push({category:'ccc_route',source_key:k,reason:'CROSS_SELECTOR_VARIANCE',selectors:selector_sources});
}
for(const [k,v] of Object.entries(data[P4].body.inherited_function_decomposition??{}))
 add('function_family',k,v,P4,{admission:'SOURCE_REGISTRY_ONLY',qualified_implementations:0});
const byDrive=new Map(),semantics=new Map();
for(const x of entries.filter(x=>x.category==='conversion_source')){
 if(x.source_drive_id){const s=byDrive.get(x.source_drive_id)??new Set();s.add(x.source_sha256??'UNKNOWN');byDrive.set(x.source_drive_id,s)}
 if(x.candidate_object_id){if(!semantics.has(x.candidate_object_id))semantics.set(x.candidate_object_id,[]);semantics.get(x.candidate_object_id).push(x.source_key)}
}
for(const [id,hashes] of byDrive)if(hashes.size>1)frontier.push({reason:'SAME_PROVIDER_ID_DIFFERENT_SHA',provider_id:id,hash_count:hashes.size});
for(const [id,refs] of semantics)if(refs.length>1)frontier.push({reason:'MULTIPLE_MAPPING_SAME_SEMANTIC_ID',candidate_object_id:id,mapping_count:refs.length,mapping_refs:refs});
const duplicate=new Set();for(const x of entries){const k=x.category+'/'+x.source_key;if(duplicate.has(k))throw Error('duplicate '+k);duplicate.add(k)}
const byCat={};for(const x of entries)byCat[x.category]=(byCat[x.category]??0)+1;
const output={
 schema:'LOAD-ALEXANDRIA-SOURCE-REGISTRY-PROJECTION/0.1',state:'GIT_SOURCE_ONLY_NOT_CANONICAL',
 generated_at:'2026-10-28',parent:'Cognigrex.cgx',file_space:'LOAD.cgx',
 purpose:'Reference-preserving online catalogue compiling existing Git source adapters, toolkits, selectors and CCC functional routes',
 source_repo:'achillesromer-coder/LightSpeed',source_branch_main:'main',scoped_review_branch:'review/load-alexandria-minimal-20261028',
 source_registries:Object.fromEntries(Object.entries(data).map(([k,v])=>[k,{git_blob:v.sha}])),
 summary:{record_count:entries.length,record_categories:byCat,selector_route_counts:routeCounts,distinct_capability_routes:routes.size,
 source_drive_id_count:byDrive.size,shared_candidate_semantic_ids:[...semantics.values()].filter(x=>x.length>1).length,
 frontier_count:frontier.length,native_accepted:0,native_host_verified:false,source_bodies_copied:0},
 invariants:[
  'one authoritative source identity per native source, no duplicate CGX Object_ID mint',
  'cross-selector route key may share a name, but divergent signatures must stay Frontier',
  'declared implementation status is not live installation or runtime proof',
  'R0 provider bytes and legal rights remain with original source provider',
  'no programmatic network fetch, file deletion, host execution or DBR writes',
  'all records are discoverable INDEX REFERENCES, not accepted CGX semantic objects'
 ],records:entries,frontier
};
const result=JSON.stringify(output,null,2)+'\n';
const prior=file(OUTPUT).toString('utf8');
const drift=prior!==result;
if(process.argv.includes('--write')){writeFileSync(resolve(ROOT,OUTPUT),result);console.log(JSON.stringify({review_only:true,updated:true,record_count:entries.length,drift}));}
else {console.log(JSON.stringify({review_only:true,drift,record_count:entries.length,categories:byCat,frontier:frontier.length}));if(process.argv.includes('--check')&&drift)process.exitCode=1;}
