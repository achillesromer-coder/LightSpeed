import {test} from 'node:test';
import assert from 'node:assert/strict';
import {radialTrianglePreview,projectUniSpaceFacet as project} from './cgxFacetProjection.mjs';
const object=()=>({schema:'UNISPACE-CGX-ONE-OBJECT-VIEW-PLAN/0.1',
 state:'PLAN_ONLY_NOT_HYDRATED',object_id:'WT-001',filespace:'Romer.cgx',
 native_admitted:false,canonical_mutation:false,execution_performed:false,
 public_publish_authorized:false,source_bytes_included:false});
const load=()=>({schema:'UNISPACE-CGX-LOAD-LENS-PLAN/0.1',
 state:'PLAN_ONLY_NOT_HYDRATED',alias:'LOAD.cgx',object_id:'WT-001',filespace:'Romer.cgx',
 native_admitted:false,hydrated:false,canonical_mutation:false,
 execution_performed:false,public_publish_authorized:false});
const make=()=>({object_view:object(),load_lens:load(),task_intent:'browse',device_profile:'desktop'});
test('source-review plan binds UniSpace to exact CGX identity',()=>{
 const x=project(make()); assert.equal(x.state,'REVIEW_FACET_PLAN_ONLY');
 assert.equal(x.product,'UniSpace.cgx'); assert.equal(x.shorthand.ref,'WT-001');
 assert.equal(x.shorthand.runtime,'existing-LightSpeed');
 for(const k of ['hydrated','dispatched','native_admitted','execution_performed','canonical_mutation','public_publish_authorized'])
 assert.equal(x[k],false,k);
});
test('no extra overlapping primary windows',()=>{
 const x=project(make());assert.equal(x.view.one_primary,true);
 assert.equal(x.view.primary,'filespace-tree');
 assert.deepEqual(x.view.secondary_on_demand,['topology-graph']);
 assert.equal(x.view.keyboard_presets['3'],'spatial-preview');
});
test('catalog preference never proves availability',()=>{
 const p=make();p.declared_renderer_ids=['topology-graph'];
 const x=project(p);assert.equal(x.view.primary,'topology-graph');
 assert.equal(x.view.available_renderer_independently_verified,false);
});
test('ecology has no geographic map from a caller label alone',()=>{
 const p=make();p.task_intent='ecology';p.declared_renderer_ids=['map-spatial'];p.independently_verified_geo_receipt=true;
 assert.equal(project(p).view.primary,'active-object-inspector');
 assert.equal(project(p).view.geo_mapping_admitted,false);
});
test('engineering has no 3d twin without receipt',()=>{
 const p=make();p.task_intent='engineer';p.declared_renderer_ids=['twin-3d'];p.independently_verified_geometry_receipt=true;
 assert.equal(project(p).view.primary,'active-object-inspector');
});
test('cross-object LOAD is denied',()=>{
 const p=make();p.load_lens.object_id='OTHER';
 assert.equal(project(p).hold_code,'LOAD_ALIAS_OR_OBJECT_SCOPE_MISMATCH');
});
test('fake native admission in gate is denied',()=>{
 const p=make();p.object_view.native_admitted=true;
 assert.equal(project(p).hold_code,'OBJECT_VIEW_GATE_NOT_SATISFIED');
});
test('publish remains held',()=>{
 const p=make();p.task_intent='publish';
 assert.equal(project(p).hold_code,'PUBLICATION_REQUIRES_SEPARATE_ACCEPTANCE');
});
test('inline secrets are not passed through',()=>{
 for(const key of ['token','source_bytes','private_path']){
 const p=make();p[key]='not-for-cgx';
 assert.equal(project(p).hold_code,'INVALID_OR_INLINE_PRIVATE_REQUEST');
 assert.equal(JSON.stringify(project(p)).includes('not-for-cgx'),false);
 }
});
test('bad device or task is denied',()=>{
 const p=make();p.device_profile='unbounded';
 assert.equal(project(p).hold_code,'UNSUPPORTED_DEVICE');
 const q=make();q.task_intent='run-everything';
 assert.equal(project(q).hold_code,'UNKNOWN_TASK_INTENT');
});
test('triangle geometry exact edge and r=L/2',()=>{
 const g=radialTrianglePreview(6);
 assert.equal(g.vertex_circle_radius,3);
 assert.equal(g.vertices.length,3);
 for(let i=0;i<3;i++){
  const a=g.vertices[i], b=g.vertices[(i+1)%3];
  assert.ok(Math.abs(Math.hypot(a[0]-b[0],a[1]-b[1])-6)<1e-12);
 }
 assert.equal(g.canonical_geometry,false);
});
test('invalid geometry cannot be introduced',()=>{
 for(const v of [-1,0,NaN,Infinity,1e9])assert.equal(radialTrianglePreview(v),null);
 const p=make();p.preview_edge_length=Infinity;
 assert.equal(project(p).geometric_preview,null);
});
test('all task modes return review-only with one primary',()=>{
 for(const task_intent of ['browse','operate','engineer','ecology','validate','runtime','audit','mobile_quicklook']){
 const p=make();p.task_intent=task_intent;
 const x=project(p);
 assert.equal(x.state,'REVIEW_FACET_PLAN_ONLY',task_intent);
 assert.equal(x.view.one_primary,true);
 assert.equal(x.dispatch.state,'NOT_QUEUED');
 }
});
