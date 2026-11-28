import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {makeCapsule} from './tir173_core.mjs';
import {reviewTirComponentArchetype,verifyOriginalGeometrySources} from './tir173_archetype_evidence.mjs';

const read=(path)=>readFileSync(new URL(path,import.meta.url));
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const projectionBytes=read('../../../docs/agent-ingestion/local-agent-homes/Z+2_Neo/pilots/raphael_temporal/geometry_language/T173_NEO_ROLE_PROJECTION.review.json');
const original=JSON.parse(projectionBytes.toString('utf8'));
const dictionary={schema:'cgx.t173.shape_dictionary/0.2',source_sha256:hash(projectionBytes),sentinel:null,
 roles:original.slots.map((r,i)=>({slot:i+1,role:'T173:'+String(i+1).padStart(3,'0'),
   name:'Research role '+(i+1),family:r.class,mesh_ref:String(r.mesh_ref),evidence:r.qualifier}))};
const bytes={
 geometry:read('../../component_atlas/component_geometry_atlas_v0_1.json'),
 ladder:read('../../component_atlas/component_physical_proof_ladder_v0_1.json'),
 packet:read('../../component_atlas/component_instance_build_packet_contract_v0_1.json')
};
const geometry=JSON.parse(bytes.geometry.toString('utf8'));
const ladder=JSON.parse(bytes.ladder.toString('utf8'));
const packet=JSON.parse(bytes.packet.toString('utf8'));
const source_claims={
 geometry_atlas_sha256:hash(bytes.geometry),
 proof_ladder_sha256:hash(bytes.ladder),
 instance_contract_sha256:hash(bytes.packet)
};
const capsule=role=>makeCapsule(dictionary,{shape:role,path:[1,role],
 object_ref:'review:object',source_ref:'review:source',coarse:{level:0,status:'REFERENCE_ONLY'},
 fine:{level:3,status:'UNRESOLVED'},state:{basis:'review:orientation',trit:0,validity:'UNRESOLVED'}});
const checkBoundary=review=>{
 const m=review.machine;
 for(const k of ['archetype_to_shape_mapping_verified','exact_instance_bound','geometry_verified',
   'material_verified','rights_verified','physical_test_performed','physical_evidence_established',
   'source_claims_authenticated','model_inference_performed','execution_performed',
   'mint_performed','native_admitted','signed_dbr','automatic_baseline_promotion'])
   assert.equal(m[k],false,k);
 assert.equal(m.source_bytes_transferred,0);
 assert.equal(m.authority,'REVIEW_ONLY');
 assert.equal(m.proof_stages_total,11);
 assert.equal(m.original_physical_state,'NOT_RUN');
 assert.match(review.human.outstanding,/T173_ROLE_TO_COMPONENT_ARCHETYPE_EQUIVALENCE_UNVERIFIED/);
};
test('reuses exactly the 411 existing Drive-owned geometry archetypes and P0-P10 NOT_RUN proof stages',()=>{
 const result=verifyOriginalGeometrySources(geometry,ladder,packet);
 assert.equal(result.geometry_records,411);
 assert.equal(result.proof_stages,11);
 assert.equal(result.physical_test_stage_count,0);
 assert.equal(result.native_admitted,false);
});
test('no archetype selected does not silently map T173 shape roles to material/physics',()=>{
 const r=reviewTirComponentArchetype(dictionary,capsule(1),geometry,ladder,packet,
   {archetype_id:null,source_claims});
 assert.equal(r.machine.status,'NO_ARCHETYPE_SELECTED');
 assert.equal(r.machine.archetype_id,null);
 assert.equal(r.machine.declared_archetype,null);
 checkBoundary(r);
});
test('explicit CGA-R-001 gives descriptive P2 representative reference, never physical part certification',()=>{
 const r=reviewTirComponentArchetype(dictionary,capsule(137),geometry,ladder,packet,
   {archetype_id:'CGA-R-001',source_claims});
 assert.equal(r.machine.status,'EXPLICIT_ARCHETYPE_CANDIDATE_REVIEW');
 assert.equal(r.machine.shape_role,'T173:137');
 assert.equal(r.machine.archetype_id,'CGA-R-001');
 assert.equal(r.machine.declared_archetype.family,'Resistive');
 assert.equal(r.machine.declared_archetype.baseline_geometry,geometry.records[0]['Baseline Geometry']);
 assert(r.machine.proof_ladder_representative_stages.some(x=>x.stage==='P2'));
 assert(r.machine.proof_ladder_representative_stages.every(x=>x.physical_state==='NOT_RUN'));
 assert.equal(r.machine.source_claims.geometry_atlas_sha256,source_claims.geometry_atlas_sha256);
 checkBoundary(r);
});
test('operator-selected archetype is not a unique role-to-archetype equivalence',()=>{
 const a=reviewTirComponentArchetype(dictionary,capsule(1),geometry,ladder,packet,
   {archetype_id:'CGA-M-029',source_claims});
 const b=reviewTirComponentArchetype(dictionary,capsule(173),geometry,ladder,packet,
   {archetype_id:'CGA-M-029',source_claims});
 assert.equal(a.machine.archetype_id,b.machine.archetype_id);
 assert.notEqual(a.machine.shape_role,b.machine.shape_role);
 assert(a.machine.proof_ladder_representative_stages.some(x=>x.stage==='P10'));
 checkBoundary(a);checkBoundary(b);
});
test('missing rights or fake digest never become verified rights or physical evidence',()=>{
 const spoof={...source_claims,geometry_atlas_sha256:'f'.repeat(64)};
 const r=reviewTirComponentArchetype(dictionary,capsule(93),geometry,ladder,packet,
   {archetype_id:'CGA-R-001',source_claims:spoof});
 assert.equal(r.machine.source_claims_authenticated,false);
 checkBoundary(r);
 for(const claims of [{}, {...source_claims,proof_ladder_sha256:'bad'},
   {...source_claims,source_rights_cleared:'a'.repeat(64)}]){
   assert.throws(()=>reviewTirComponentArchetype(dictionary,capsule(93),geometry,ladder,packet,
     {archetype_id:'CGA-R-001',source_claims:claims}));
 }
});
test('unregistered archetype and tampered source schemas fail closed',()=>{
 for(const id of ['CGA-R-999','T173:001','../../source','CGA-R-001;mint']){
   assert.throws(()=>reviewTirComponentArchetype(dictionary,capsule(1),geometry,ladder,packet,
     {archetype_id:id,source_claims}));
 }
 const duplicate=structuredClone(geometry);
 duplicate.records[1]={...duplicate.records[1],ID:duplicate.records[0].ID};
 assert.throws(()=>verifyOriginalGeometrySources(duplicate,ladder,packet));
 const wrongCount={...geometry,record_count:410};
 assert.throws(()=>verifyOriginalGeometrySources(wrongCount,ladder,packet));
 const fraudulent=structuredClone(ladder);
 fraudulent.stages[0].physical_state='MEASURED';
 assert.throws(()=>verifyOriginalGeometrySources(geometry,fraudulent,packet));
 const wrongPacket={...packet,required_instance_fields:['DBR']};
 assert.throws(()=>verifyOriginalGeometrySources(geometry,ladder,wrongPacket));
});
test('native-admitted capsules and missing shape-role evidence cannot enter the review projection',()=>{
 assert.throws(()=>reviewTirComponentArchetype(dictionary,{...capsule(1),native_admitted:true},
    geometry,ladder,packet,{archetype_id:'CGA-R-001',source_claims}));
 const mismatch={...capsule(1),geometry_ref:'fake'};
 assert.throws(()=>reviewTirComponentArchetype(dictionary,mismatch,
    geometry,ladder,packet,{archetype_id:'CGA-R-001',source_claims}));
});
