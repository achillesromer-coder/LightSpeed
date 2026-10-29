import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {validateRegistry,searchLoad,resolveLoad,planScopedLoad} from './loadOnlineRegistry.mjs';
const data=JSON.parse(readFileSync(new URL('./online_registry_projection_2026-10-28.json',import.meta.url),'utf8'));
const copy=x=>JSON.parse(JSON.stringify(x));
test('Git catalogue is valid and source linked',()=>assert.equal(validateRegistry(data).reference_count,131));
test('all nine selectors preserved',()=>assert.equal(searchLoad(data,{category:'selector',limit:50}).total,9));
test('45 unique CCC route keys indexed',()=>assert.equal(searchLoad(data,{category:'ccc_route',limit:100}).total,45));
test('adapter is discoverable without claiming installed execution',()=>{
 const x=resolveLoad(data,{category:'format_adapter',sourceKey:'json-stdlib-v0.1'});
 assert.equal(x.status,'REFERENCE_ONLY');assert.equal(x.install_executed,false);
});
test('version variants do not silently merge',()=>{
 assert.equal(resolveLoad(data,{category:'conversion_source',sourceKey:'FF-M1-BASEKM-FCSTD-001'}).status,'FRONTIER_REVIEW');
});
test('missing exact ID blocks acceptance',()=>assert.equal(planScopedLoad(data,{fileSpace:'Eco.cgx',owner:'Athene'}).state,'EXACT_ID_REQUIRED'));
test('supplied ID permits only host preflight',()=>{
 const x=planScopedLoad(data,{fileSpace:'Eco.cgx',owner:'Athene',objectId:'cgx:fixture'});
 assert.equal(x.state,'HOST_PREFLIGHT_REQUIRED');assert.equal(x.ccc_installed,false);assert.equal(x.dbr_mutated,false);
});
test('cannot assert native acceptance by editing metadata',()=>{
 const x=copy(data);x.summary.native_accepted=5;assert.throws(()=>validateRegistry(x),/UNSUPPORTED_AUTHORITY_CLAIM/);
});
test('cannot replace trusted source blob',()=>{
 const x=copy(data);x.records[0].source_git_blob='0'.repeat(40);assert.throws(()=>validateRegistry(x),/SOURCE_PROOF_MISMATCH/);
});
test('cannot duplicate categorical key',()=>{
 const x=copy(data);x.records.push(copy(x.records[0]));assert.throws(()=>validateRegistry(x),/DUPLICATE_REGISTRY_KEY/);
});
test('reject invalid search quota',()=>assert.throws(()=>searchLoad(data,{limit:500}),/INVALID_QUERY/));
test('reject empty target',()=>assert.throws(()=>planScopedLoad(data,{fileSpace:'',owner:'Athene'}),/INVALID_TARGET/));

test('cross-family discovery does not copy other domains into a child',()=>{
 const from=data.records.filter(r=>r.category==='conversion_source');
 const shared=data.records.length-from.length;
 for(const [fileSpace,domain] of [['Romer.cgx','romer'],['Eco.cgx','eco'],['EMASSC.cgx','emassc'],['LS.cgx','lightspeed']]){
  const plan=planScopedLoad(data,{fileSpace,owner:'test-owner',objectId:'cgx:test'});
  assert.equal(plan.source_references,shared+from.filter(r=>r.owner_domain===domain).length);
  assert.equal(plan.source_bodies_copied,0);
 }
});
test('unregistered family does not inherit another domains source mappings',()=>{
 const p=planScopedLoad(data,{fileSpace:'Unregistered.cgx',owner:'test-owner',objectId:'cgx:test'});
 const publicShared=data.records.filter(r=>r.category!=='conversion_source').length;
 assert.equal(p.source_references,publicShared);assert.equal(p.external_fetch,false);
});

test('each CCC route retains source-blob evidence from its actual declaring selectors',()=>{
 const routes=data.records.filter(r=>r.category==='ccc_route');
 assert.equal(routes.length,45);
 for(const r of routes){
  assert.ok(r.selector_sources.some(s=>r.route_source_proofs[s].source_registry===r.source_registry));
  for(const selector of r.selector_sources){
   const p=`plugins/packages/${selector}/references/capabilities.json`;
   assert.equal(r.route_source_proofs[selector].source_registry,p);
   assert.equal(r.route_source_proofs[selector].git_blob,data.source_registries[p].git_blob);
  }
 }
});
test('reject forged CCC route attribution to a selector that never declared it',()=>{
 const x=copy(data),r=x.records.find(v=>v.category==='ccc_route'&&v.source_key==='cad.freecad');
 const p='plugins/packages/cognigrex/references/capabilities.json';
 assert.ok(!r.selector_sources.includes('cognigrex'));
 r.source_registry=p;r.source_git_blob=x.source_registries[p].git_blob;
 assert.throws(()=>validateRegistry(x),/CCC_ROUTE_PROVENANCE_MISMATCH/);
});
test('reject missing or altered selector-level route provenance',()=>{
 const x=copy(data),r=x.records.find(v=>v.category==='ccc_route'&&v.source_key==='cad.freecad');
 delete r.route_source_proofs.raphael;
 assert.throws(()=>validateRegistry(x),/CCC_ROUTE_PROVENANCE_MISMATCH/);
 const y=copy(data),q=y.records.find(v=>v.category==='ccc_route'&&v.source_key==='cad.freecad');
 q.route_source_proofs.raphael.git_blob='0'.repeat(40);
 assert.throws(()=>validateRegistry(y),/CCC_ROUTE_PROVENANCE_MISMATCH/);
});

test('checked-out source bytes match all 14 projected Git blob fingerprints',()=>{
 const sources=Object.entries(data.source_registries);
 assert.equal(sources.length,14);
 for(const [p,proof] of sources){
  assert.match(p,/^(cgx|plugins)\/[a-zA-Z0-9_./-]+$/);
  assert.ok(!p.split('/').includes('..'));
  const bytes=readFileSync(new URL('../../'+p,import.meta.url));
  const gitBlob=createHash('sha1').update(Buffer.from('blob '+bytes.length+'\0')).update(bytes).digest('hex');
  assert.equal(gitBlob,proof.git_blob,'SOURCE_BYTES_DRIFT: '+p);
 }
});
test('all projected CCC routes are present in their actual declaring selector files',()=>{
 const routes=data.records.filter(r=>r.category==='ccc_route');
 let declarations=0;
 for(const r of routes){
  for(const selector of r.selector_sources){
   const p='plugins/packages/'+selector+'/references/capabilities.json';
   const body=JSON.parse(readFileSync(new URL('../../'+p,import.meta.url),'utf8'));
   assert.ok(Object.hasOwn(body.routes??{},r.source_key),'ROUTE_NOT_DECLARED: '+selector+'/'+r.source_key);
   declarations++;
  }
 }
 assert.equal(routes.length,45);
 assert.equal(declarations,265);
 assert.equal(declarations,Object.values(data.summary.selector_route_counts).reduce((n,x)=>n+x,0));
});

test('Eco relation grammar collision and version mismatch fail closed without canonical identity', async()=>{
 const {inspectRelationGrammar}=await import('./inspectRelationGrammar.mjs');
 const eco=JSON.parse(readFileSync(new URL('../domain_templates/eco_relation_registry.json',import.meta.url),'utf8'));
 const shared=JSON.parse(readFileSync(new URL('../domain_templates/relation_qualifier_contract.json',import.meta.url),'utf8'));
 const result=inspectRelationGrammar(eco,shared);
 assert.equal(result.stage,'SOURCE_REVIEW_ONLY');
 assert.equal(result.status,'HOLD');
 assert.equal(result.qualified_object_id,null);
 assert.equal(result.native_admitted,false);
 assert.equal(result.dbr_readback_verified,false);
 const collision=result.issues.find(i=>i.code==='RELATION_TYPE_NAMESPACE_AMBIGUITY'&&i.relation_id==='MODIFIES');
 assert.deepEqual(collision.source_declarations.map(x=>x.family),['process','intervention']);
 const version=result.issues.find(i=>i.code==='RELATION_SCHEMA_COMPATIBILITY_HOLD');
 assert.equal(version.declared_extends,'CGX-RELATION-QUALIFIER/0.1');
 assert.equal(version.available_contract,'CGX-RELATION-QUALIFIER/0.2');
 // Synthetic correction proves the checker can distinguish a clean source schema,
 // not that the real Eco registry has been corrected or owner-approved.
 const synthetic=copy(eco);
 synthetic.extends=shared.schema;
 synthetic.families.intervention.find(x=>x.id==='MODIFIES').id='MODIFIES_INTERVENTION_SYNTHETIC';
 const clear=inspectRelationGrammar(synthetic,shared);
 assert.equal(clear.status,'HOLD'); // Lexical crosswalks still require owner qualification.
 assert.equal(clear.unresolved_crosswalk_count,6);
 assert.equal(clear.issues.length,0);
 assert.equal(clear.native_admitted,false);
 assert.equal(clear.qualified_object_id,null);
});

test('shared/Eco relation lexical reuse is preserved as unresolved owner crosswalk candidates', async()=>{
 const {inspectRelationGrammar}=await import('./inspectRelationGrammar.mjs');
 const eco=JSON.parse(readFileSync(new URL('../domain_templates/eco_relation_registry.json',import.meta.url),'utf8'));
 const shared=JSON.parse(readFileSync(new URL('../domain_templates/relation_qualifier_contract.json',import.meta.url),'utf8'));
 const result=inspectRelationGrammar(eco,shared);
 const byId=new Map(result.crosswalk_candidates.map(x=>[x.relation_id,x]));
 assert.deepEqual([...byId.keys()].sort(),['DERIVED_FROM','EVIDENCED_BY','GATED_BY','HAS_CRITERION','MITIGATED_BY','USES_INPUT']);
 assert.equal(result.crosswalk_candidates.length,6);
 assert.equal(byId.get('USES_INPUT').domain_family,'recipe_test');
 assert.equal(byId.get('USES_INPUT').shared_family,'process');
 assert.equal(byId.get('MITIGATED_BY').domain_family,'intervention');
 assert.equal(byId.get('MITIGATED_BY').shared_family,'risk');
 assert.equal(byId.get('DERIVED_FROM').shared_family,'provenance');
 for(const candidate of result.crosswalk_candidates){
  assert.equal(candidate.classification,'UNRESOLVED_SHARED_TYPE_REUSE');
  assert.equal(candidate.qualified_object_id,null);
  assert.equal(candidate.owner_qualified,false);
  assert.equal(candidate.native_admitted,false);
 }
 assert.equal(result.status,'HOLD'); // Real Eco /0.1 contract and MODIFIES duplication remain.
 assert.equal(result.dbr_readback_verified,false);
 const synthetic=copy(eco);
 synthetic.extends=shared.schema;
 synthetic.families.intervention.find(x=>x.id==='MODIFIES').id='MODIFIES_INTERVENTION_SYNTHETIC';
 const structurallyClean=inspectRelationGrammar(synthetic,shared);
 assert.equal(structurallyClean.status,'HOLD');
 assert.equal(structurallyClean.unresolved_crosswalk_count,6);
 assert.equal(structurallyClean.crosswalk_candidates.length,6);
 assert.ok(structurallyClean.crosswalk_candidates.every(x=>x.owner_qualified===false));
});


test('structurally valid schemas still HOLD when shared lexical crosswalks lack owner proof', async()=>{
 const {inspectRelationGrammar}=await import('./inspectRelationGrammar.mjs');
 const eco=JSON.parse(readFileSync(new URL('../domain_templates/eco_relation_registry.json',import.meta.url),'utf8'));
 const shared=JSON.parse(readFileSync(new URL('../domain_templates/relation_qualifier_contract.json',import.meta.url),'utf8'));
 const corrected=copy(eco);
 corrected.extends=shared.schema;
 corrected.families.intervention.find(x=>x.id==='MODIFIES').id='MODIFIES_INTERVENTION_SYNTHETIC';
 const unresolved=inspectRelationGrammar(corrected,shared);
 assert.equal(unresolved.issues.length,0);
 assert.equal(unresolved.crosswalk_candidates.length,6);
 assert.equal(unresolved.unresolved_crosswalk_count,6);
 assert.equal(unresolved.status,'HOLD');
 assert.equal(unresolved.native_admitted,false);
 assert.equal(unresolved.dbr_readback_verified,false);
 // No shared lexical overlap is a structural check only, never native acceptance.
 const isolated=copy(shared);isolated.shared_relation_types={};
 const noOverlap=inspectRelationGrammar(corrected,isolated);
 assert.equal(noOverlap.status,'SOURCE_CONTRACT_CHECK_ONLY');
 assert.equal(noOverlap.unresolved_crosswalk_count,0);
 assert.equal(noOverlap.native_admitted,false);
 assert.equal(noOverlap.qualified_object_id,null);
});
