import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
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
