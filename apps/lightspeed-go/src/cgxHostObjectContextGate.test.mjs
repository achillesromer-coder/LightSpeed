import { test } from 'node:test';
import assert from 'node:assert/strict';
import { projectCgxHostObjectContextGate as project } from './cgxHostObjectContextGate.mjs';
// SHA values below are real provider Git blob metadata from this review branch.
// The context response and owner/session fields are SYNTHETIC test fixtures.
const make = () => ({
  requested_object_id: 'WT-001', requested_layer: 'R0',
  expected_child: {semantic_object_id:'cgx:domain:romer',filespace:'Romer.cgx',domain:'romer'},
  registry_git_blob_sha:'c2e03b1137ba844209e6c80e94c9fc7532f0db11',
  lineage_git_blob_sha:'75d913822e4da42e64ab8a2274c84d6f853340b3',
  lineage_candidates:[{semantic_object_id:'WT-001',twin_id:'watchtower'}],
  context_response: {execution_performed:false,external_action_performed:false,canonical_mutation:false,authority_transfer:false,
    object_context:{schema:'CGX-OBJECT-CONTEXT/0.1',automatic_execution:false,canonical_mutation:false,
      resolved_twin_id:'watchtower',semantic_domain:'romer',
      domain_identity:{semantic_object_id:'cgx:domain:romer',filespace:'Romer.cgx'},
      semantic_resolution:{state:'exact_semantic_object',semantic_object_id:'WT-001'},
      source_name:'PRIVATE_SOURCE.xlsx',representation:{file:'/private/secret.obj'},session_token:'secret'}},
});
const expectHold = (p,code) => assert.equal(project(p).hold_code,code);
test('one exact WatchTower identity produces bounded R0 plan only',()=>{
 const v=project(make());assert.equal(v.state,'PLAN_ONLY_NOT_HYDRATED');assert.equal(v.object_id,'WT-001');assert.equal(v.filespace,'Romer.cgx');
 assert.equal(v.source_registry_independently_verified,false);assert.equal(v.host_context_readback_authenticated,false);
 assert.equal(v.native_admitted,false);assert.equal(v.private_hydration_authorized,false);
 assert.equal(JSON.stringify(v).includes('secret'),false);assert.equal(JSON.stringify(v).includes('/private/'),false);
});
test('domain identity is not a concrete semantic object',()=>{const p=make();p.requested_object_id='cgx:domain:eco';expectHold(p,'DOMAIN_ID_IS_NOT_INSTANCE_ID');});
test('Eco family-only lineage cannot be promoted by a context alias',()=>{const p=make();p.requested_object_id='ECO-UNQUALIFIED';p.expected_child={semantic_object_id:'cgx:domain:eco',filespace:'Eco.cgx',domain:'eco'};p.lineage_candidates=[{semantic_object_id:'ECO-UNQUALIFIED',twin_id:'second_cycle'}];p.context_response.object_context.semantic_domain='eco';p.context_response.object_context.domain_identity={semantic_object_id:'cgx:domain:eco',filespace:'Eco.cgx'};p.context_response.object_context.resolved_twin_id='second_cycle';p.context_response.object_context.semantic_resolution={state:'family_bound_only',semantic_object_id:null};expectHold(p,'FAMILY_ONLY_OR_OBJECT_ID_MISMATCH');});
test('INF-001 collides across InterSol and Spaceport lineage',()=>{const p=make();p.requested_object_id='INF-001';p.lineage_candidates=[{semantic_object_id:'INF-001',twin_id:'intersol'},{semantic_object_id:'INF-001',twin_id:'romer_spaceport'}];expectHold(p,'MISSING_OR_COLLIDING_SEMANTIC_ID');});
test('missing or mismatched lineage fails closed',()=>{const p=make();p.lineage_candidates=[];expectHold(p,'MISSING_OR_COLLIDING_SEMANTIC_ID');const q=make();q.lineage_candidates[0].semantic_object_id='SPACE-01';expectHold(q,'MISSING_OR_COLLIDING_SEMANTIC_ID');});
test('host response cannot report execution or authority transfer',()=>{for(const k of ['execution_performed','external_action_performed','canonical_mutation','authority_transfer']){const p=make();p.context_response[k]=true;expectHold(p,'HOST_RESPONSE_BOUNDARY_UNVERIFIED');}});
test('host context schema and read-only flags mandatory',()=>{const p=make();p.context_response.object_context.schema='wrong';expectHold(p,'HOST_CONTEXT_SCHEMA_OR_BOUNDARY');const q=make();q.context_response.object_context.automatic_execution=true;expectHold(q,'HOST_CONTEXT_SCHEMA_OR_BOUNDARY');});
test('host object and twin must match exactly',()=>{const p=make();p.context_response.object_context.semantic_resolution.semantic_object_id='SPACE-01';expectHold(p,'FAMILY_ONLY_OR_OBJECT_ID_MISMATCH');const q=make();q.context_response.object_context.resolved_twin_id='intersol';expectHold(q,'FAMILY_ONLY_OR_OBJECT_ID_MISMATCH');});
test('domain and FileSpace mismatch rejected',()=>{const p=make();p.context_response.object_context.domain_identity.filespace='Eco.cgx';expectHold(p,'CHILD_FILESPACE_MISMATCH');const q=make();q.context_response.object_context.semantic_domain='eco';expectHold(q,'CHILD_FILESPACE_MISMATCH');});
test('invalid source registry metadata rejected',()=>{const p=make();p.lineage_git_blob_sha='not-a-hash';expectHold(p,'SOURCE_REGISTRY_BINDING_UNVERIFIED');const q=make();q.expected_child.filespace='../Romer.cgx';expectHold(q,'SOURCE_REGISTRY_BINDING_UNVERIFIED');});
test('R1 R2 R3 and F are not authorised by this adapter',()=>{for(const layer of ['R1','R2','R3','F']){const p=make();p.requested_layer=layer;expectHold(p,'PRIVATE_LAYER_REQUIRES_AUTH_AND_DBR');}});
test('invalid input and control characters fail closed',()=>{expectHold(null,'INVALID_INPUT');const p=make();p.requested_object_id='WT-001\n';expectHold(p,'INVALID_OBJECT_ID');});
