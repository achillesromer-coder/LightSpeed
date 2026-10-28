import test from 'node:test';
import assert from 'node:assert/strict';
import {reviewLoadSemanticHost as review} from '../src/cgxLoadSemanticHostReview.mjs';
// Synthetic source-only fixtures; not authenticated LOAD, native host or DBR evidence.
const ceilings={max_nodes:8,max_hops:2,max_cross_domains:1,max_cross_edges:4,
 max_evidence_refs:8,max_compute_ms:2000,max_ops_per_second:50,max_transfer_bytes:0};
function fixture(mode='viewport'){
 const id='fixture:ls:root',cap='load-hydration-review';
 const x={
  hydration_review:{
   schema:'CGX-LS-LOAD-HOST-HYDRATION-REVIEW/0.1',state:'HOST_HANDSHAKE_REQUIRED',
   target_filespace:'LS.cgx',parent_filespace:'EMASSC.cgx',parent_ccc:'Cognigrex.cgx:/ccc',
   candidate_object_id:id,capability_id:cap,source_revision:'a'.repeat(40),
   native_admitted:false,capability_installed:false,host_authenticated:false,
   owner_lease_verified:false,dbr_readback_verified:false,hydration_performed:false,
   network_fetch:false,canonical_mutation:false,source_proof_independently_verified:false,
   source_rights_verified:false,source_bytes_copied:0,
  },
  spread:{
   schema:'LOAD-SEMANTIC-SPREAD-PLAN/0.1',status:'REVIEW_ONLY',focus_id:id,
   objects:[{object_id:id,domain:'lightspeed',source_refs:['fixture:source']}],
   edges:[],frontier:[],budgets:{...ceilings,reasoning_depth:'standard',
     device_hydration:'reader',execution_depth:'inspect'},
   max_planned_operations:100,actual_compute_ms:null,actual_ops_per_second:null,
   requested_ceiling_only:true,network_fetch:false,rendered:false,
   canonical_mutation:false,hydration_complete:false,
  },
  request:{target_filespace:'LS.cgx',parent_filespace:'EMASSC.cgx',
   parent_ccc:'Cognigrex.cgx:/ccc',object_id:id,focus_id:id,capability_id:cap,
   mode,budget_ceiling:{...ceilings},max_transfer_bytes:0,
   network_permission:false,execution_requested:false,install_requested:false,
   publish_requested:false,canonical_mutation_requested:false,
  }
 };
 if(mode==='viewport'){
  x.request.view='graph';
  x.viewport_plan={schema:'LOAD-VIEWPORT-SWITCH-PLAN/0.1',identity:id,
   to:'graph',state:'VIEW_PLAN_READY',network_fetch:false,rendered:false,
   interactive_execution:false,semantic_mutation:false,public_release:false};
 }else{
  x.operator_plan={schema:'LOAD-QUALIFIED-OPERATOR-PLAN/0.1',
   status:'SOURCE_ONLY_NO_EXECUTION',computation_executed:false,
   numeric_result:null,object_ids_minted:0,operator_candidates:[{
    route_key:'science.query',state:'EXPLICIT_TYPED_OPERATOR_CANDIDATE',
    solver_invoked:false,results_generated:false,
    blockers:['HOST_CAPABILITY_LEASE_AND_DB_R_READBACK_REQUIRED']
   }]};
 }
 return x;
}
const denied=(mutate,code,mode='viewport')=>{
 const x=fixture(mode);mutate(x);assert.equal(review(x).hold_code,code);
};
test('source-only viewport produces host revalidation, never rendering',()=>{
 const x=review(fixture());
 assert.equal(x.state,'HOST_REVALIDATION_REQUIRED');
 assert.equal(x.max_planned_operations,100);
 for(const key of ['native_admitted','capability_installed','host_authenticated',
  'lease_verified','dbr_readback_verified','solver_invoked','rendered',
  'hydration_performed','canonical_mutation','network_fetch'])assert.equal(x[key],false,key);
});
test('typed science route is candidate only, never numerical execution',()=>{
 const x=review(fixture('operator'));assert.equal(x.state,'HOST_REVALIDATION_REQUIRED');
 assert.equal(x.solver_invoked,false);assert.equal(x.source_bytes_copied,0);
});
test('forged host proof in envelope cannot upgrade review',()=>{
 denied(x=>{x.hydration_review.host_authenticated=true;},'HYDRATION_SOURCE_REVIEW_UNQUALIFIED');
 denied(x=>{x.hydration_review.dbr_readback_verified=true;},'HYDRATION_SOURCE_REVIEW_UNQUALIFIED');
});
test('host lease/receipt assertions are not accepted',()=>{
 denied(x=>{x.host_claim={state:'CAN_DO'};},'HOST_ASSERTION_NOT_EVIDENCE');
 denied(x=>{x.dbr_receipt={signed:true};},'HOST_ASSERTION_NOT_EVIDENCE');
});
test('Römer child substitution and identity mismatch are held',()=>{
 denied(x=>{x.request.target_filespace='Romer.cgx';},'REQUEST_SCOPE_OR_IDENTITY_MISMATCH');
 denied(x=>{x.spread.focus_id='fixture:eco:other';},'SEMANTIC_SPREAD_NOT_REVIEW_ONLY');
});
test('unauthorised extra object ID or duplicate is rejected',()=>{
 denied(x=>{x.spread.objects.push({...x.spread.objects[0]});},'UNQUALIFIED_OR_COLLIDING_OBJECTS');
 denied(x=>{x.spread.objects[0].object_id='fixture:private';},'SEMANTIC_SPREAD_NOT_REVIEW_ONLY');
});
test('node, hop, cross-domain, edge and evidence ceilings are orthogonal',()=>{
 for(const k of ['max_nodes','max_hops','max_cross_domains','max_cross_edges','max_evidence_refs']){
  denied(x=>{x.spread.budgets[k]=x.request.budget_ceiling[k]+1;},
   'INDEPENDENT_BUDGET_EXCEEDED');
 }
});
test('compute milliseconds and rate have independent ceilings',()=>{
 for(const k of ['max_compute_ms','max_ops_per_second']){
  denied(x=>{x.spread.budgets[k]=x.request.budget_ceiling[k]+1;},
   'INDEPENDENT_BUDGET_EXCEEDED');
 }
});
test('declared maximum operations must equal floor(ms * rate / 1000)',()=>{
 denied(x=>{x.spread.max_planned_operations=101;},'INDEPENDENT_BUDGET_EXCEEDED');
});
test('zero source bytes and no network are mandatory',()=>{
 denied(x=>{x.request.max_transfer_bytes=1;},'REQUEST_SCOPE_OR_IDENTITY_MISMATCH');
 denied(x=>{x.request.network_permission=true;},'REQUEST_SCOPE_OR_IDENTITY_MISMATCH');
 denied(x=>{x.spread.network_fetch=true;},'SEMANTIC_SPREAD_NOT_REVIEW_ONLY');
});
test('actual compute measurements cannot be fabricated in source plan',()=>{
 denied(x=>{x.spread.actual_compute_ms=10;},'SEMANTIC_SPREAD_NOT_REVIEW_ONLY');
 denied(x=>{x.spread.actual_ops_per_second=5;},'SEMANTIC_SPREAD_NOT_REVIEW_ONLY');
});
test('geometry viewport without qualified frame remains held',()=>{
 denied(x=>{x.request.view='3d';x.viewport_plan.to='3d';
  x.viewport_plan.state='FRONTIER_GEOMETRY_UNQUALIFIED';},'VIEWPORT_NOT_SOURCE_QUALIFIED');
});
test('viewport cannot claim rendering, interaction or public release',()=>{
 for(const k of ['rendered','interactive_execution','public_release'])
  denied(x=>{x.viewport_plan[k]=true;},'VIEWPORT_NOT_SOURCE_QUALIFIED');
});
test('operator route cannot claim solver execution or numerical result',()=>{
 denied(x=>{x.operator_plan.computation_executed=true;},'OPERATOR_NOT_SOURCE_QUALIFIED','operator');
 denied(x=>{x.operator_plan.numeric_result=42;},'OPERATOR_NOT_SOURCE_QUALIFIED','operator');
 denied(x=>{x.operator_plan.operator_candidates[0].solver_invoked=true;},
  'DUPLICATE_OR_UNQUALIFIED_OPERATOR','operator');
});
test('duplicate CCC route cannot create a second executable candidate',()=>{
 denied(x=>{x.operator_plan.operator_candidates.push({...x.operator_plan.operator_candidates[0]});},
  'DUPLICATE_OR_UNQUALIFIED_OPERATOR','operator');
});
test('source-only route must retain host lease and DBR blocker',()=>{
 denied(x=>{x.operator_plan.operator_candidates[0].blockers=[];},
  'DUPLICATE_OR_UNQUALIFIED_OPERATOR','operator');
});
test('secret-bearing fields are rejected without echoing their value',()=>{
 const x=fixture();x.request.session_token='DO_NOT_ECHO';
 const y=review(x);assert.equal(y.hold_code,'INVALID_OR_SENSITIVE_ENVELOPE');
 assert.equal(JSON.stringify(y).includes('DO_NOT_ECHO'),false);
});
test('operator plan cannot be swapped into viewport mode',()=>{
 denied(x=>{x.operator_plan=fixture('operator').operator_plan;},'UNEXPECTED_OPERATOR_PLAN');
});
