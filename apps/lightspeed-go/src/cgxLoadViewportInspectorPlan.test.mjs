import { test } from 'vitest';
import assert from 'node:assert/strict';
import {planUniSpaceLoadViewportInspector as plan} from './cgxLoadViewportInspectorPlan.mjs';
const budgets={reasoning_depth:'standard',device_hydration:'reader',execution_depth:'inspect',max_nodes:16,max_hops:2,max_cross_domains:1,max_cross_edges:4,max_evidence_refs:32,max_compute_ms:2000,max_ops_per_second:50,max_transfer_bytes:1048576};
function fixture({geometry=true,view='document',offline=false,novel=false}={}){
 const focus={object_id:'fixture:romer:watchtower',domain:'romer',source_ceiling:'synthetic-fixture',source_refs:['fixture:s1'],geometry:geometry?{source_ref:'fixture:geo',frame:'EPSG:7856',units:'m'}:null};
 return {
  context_plan:{schema:'UNISPACE-CGX-HOST-CONTEXT-GATE/0.1',state:'PLAN_ONLY_NOT_HYDRATED',object_id:focus.object_id,filespace:'Romer.cgx',native_admitted:false,host_context_readback_authenticated:false,private_hydration_authorized:false,public_publish_authorized:false,canonical_mutation:false,execution_performed:false},
  lens_plan:{schema:'UNISPACE-CGX-LOAD-LENS-PLAN/0.1',state:'PLAN_ONLY_NOT_HYDRATED',alias:'LOAD.cgx',parent_filespace:'Cognigrex.cgx',object_id:focus.object_id,filespace:'Romer.cgx',hydrated:false,native_admitted:false,canonical_mutation:false,execution_performed:false,public_publish_authorized:false,host_context_readback_authenticated:false,evidence_class:'scientific',planned_hydration:offline?'H0':'H2'},
  spread_plan:{schema:'LOAD-SEMANTIC-SPREAD-PLAN/0.1',status:'REVIEW_ONLY',focus_id:focus.object_id,objects:[focus],edges:[],budgets:{...budgets},network_fetch:false,rendered:false,canonical_mutation:false,hydration_complete:false},
  viewport_plan:{schema:'LOAD-VIEWPORT-SWITCH-PLAN/0.1',state:view==='3d'&&!geometry?'FRONTIER_GEOMETRY_UNQUALIFIED':'VIEW_PLAN_READY',identity:focus.object_id,to:view,selected_object_ids:[focus.object_id],source_refs:['fixture:s1'],geometry_ref:geometry?'fixture:geo':null,evidence_ceiling:'synthetic-fixture',network_fetch:false,rendered:false,interactive_execution:false,semantic_mutation:false,public_release:false},
  client_permissions:{mode:'review_only',revoked:false,allowed_object_ids:[focus.object_id],allowed_filespaces:['Romer.cgx'],allowed_source_ids:['fixture:s1','fixture:geo'],allowed_domains:['romer']},
  novel_plan:novel?{schema:'LOAD-NOVEL-TO-KNOWN-PLAN/0.1',domain:'romer',status:'SEMANTIC_MATCH_REVIEW',native_admission:false,created_object_ids:0,verified_object_id:null,required:['source identity']}:null,
  offline
 };
}
const clone=x=>structuredClone(x);
const state=x=>plan(x).state;
test('source-review inspector returns one exact object and child FileSpace',()=>{
 const a=plan(fixture());assert.equal(a.state,'SOURCE_REVIEW_ONLY');assert.equal(a.object_id,'fixture:romer:watchtower');assert.equal(a.filespace,'Romer.cgx');assert.equal(a.alias,'LOAD.cgx');assert.equal(a.parent_filespace,'Cognigrex.cgx');
});
test('all six views remain review-only, not rendered or released',()=>{
 for(const view of ['document','3d','chat','graph','interactive','matrix']){
  const a=plan(fixture({view}));assert.equal(a.state,'SOURCE_REVIEW_ONLY');assert.equal(a.view,view);assert.equal(a.rendered,false);assert.equal(a.public_release,false);assert.equal(a.execution_performed,false);
 }
});
test('offline fallback returns H0 without halo, source refs, novel matches or controls',()=>{
 const a=plan(fixture({offline:true,novel:true}));assert.equal(a.hydration,'H0_OFFLINE_METADATA_ONLY');assert.equal(a.halo,null);assert.equal(a.novel_match,null);assert.equal(a.current_controls,null);assert.ok(a.frontier.includes('OFFLINE_H0_ONLY'));
});
test('offline with H2 is denied',()=>{const x=fixture({offline:true});x.lens_plan.planned_hydration='H2';assert.equal(state(x),'HOLD')});
test('geometry absent explicitly yields Frontier instead of invented 3D',()=>{
 const a=plan(fixture({view:'3d',geometry:false}));assert.equal(a.state,'SOURCE_REVIEW_ONLY');assert.ok(a.frontier.includes('GEOMETRY_FRAME_UNITS_OR_SOURCE_MISSING'));assert.equal(a.geometry_rendered,false);
});
test('false 3D readiness is held',()=>{const x=fixture({view:'3d',geometry:false});x.viewport_plan.state='VIEW_PLAN_READY';assert.equal(plan(x).hold_code,'FALSE_GEOMETRY_READINESS')});
test('geometry source not in client allowed sources is held',()=>{const x=fixture({view:'3d'});x.client_permissions.allowed_source_ids=['fixture:s1'];assert.equal(plan(x).hold_code,'FALSE_GEOMETRY_READINESS')});
test('requested slider changes trigger replan, never pretend hydration',()=>{
 const x=fixture();x.requested_controls={max_nodes:24,max_compute_ms:4500,reasoning_depth:'deep'};
 const a=plan(x);assert.equal(a.state,'REPLAN_REQUIRED');assert.equal(a.current_controls.max_nodes,16);assert.equal(a.proposed_controls.max_nodes,24);assert.equal(a.network_fetch,false);
});
test('oversized compute or node control denied',()=>{const x=fixture();x.requested_controls={max_compute_ms:120001};assert.equal(plan(x).hold_code,'CONTROL_LIMIT_EXCEEDED')});
test('unknown control key denied',()=>{const x=fixture();x.requested_controls={execute:true};assert.equal(plan(x).hold_code,'UNSUPPORTED_CONTROL')});
test('revoked permission denies',()=>{const x=fixture();x.client_permissions.revoked=true;assert.equal(plan(x).hold_code,'CLIENT_SCOPE_DENIED')});
test('mismatched exact Object_ID denies',()=>{const x=fixture();x.lens_plan.object_id='fixture:other';assert.equal(plan(x).hold_code,'LOAD_LENS_BOUNDARY_MISMATCH')});
test('mismatched FileSpace denies',()=>{const x=fixture();x.context_plan.filespace='Eco.cgx';assert.equal(plan(x).hold_code,'LOAD_LENS_BOUNDARY_MISMATCH')});
test('family-only identity is not a valid exact instance',()=>{const x=fixture();x.context_plan.object_id='cgx:domain:romer';assert.equal(plan(x).hold_code,'EXACT_CONTEXT_REQUIRED')});
test('unpermitted halo object ID is rejected, not leaked',()=>{
 const x=fixture();x.spread_plan.objects.push({object_id:'fixture:eco:secret',domain:'eco',source_ceiling:'private',source_refs:['fixture:private']});
 assert.equal(plan(x).hold_code,'UNAUTHORIZED_HALO_OR_SOURCE');assert.ok(!JSON.stringify(plan(x)).includes('fixture:eco:secret'));
});
test('unpermitted source reference is rejected, not leaked',()=>{const x=fixture();x.spread_plan.objects[0].source_refs=['fixture:private'];assert.equal(plan(x).hold_code,'UNAUTHORIZED_HALO_OR_SOURCE')});
test('cross-domain not allowed without explicit scope',()=>{const x=fixture();x.spread_plan.objects.push({object_id:'fixture:eco:tree',domain:'eco',source_ceiling:'fixture',source_refs:[]});x.viewport_plan.selected_object_ids.push('fixture:eco:tree');x.client_permissions.allowed_object_ids.push('fixture:eco:tree');assert.equal(plan(x).hold_code,'UNAUTHORIZED_HALO_OR_SOURCE')});
test('duplicate semantic Object_ID rejected',()=>{const x=fixture();x.spread_plan.objects.push(clone(x.spread_plan.objects[0]));assert.equal(plan(x).hold_code,'UNAUTHORIZED_HALO_OR_SOURCE')});
test('view identity substitution denied',()=>{const x=fixture();x.viewport_plan.identity='fixture:eco:tree';assert.equal(plan(x).hold_code,'VIEW_CEILING_OR_ID_MISMATCH')});
test('evidence ceiling escalation denied',()=>{const x=fixture();x.viewport_plan.evidence_ceiling='peer-reviewed';assert.equal(plan(x).hold_code,'VIEW_CEILING_OR_ID_MISMATCH')});
test('inline private LOAD locator rejected',()=>{const x=fixture();x.spread_plan.objects[0].source_locator='C:/owner/private/LOAD';assert.equal(plan(x).hold_code,'INVALID_OR_PRIVATE_INPUT')});
test('nested token rejected without echo',()=>{const x=fixture();x.client_permissions.token='MYTOPSECRET123';assert.equal(plan(x).hold_code,'INVALID_OR_PRIVATE_INPUT');assert.ok(!JSON.stringify(plan(x)).includes('MYTOPSECRET123'))});
test('novel match remains candidate with explicit gaps, not minted',()=>{
 const a=plan(fixture({novel:true}));assert.equal(a.novel_match.status,'SEMANTIC_MATCH_REVIEW');assert.ok(a.novel_match.gap_categories.includes('native_dbr'));assert.equal(a.native_admitted,false);
});
test('novel match claiming native admission denied',()=>{const x=fixture({novel:true});x.novel_plan.native_admission=true;assert.equal(plan(x).hold_code,'UNTRUSTED_NOVEL_MATCH')});
test('fake authenticated host or rendered plan denied',()=>{const x=fixture();x.context_plan.host_context_readback_authenticated=true;assert.equal(plan(x).hold_code,'EXACT_CONTEXT_REQUIRED')});
test('no network, DBR, public publish or host readback claimed',()=>{const a=plan(fixture());assert.equal(a.host_authenticated,false);assert.equal(a.native_admitted,false);assert.equal(a.canonical_mutation,false);assert.equal(a.public_release,false);assert.equal(a.network_fetch,false)});
