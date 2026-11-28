import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {makeCapsule} from './tir173_core.mjs';
import {verifyOriginalInstancePopulation,reviewTirExistingInstance} from './tir173_archetype_evidence.mjs';

const bytes=(path)=>readFileSync(new URL(path,import.meta.url));
const sha=b=>createHash('sha256').update(b).digest('hex');
const projection=bytes('../../../docs/agent-ingestion/local-agent-homes/Z+2_Neo/pilots/raphael_temporal/geometry_language/T173_NEO_ROLE_PROJECTION.review.json');
const d={schema:'cgx.t173.shape_dictionary/0.2',source_sha256:sha(projection),sentinel:null,
 roles:JSON.parse(projection.toString('utf8')).slots.map((x,i)=>({
  slot:i+1,role:'T173:'+String(i+1).padStart(3,'0'),
  name:'Research role '+i,family:x.class,mesh_ref:String(x.mesh_ref),evidence:x.qualifier
 }))};
const raw={
 atlas:bytes('../../component_atlas/component_geometry_atlas_v0_1.json'),
 ladder:bytes('../../component_atlas/component_physical_proof_ladder_v0_1.json'),
 packet:bytes('../../component_atlas/component_instance_build_packet_contract_v0_1.json'),
 population:bytes('../../component_atlas/component_instance_population_v0_1.json')
};
const atlas=JSON.parse(raw.atlas.toString('utf8'));
const ladder=JSON.parse(raw.ladder.toString('utf8'));
const packet=JSON.parse(raw.packet.toString('utf8'));
const population=JSON.parse(raw.population.toString('utf8'));
const source_claims={
 geometry_atlas_sha256:sha(raw.atlas),
 proof_ladder_sha256:sha(raw.ladder),
 instance_contract_sha256:sha(raw.packet),
 instance_register_sha256:sha(raw.population)
};
const capsule=i=>makeCapsule(d,{shape:i,path:[1,i],
 object_ref:'review:obj',source_ref:'review:source',
 coarse:{level:0,status:'REFERENCE_ONLY'},fine:{level:3,status:'UNRESOLVED'},
 state:{basis:'review:axis',trit:0,validity:'UNRESOLVED'}
});
const inspect=(shape,arch=null,instance=null,claims=source_claims)=>{
 return reviewTirExistingInstance(d,capsule(shape),atlas,ladder,packet,population,
   {archetype_id:arch,instance_id:instance,source_claims:claims});
};
const reviewOnly=r=>{
 assert.equal(r.machine.authority,'REVIEW_ONLY');
 for(const k of ['source_claims_authenticated','archetype_to_shape_mapping_verified',
   'exact_instance_bound','geometry_verified','material_verified','rights_verified',
   'source_verified_against_drive','physical_test_performed','measurement_verified',
   'execution_performed','native_admitted','signed_dbr','mint_performed',
   'model_inference_performed','model_weights_changed'])assert.equal(r.machine[k],false,k);
 assert.equal(r.machine.source_bytes_transferred,0);
 assert.equal(r.machine.original_register_instance_count,8);
 assert.equal(r.machine.original_unbound_count,8);
};
test('original Drive-owned population: 8 unbound P0-P3 envelopes, no measured stage',()=>{
 const report=verifyOriginalInstancePopulation(population,packet,ladder);
 assert.equal(report.instance_count,8);
 assert.equal(report.cga_related_instances,7);
 assert.equal(report.non_cga_p0_instances,1);
 assert.equal(report.physical_tests_completed,0);
 assert.equal(report.native_admitted,false);
});
test('default has no archetype or instance; exact CGA-R-001 yields eligible but unselected instance',()=>{
 const none=inspect(173);
 assert.equal(none.machine.status,'NO_INSTANCE_SELECTED');
 assert.deepEqual(none.machine.eligible_existing_instance_ids,[]);
 reviewOnly(none);
 const r=inspect(173,'CGA-R-001');
 assert.equal(r.machine.instance_id,null);
 assert.deepEqual(r.machine.eligible_existing_instance_ids,['CGXI-P2-R-001']);
 assert.equal(r.machine.selected_record,null);
 reviewOnly(r);
});
test('explicit register-to-archetype match preserves exact P2 source, revision and all missing evidence',()=>{
 const r=inspect(137,'CGA-R-001','CGXI-P2-R-001');
 assert.equal(r.machine.status,'EXPLICIT_REGISTERED_INSTANCE_CANDIDATE');
 assert.equal(r.machine.shape_role,'T173:137');
 assert.equal(r.machine.archetype_id,'CGA-R-001');
 assert.equal(r.machine.instance_id,'CGXI-P2-R-001');
 assert.equal(r.machine.selected_record.proof_stage,'P2');
 assert.equal(r.machine.selected_record.binding_state,'UNBOUND');
 assert.equal(r.machine.selected_record.physical_state,'NOT_RUN');
 assert.equal(r.machine.selected_record.geometry_revision,'UNRESOLVED');
 assert.equal(r.machine.selected_record.source_hashes,'UNRESOLVED');
 assert.equal(r.machine.selected_record.dbr_pointer,'UNRESOLVED');
 assert.match(r.human.next_binding,/Acquire\/passport/);
 reviewOnly(r);
});
test('P0 identity coupon uses original non-CGA namespace, not invented CGA alignment',()=>{
 const p0=population.records.find(x=>x.proof_stage==='P0');
 assert.equal(p0.archetype_id,'SH01-ID-A / CGX-PHYSOBJ-001');
 assert.equal(p0.instance_id,'CGXI-P0-SH01-ID-A');
 assert.throws(()=>inspect(1,'CGA-I-002',p0.instance_id));
 assert.equal(inspect(1,'CGA-I-002').machine.eligible_existing_instance_ids.includes(p0.instance_id),false);
});
test('role-to-CGA-to-instance remains a candidate regardless of T173 role',()=>{
 const a=inspect(1,'CGA-R-001','CGXI-P2-R-001');
 const b=inspect(173,'CGA-R-001','CGXI-P2-R-001');
 assert.notEqual(a.machine.shape_role,b.machine.shape_role);
 assert.equal(a.machine.instance_id,b.machine.instance_id);
 reviewOnly(a);reviewOnly(b);
});
test('unknown instance, mismatched archetype and missing explicit selection fail closed',()=>{
 for(const pair of [
   [null,'CGXI-P2-R-001'],
   ['CGA-C-001','CGXI-P2-R-001'],
   ['CGA-R-001','CGXI-P2-C-001'],
   ['CGA-R-001','CGXI-P9-FAKE-001'],
   ['CGA-R-001','../../../credential'],
   ['CGA-R-001','CGXI-P0-SH01-ID-A']
 ])assert.throws(()=>inspect(1,pair[0],pair[1]),undefined,JSON.stringify(pair));
});
test('invented, extra and malformed digest claims cannot authenticate owner source or grant rights',()=>{
 const spoof={...source_claims,instance_register_sha256:'f'.repeat(64)};
 const r=inspect(5,'CGA-I-002','CGXI-P1-TRACE-001',spoof);
 assert.equal(r.machine.source_claims_authenticated,false);
 assert.equal(r.machine.source_claims.instance_register_sha256,spoof.instance_register_sha256);
 reviewOnly(r);
 for(const claims of [
   {...source_claims,instance_register_sha256:'x'},
   {...source_claims,owner_authenticated:true},
   {geometry_atlas_sha256:source_claims.geometry_atlas_sha256}
 ])assert.throws(()=>inspect(5,'CGA-I-002','CGXI-P1-TRACE-001',claims));
});
test('duplicate IDs, invented binding progress, measured evidence and altered P0 identity are rejected',()=>{
 const variants=[];
 const change=(id,key,value)=>{
   const x=structuredClone(population);x.records[id][key]=value;return x;
 };
 variants.push(change(1,'instance_id',population.records[0].instance_id));
 variants.push(change(1,'binding_state','SOURCE_BOUND'));
 variants.push(change(1,'physical_state','MEASURED'));
 variants.push(change(1,'geometry_revision','CAD-V1'));
 variants.push(change(1,'source_hashes','a'.repeat(64)));
 variants.push(change(1,'readback_receipt','Signed receipt'));
 variants.push(change(1,'dbr_pointer','DBR-001'));
 variants.push(change(0,'archetype_id','CGA-I-002'));
 variants.push(change(0,'proof_stage','P2'));
 variants.push({...population,record_count:9});
 for(const v of variants)
   assert.throws(()=>verifyOriginalInstancePopulation(v,packet,ladder));
});
test('non-admitted original capsule or source data cannot be replaced with forged geometry/rights',()=>{
 assert.throws(()=>reviewTirExistingInstance(d,{...capsule(1),native_admitted:true},
   atlas,ladder,packet,population,{archetype_id:'CGA-I-002',
   instance_id:'CGXI-P1-TRACE-001',source_claims}));
 assert.throws(()=>reviewTirExistingInstance(d,{...capsule(1),geometry_ref:'invented_mesh'},
   atlas,ladder,packet,population,{archetype_id:'CGA-I-002',
   instance_id:'CGXI-P1-TRACE-001',source_claims}));
 const f=structuredClone(packet);f.required_instance_fields=['DBR'];
 assert.throws(()=>verifyOriginalInstancePopulation(population,f,ladder));
});


test('missing P0 envelope and required projected instance fields fail closed',()=>{
 const missing=structuredClone(population);
 const p0=missing.records.findIndex(r=>r.proof_stage==='P0');
 const replacement=structuredClone(missing.records.find(r=>r.proof_stage==='P1'));
 replacement.instance_id='CGXI-P1-ADDITIONAL';
 missing.records[p0]=replacement;
 assert.throws(()=>verifyOriginalInstancePopulation(missing,packet,ladder),/EXISTING_P0_IDENTITY_REQUIRED/);
 for(const key of ['instance_type','blocked_by_next_binding']){
  const broken=structuredClone(population);
  delete broken.records[1][key];
  assert.throws(()=>verifyOriginalInstancePopulation(broken,packet,ladder),/INSTANCE_RECORD_REQUIRED_FIELD_MISSING/);
 }
});
