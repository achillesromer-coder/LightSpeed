import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {makeCapsule} from './tir173_core.mjs';
import {projectGuiosContext} from './tir173_context.mjs';
import {bindTirIntentToExistingPlans} from './tir173_intent_binding.mjs';
import {projectUniSpaceLoadLens} from '../../../apps/lightspeed-go/src/cgxLoadLibraryLensPlan.mjs';

const projectionBytes=readFileSync(new URL('../../../docs/agent-ingestion/local-agent-homes/Z+2_Neo/pilots/raphael_temporal/geometry_language/T173_NEO_ROLE_PROJECTION.review.json',import.meta.url));
const slots=JSON.parse(projectionBytes.toString('utf8')).slots;
const dictionary={
 schema:'cgx.t173.shape_dictionary/0.2',
 source_sha256:createHash('sha256').update(projectionBytes).digest('hex'),
 sentinel:null,
 roles:slots.map((r,i)=>({slot:i+1,role:'T173:'+String(i+1).padStart(3,'0'),
   name:'Raphael role '+(i+1),family:r.class,mesh_ref:String(r.mesh_ref),evidence:r.qualifier}))
};
const cap=makeCapsule(dictionary,{
 shape:173,path:[1,173],object_ref:'review:object',source_ref:'review:original',
 coarse:{level:0,status:'REFERENCE_ONLY'},fine:{level:3,status:'UNRESOLVED'},
 state:{basis:'review:axis',trit:0,validity:'UNRESOLVED'}
});
const lens=projectGuiosContext(dictionary,cap,{environment:'physical',spatial:'through'}).context;
const loadPlan={
 schema:'UNISPACE-CGX-LOAD-LENS-PLAN/0.1',state:'PLAN_ONLY_NOT_HYDRATED',
 alias:'LOAD.cgx',parent_filespace:'Cognigrex.cgx',object_id:cap.object_ref,
 native_admitted:false,hydrated:false,execution_performed:false,
 public_publish_authorized:false,canonical_mutation:false,
 host_context_readback_authenticated:false,source_rights_independently_verified:false,
 client_scope_independently_authenticated:false,requested_hydration:'H2',planned_hydration:'H2'
};
const rule={
 ID:'CIM-001','Source Family':'Interconnect','Target Family':'Ground/Shield',
 'Interaction Type':'return-path coupling',Mechanism:'current and return path interact',
 'Geometry Variables':'gap;orientation','State Variables':'I;f','Baseline Model':'Maxwell and circuit',
 'Higher-Order Trigger':'higher frequency','Validation Test':'VNA/TDR','Evidence State':'ESTABLISHED'
};
const atlas={schema:'CGX-COMPONENT-INTERACTION-MAP/0.1',record_count:1,
 authority:{drive_sheet:'30_CGX_Component_Interaction_Map_v0_1',
 rule:'Drive owns evidence; derivative is review only'},records:[rule]};
const atlasSelection={rule_id:'CIM-001',source_sha256:'a'.repeat(64)};
const common={loadPlan,atlas,atlasSelection};
const checkNoAction=r=>{
 assert.equal(r.machine.authority,'REVIEW_ONLY');
 for(const key of ['execution_performed','source_hydrated','rights_verified','geometry_verified',
   'native_admitted','physical_interaction_established','model_inference_performed',
   'model_weights_changed','mint_performed','signed_dbr','automatic_baseline_promotion'])
   assert.equal(r.machine[key],false,key);
 assert.equal(r.machine.source_bytes_transferred,0);
 assert.equal(r.machine.identity.object_ref,cap.object_ref);
 assert.equal(r.machine.identity.shape_role,cap.shape_role);
 assert.equal(r.intent_review.machine.command_executed,false);
 assert.equal(r.human.authority,'Review only');
};
test('exact SELECT binds only to dictionary identity, with no source/admission',()=>{
 const r=bindTirIntentToExistingPlans(dictionary,cap,lens,{...common,command:'SELECT T173:173'});
 assert.equal(r.machine.status,'DICTIONARY_REFERENCE_REVIEW');
 assert.equal(r.machine.adapter_result,null);
 assert.equal(r.intent_review.machine.address_trits,'20101');
 checkNoAction(r);
});
test('exact PLAN_HYDRATE binds existing LOAD review adapter; H2 is not hydrated',()=>{
 const r=bindTirIntentToExistingPlans(dictionary,cap,lens,{...common,command:'PLAN_HYDRATE T173:173'});
 assert.equal(r.machine.status,'EXISTING_LOAD_PLAN_REVIEW');
 assert.equal(r.machine.adapter_result.schema,'cgx.tir173.existing-load-seam/0.1');
 assert.equal(r.machine.adapter_result.requested_level,'H2');
 assert.equal(r.machine.adapter_result.source_bytes_transferred,0);
 assert.equal(r.machine.adapter_result.source_hydrated,false);
 assert.match(r.human.interpretation,/No hydration/);
 checkNoAction(r);
});
test('existing atlas rule is only source candidate; even ESTABLISHED never proves this shape',()=>{
 const r=bindTirIntentToExistingPlans(dictionary,cap,lens,{...common,command:'ATLAS_RULE T173:173'});
 assert.equal(r.machine.status,'EXISTING_ATLAS_RULE_REVIEW');
 assert.equal(r.machine.adapter_result.schema,'cgx.tir173.component-interaction-plan/0.1');
 assert.equal(r.machine.adapter_result.status,'SOURCE_RULE_CANDIDATE_ONLY');
 assert.equal(r.machine.adapter_result.source.source_evidence_state,'ESTABLISHED');
 assert.equal(r.machine.adapter_result.physical_interaction_established,false);
 assert.deepEqual(r.machine.adapter_result.missing_variables,['gap','orientation','I','f']);
 checkNoAction(r);
});
test('non-executable ambiguous requests and conflicting object roles never use either adapter',()=>{
 for(const command of [
   'mint T173:173','PLAN_HYDRATE T173:174','ATLAS_RULE T173:001',
   'PLAN_HYDRATE T173:173 now','ATLAS_RULE T173:173 CIM-001',
   'PLAN_HYDRATE T173:173 T173:001'
 ]){
   const r=bindTirIntentToExistingPlans(dictionary,cap,lens,{...common,command});
   assert.equal(r.machine.status,'ABSTAIN_REVIEW_REQUIRED',command);
   assert.equal(r.machine.adapter_result,null,command);
   checkNoAction(r);
 }
});
test('unbound review commands never silently invoke a different adapter',()=>{
 for(const command of ['PLAN_HYDRATE T173:173','ATLAS_RULE T173:173',
   'PLAN_TRANSFORM T173:173','ENCODE_BYTES T173:173','TRIAD T173:173']){
   const r=bindTirIntentToExistingPlans(dictionary,cap,lens,{command});
   assert.equal(r.machine.adapter_result,null);
   assert.equal(r.machine.status,'OPERANDS_OR_ADAPTER_REQUIRED');
   checkNoAction(r);
 }
});
test('LOAD cannot gain rights, native admission or mismatched hydration through intent binding',()=>{
 for(const patch of [{hydrated:true},{native_admitted:true},{execution_performed:true},
   {state:'HYDRATED'},{object_id:'review:other'},
   {planned_hydration:'H3'},{source_rights_independently_verified:true}]){
   assert.throws(()=>bindTirIntentToExistingPlans(dictionary,cap,lens,{
     ...common,command:'PLAN_HYDRATE T173:173',loadPlan:{...loadPlan,...patch}
   }),undefined,JSON.stringify(patch));
 }
});
test('forged atlas rights, incomplete row selector and context identity cannot escalate',()=>{
 for(const selection of [
   {...atlasSelection,rule_id:'CIM-999'},
   {...atlasSelection,source_sha256:'not-a-digest'},
   {...atlasSelection,source_facet_ref:'review:source'},
   {...atlasSelection,measured:{gap:{value:NaN,unit:'m',source_ref:'review:sensor'}}}
 ]){
   assert.throws(()=>bindTirIntentToExistingPlans(dictionary,cap,lens,{
     ...common,command:'ATLAS_RULE T173:173',atlasSelection:selection
   }));
 }
 for(const drift of [{...lens,object_ref:'review:someone-else'},
   {...lens,interaction:{...lens.interaction,relation_established:true}},
   {...lens,native_admitted:true},
   {...lens,dictionary_source_sha256:'b'.repeat(64)}]){
   assert.throws(()=>bindTirIntentToExistingPlans(dictionary,cap,drift,{...common,command:'SELECT T173:173'}));
 }
 assert.throws(()=>bindTirIntentToExistingPlans(dictionary,{...cap,native_admitted:true},lens,{...common,command:'SELECT T173:173'}));
});


test('existing LOAD planner offline H1-H3 review output binds without fabricating hydration',()=>{
 const activation=JSON.parse(readFileSync(new URL('../../load_minimum/activation_contract.json',import.meta.url),'utf8'));
 const filespace='Cognigrex.cgx',object_id=cap.object_ref;
 for(const requested_hydration of ['H0','H1','H2','H3'])for(const offline of [true,false]){
  const plan=projectUniSpaceLoadLens({load_contract:activation,requested_object_id:object_id,destination_filespace:filespace,requested_hydration,requested_layer:'R0',offline,
   context_plan:{schema:'UNISPACE-CGX-HOST-CONTEXT-GATE/0.1',state:'PLAN_ONLY_NOT_HYDRATED',object_id,filespace,source_lineage_git_blob_sha:'a'.repeat(40),source_registry_git_blob_sha:'b'.repeat(40),native_admitted:false,canonical_mutation:false,execution_performed:false,private_hydration_authorized:false,public_publish_authorized:false,host_context_readback_authenticated:false,source_registry_independently_verified:false},
   client_permissions:{mode:'review_only',revoked:false,allowed_object_ids:[object_id],allowed_filespaces:[filespace]},source_status:{collision:'no_conflict_reported',rights:'cleared_for_review',evidence_class:'scientific'}});
  assert.equal(plan.state,'PLAN_ONLY_NOT_HYDRATED');
  const result=bindTirIntentToExistingPlans(dictionary,cap,lens,{command:'PLAN_HYDRATE T173:173',loadPlan:plan});
  assert.equal(result.machine.status,'EXISTING_LOAD_PLAN_REVIEW');assert.equal(result.machine.adapter_result.requested_level,requested_hydration);assert.equal(result.machine.adapter_result.planned_level,offline?'H0':requested_hydration);checkNoAction(result);
 }
});
