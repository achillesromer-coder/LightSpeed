import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {planKnownAlignment,planQualifiedOperator} from './loadQualifiedKnowledge.mjs';
const registry=JSON.parse(readFileSync(new URL('./online_registry_projection_2026-10-28.json',import.meta.url),'utf8'));
// Synthetic values, not measured orbital state or validated scientific results.
const novel={semantic_type:'orbital_state',dimensions:{position:'L',velocity:'L/T'},units:{position:'km',velocity:'km/s'},
 frame:'ICRF',epoch:'synthetic-2026',configuration:'fixture-A',source_refs:['fixture:novel']};
const known=[
 {object_id:'fixture:one',...novel,source_refs:['fixture:known']},
 {object_id:'fixture:two',...novel,frame:'ECEF',source_refs:['fixture:known2']},
 {object_id:'fixture:three',...novel,units:{position:'m',velocity:'m/s'},source_refs:['fixture:known3']},
 {object_id:'fixture:private',...novel,source_refs:['fixture:private']}
];
const acl={authorised_object_ids:['fixture:one','fixture:two','fixture:three'],
 authorised_source_ids:['fixture:novel','fixture:known','fixture:known2','fixture:known3']};
const run=(more={})=>planKnownAlignment({novel,known_objects:known,...acl,...more});
test('typed known matches are only candidates, not minted',()=>{
 const x=run();assert.equal(x.matched_candidates.length,3);assert.equal(x.objects_minted,0);
 assert.equal(x.matched_candidates[0].auto_merge,false);
});
test('private known Object_ID is omitted entirely',()=>assert.ok(!JSON.stringify(run()).includes('fixture:private')));
test('same IDs do not independently prove semantic equivalence',()=>{
 const x=run({novel:{...novel,object_id:'fixture:one'}});
 assert.equal(x.matched_candidates[0].state,'SAME_ID_CLAIM_REQUIRES_PROOF');
});
test('coordinate frame mismatch preserved',()=>assert.ok(run().matched_candidates.some(x=>x.checks.includes('FRAME_TRANSFORM_OR_DEFINITION_REQUIRED'))));
test('units mismatch requires explicit unit conversion',()=>assert.ok(run().matched_candidates.some(x=>x.checks.includes('UNIT_CONVERSION_REQUIRED'))));
test('unknown units are held for dimensioned quantities',()=>{
 const x=run({novel:{...novel,units:undefined}});
 assert.ok(x.matched_candidates.every(row=>row.checks.includes('UNITS_UNDECLARED')));
});
test('missing allowed sources becomes evidence gap',()=>{
 const x=run({authorised_source_ids:[]});
 assert.ok(x.matched_candidates.every(row=>row.checks.includes('EVIDENCE_GAP')));
});
test('dimension mismatches are not considered equivalent',()=>{
 const x=run({novel:{...novel,dimensions:{position:'T',velocity:'L/T'}}});
 assert.ok(x.matched_candidates.every(row=>row.checks.includes('INCOMPATIBLE_DIMENSIONS')));
});
test('duplicate stable known Object_ID is rejected',()=>assert.throws(()=>run({known_objects:[...known,known[0]]}),/DUPLICATE_KNOWN_OBJECT_ID/));
test('missing ACL is rejected',()=>assert.throws(()=>planKnownAlignment({novel,known_objects:known}),/INVALID_ALIGNMENT_SCOPE/));
test('matched CCC route only proposes solver: no execution, result or native write',()=>{
 const p=planQualifiedOperator({registry,problem:novel,authorised_source_ids:['fixture:novel'],
 bindings:[{route_key:'science.query',input_type:'orbital_state',required_dimensions:novel.dimensions,
 required_units:novel.units,qualified_method_source:'fixture:math-method'}]});
 assert.equal(p.operator_candidates.length,1);assert.equal(p.computation_executed,false);
 assert.equal(p.numeric_result,null);assert.equal(p.object_ids_minted,0);
 assert.ok(p.operator_candidates[0].blockers.includes('HOST_CAPABILITY_LEASE_AND_DB_R_READBACK_REQUIRED'));
});
test('unregistered route and dimensionally incompatible route are excluded',()=>{
 const p=planQualifiedOperator({registry,problem:novel,authorised_source_ids:['fixture:novel'],
 bindings:[{route_key:'not-installed',input_type:'orbital_state',required_dimensions:novel.dimensions},
 {route_key:'science.query',input_type:'orbital_state',required_dimensions:{position:'T'}}]});
 assert.equal(p.operator_candidates.length,0);
});
test('typed operator mismatched unit basis gets conversion gate',()=>{
 const p=planQualifiedOperator({registry,problem:novel,authorised_source_ids:['fixture:novel'],
 bindings:[{route_key:'science.query',input_type:'orbital_state',required_dimensions:novel.dimensions,
 required_units:{position:'m',velocity:'m/s'},qualified_method_source:'fixture:math-method'}]});
 assert.ok(p.operator_candidates[0].blockers.includes('UNIT_CONVERSION_METHOD_REQUIRED'));
});

test('operator rejects forged source-registry route provenance',()=>{
 const forged=JSON.parse(JSON.stringify(registry));
 const route=forged.records.find(x=>x.category==='ccc_route');
 forged.records.push({...route,source_key:'fixture.injected',source_git_blob:'0'.repeat(40)});
 assert.throws(()=>planQualifiedOperator({registry:forged,problem:novel,
  authorised_source_ids:['fixture:novel'],
  bindings:[{route_key:'fixture.injected',input_type:'orbital_state',
   required_dimensions:novel.dimensions,qualified_method_source:'fixture:math-method'}]}),
  /SOURCE_PROOF_MISMATCH/);
});
test('operator rejects forged native-admission count in source-only catalogue',()=>{
 const forged=JSON.parse(JSON.stringify(registry));forged.summary.native_accepted=1;
 assert.throws(()=>planQualifiedOperator({registry:forged,problem:novel,
  authorised_source_ids:['fixture:novel'],bindings:[]}),/UNSUPPORTED_AUTHORITY_CLAIM/);
});

test('dimensioned operator without declared method units is held, not silently treated as compatible',()=>{
 const p=planQualifiedOperator({registry,problem:novel,authorised_source_ids:['fixture:novel'],
  bindings:[{route_key:'science.query',input_type:'orbital_state',required_dimensions:novel.dimensions,
   qualified_method_source:'fixture:math-method'}]});
 assert.ok(p.operator_candidates[0].blockers.includes('METHOD_UNITS_UNDECLARED'));
 assert.equal(p.computation_executed,false);
});
test('partial method unit basis is held independently of a conversion claim',()=>{
 const p=planQualifiedOperator({registry,problem:novel,authorised_source_ids:['fixture:novel'],
  bindings:[{route_key:'science.query',input_type:'orbital_state',required_dimensions:novel.dimensions,
   required_units:{position:'km'},qualified_method_source:'fixture:math-method'}]});
 assert.ok(p.operator_candidates[0].blockers.includes('METHOD_UNITS_UNDECLARED'));
 assert.ok(!p.operator_candidates[0].blockers.includes('UNIT_CONVERSION_METHOD_REQUIRED'));
 assert.equal(p.object_ids_minted,0);
});

test('method provenance is denied when method source is not in the explicit source ACL',()=>{
 const p=planQualifiedOperator({registry,problem:novel,authorised_source_ids:['fixture:novel'],
  bindings:[{route_key:'science.query',input_type:'orbital_state',required_dimensions:novel.dimensions,
   required_units:novel.units,qualified_method_source:'fixture:private-method'}]});
 assert.equal(p.operator_candidates.length,1);
 assert.ok(p.operator_candidates[0].blockers.includes('METHOD_SOURCE_NOT_AUTHORISED'));
 assert.equal(p.computation_executed,false);
});
test('method provenance ACL gate clears only for explicitly authorised method source',()=>{
 const p=planQualifiedOperator({registry,problem:novel,
  authorised_source_ids:['fixture:novel','fixture:qualified-method'],
  bindings:[{route_key:'science.query',input_type:'orbital_state',required_dimensions:novel.dimensions,
   required_units:novel.units,qualified_method_source:'fixture:qualified-method'}]});
 assert.equal(p.operator_candidates.length,1);
 assert.ok(!p.operator_candidates[0].blockers.includes('METHOD_SOURCE_NOT_AUTHORISED'));
 assert.ok(p.operator_candidates[0].blockers.includes('HOST_CAPABILITY_LEASE_AND_DB_R_READBACK_REQUIRED'));
 assert.equal(p.computation_executed,false);
});

test('typed operator without a declared selector scope remains held',()=>{
 const p=planQualifiedOperator({registry,problem:novel,authorised_source_ids:['fixture:novel','fixture:method'],
  bindings:[{route_key:'science.query',input_type:'orbital_state',required_dimensions:novel.dimensions,
   required_units:novel.units,qualified_method_source:'fixture:method'}]});
 assert.ok(p.operator_candidates[0].blockers.includes('SELECTOR_SCOPE_UNDECLARED'));
 assert.equal(p.computation_executed,false);
});
test('registered route not declared for requested family selector remains held',()=>{
 const p=planQualifiedOperator({registry,problem:novel,selector:'cognigrex',
  authorised_source_ids:['fixture:novel','fixture:method'],
  bindings:[{route_key:'cad.freecad',input_type:'orbital_state',required_dimensions:novel.dimensions,
   required_units:novel.units,qualified_method_source:'fixture:method'}]});
 assert.ok(p.operator_candidates[0].blockers.includes('SELECTOR_ROUTE_NOT_DECLARED'));
 assert.equal(p.object_ids_minted,0);
});
test('declared family selector removes only catalogue mismatch, not host acceptance',()=>{
 const p=planQualifiedOperator({registry,problem:novel,selector:'romer-grex',
  authorised_source_ids:['fixture:novel','fixture:method'],
  bindings:[{route_key:'cad.freecad',input_type:'orbital_state',required_dimensions:novel.dimensions,
   required_units:novel.units,qualified_method_source:'fixture:method'}]});
 assert.ok(!p.operator_candidates[0].blockers.includes('SELECTOR_ROUTE_NOT_DECLARED'));
 assert.ok(p.operator_candidates[0].blockers.includes('HOST_CAPABILITY_LEASE_AND_DB_R_READBACK_REQUIRED'));
 assert.equal(p.computation_executed,false);
});
