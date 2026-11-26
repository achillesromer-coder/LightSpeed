import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {makeCapsule} from './tir173_core.mjs';
import {projectGuiosContext,ENVIRONMENTS,SPATIAL_RELATIONS,PERSPECTIVES} from './tir173_context.mjs';
const source=readFileSync(new URL('../../../docs/agent-ingestion/local-agent-homes/Z+2_Neo/pilots/raphael_temporal/geometry_language/T173_NEO_ROLE_PROJECTION.review.json',import.meta.url));
const projection=JSON.parse(source.toString('utf8'));
const dictionary={schema:'cgx.t173.shape_dictionary/0.2',source_sha256:createHash('sha256').update(source).digest('hex'),sentinel:null,
 roles:projection.slots.map((r,i)=>({slot:i+1,role:'T173:'+String(i+1).padStart(3,'0'),name:'Research role '+(i+1),family:r.class,mesh_ref:String(r.mesh_ref),evidence:r.qualifier}))};
const cap=makeCapsule(dictionary,{shape:137,path:[1,137],object_ref:'review:object',source_ref:'review:source',
 coarse:{level:0,status:'REFERENCE_ONLY'},fine:{level:3,status:'UNRESOLVED'},
 state:{basis:'review:axis',trit:0,validity:'UNRESOLVED'}});
test('same capsule across all perspective/space combinations retains dictionary and shape identity',()=>{
 for(const environment of ENVIRONMENTS)for(const perspective of PERSPECTIVES)for(const spatial of SPATIAL_RELATIONS){
  const r=projectGuiosContext(dictionary,cap,{environment,perspective,spatial,scale_ratio:10});
  assert.equal(r.context.shape_role,cap.shape_role);assert.equal(r.context.geometry_ref,cap.geometry_ref);
  assert.equal(r.machine.context,r.context);assert.equal(r.context.execution_performed,false);
  assert.equal(r.context.interaction.relation_established,false);
 }
});
test('scale ratio changes lens only, not underlying geometry or object state',()=>{
 const a=projectGuiosContext(dictionary,cap,{scale_ratio:.001});
 const b=projectGuiosContext(dictionary,cap,{scale_ratio:1000});
 assert.equal(a.context.scale.observed_magnitude,.001);
 assert.equal(b.context.scale.observed_magnitude,1000);
 assert.equal(a.context.object_ref,b.context.object_ref);
 assert.equal(a.context.dictionary_source_sha256,b.context.dictionary_source_sha256);
 assert.equal(cap.magnitude,1);
});
test('unresolved environment and void stay explicit, never silently inferred as solid truth',()=>{
 const r=projectGuiosContext(dictionary,cap,{perspective:'void',environment:'physical'});
 assert.equal(r.context.negative_space.empty_space_is_context,true);
 assert.equal(r.context.negative_space.unresolved_fine,true);
 assert.equal(r.context.environment.evidence,'UNRESOLVED');
 assert.equal(r.context.hydration.status,'PLAN_ONLY_NOT_HYDRATED');
});
test('invalid and unproved contexts fail closed',()=>{
 for(const options of [{environment:'astral'},{perspective:'oracle'},{spatial:'teleport'},{scale_ratio:0},{scale_ratio:Infinity},{evidence:'SUPPORTED'},{source_ref:'../../secret'}])
  assert.throws(()=>projectGuiosContext(dictionary,cap,options));
});
