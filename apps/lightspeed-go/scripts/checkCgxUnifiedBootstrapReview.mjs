import test from 'node:test';
import assert from 'node:assert/strict';
import {reviewUnifiedBootstrapBinding as review} from '../src/cgxUnifiedBootstrapReview.mjs';
// Synthetic envelopes: no authenticated host, signed lease, installed tool or DBR.
const id='fixture:ls:child',cap='fixture:load:viewport',rev='a'.repeat(40);
const steps=['discover','resume','identity','sources','load','tools','runtime',
 'ls_go','handshake','verify','handoff'];
function fixture(){
 return {
  source_pin:{repository:'achillesromer-coder/LightSpeed',pr:206,
   head_sha:'34f45718c13a1667bdb49fb6aea6736f4bf703eb',
   bootstrap_blob_sha:'dde0600c354799dbb428183c83ece7403b933b45',
   provider_verified:false,native_admitted:false},
  bootstrap_plan:{schema:'CGX-UNIFIED-BOOTSTRAP-PLAN/0.1',state:'REVIEW_ONLY',
   family:'LS.cgx',existing_runtime:{
    status_owner:'lightspeed_runtime.runtime_productization',
    settings_owner:'lightspeed_runtime.startup_options'},
   library:{name:'LOAD.cgx',bind:'EXISTING_IDENTITY_ONLY',install:false,network_hydration:false},
   ls_go:{requested:true,enabled:false,actual_toggle_write:false,separate_product:'UniSpace'},
   duplicate_wizard_authority:false,independent_host_acceptance:false,
   runtime_installed:false,source_ingested:false,canonical_accepted:false,
   ls_go_enabled:false,published:false,website_deployed:false,
   steps:steps.map(id=>({id,auto_run:false,canonical_mutation:false}))},
  semantic_review:{schema:'CGX-LS-LOAD-SEMANTIC-HOST-REVIEW/0.1',
   state:'HOST_REVALIDATION_REQUIRED',target_filespace:'LS.cgx',
   parent_filespace:'EMASSC.cgx',parent_ccc:'Cognigrex.cgx:/ccc',
   candidate_object_id:id,capability_id:cap,source_revision:rev,
   source_proof_independently_verified:false,rights_verified:false,
   native_admitted:false,capability_installed:false,host_authenticated:false,
   lease_verified:false,dbr_readback_verified:false,solver_invoked:false,
   rendered:false,hydration_performed:false,canonical_mutation:false,
   network_fetch:false,source_bytes_copied:0},
  request:{family:'LS.cgx',parent_filespace:'EMASSC.cgx',
   parent_ccc:'Cognigrex.cgx:/ccc',object_id:id,capability_id:cap,
   source_revision:rev,intent:'review',execution_requested:false,
   install_requested:false,publish_requested:false,network_permission:false,
   canonical_mutation_requested:false,max_transfer_bytes:0}
 };
}
const denied=(mutate,code)=>{const x=fixture();mutate(x);assert.equal(review(x).hold_code,code);};
test('pinned bootstrap and semantic source reviews only request host negative tests',()=>{
 const x=review(fixture());assert.equal(x.state,'HOST_NEGATIVE_TESTS_REQUIRED');
 assert.equal(x.candidate_object_id,id);assert.equal(x.ls_go_requested,true);
 assert.equal(x.ls_go_enabled,false);assert.equal(x.source_bytes_copied,0);
 for(const k of ['native_admitted','capability_installed','host_authenticated',
  'lease_verified','dbr_readback_verified','canonical_mutation','network_fetch'])
  assert.equal(x[k],false,k);
});
test('changed PR head or blob cannot be silently substituted',()=>{
 denied(x=>{x.source_pin.head_sha='b'.repeat(40);},'BOOTSTRAP_SOURCE_PIN_UNQUALIFIED');
 denied(x=>{x.source_pin.bootstrap_blob_sha='b'.repeat(40);},'BOOTSTRAP_SOURCE_PIN_UNQUALIFIED');
});
test('caller assertions of provider verification cannot promote source pin',()=>{
 denied(x=>{x.source_pin.provider_verified=true;},'BOOTSTRAP_SOURCE_PIN_UNQUALIFIED');
});
test('LS GO and runtime cannot be presented as installed or activated',()=>{
 denied(x=>{x.bootstrap_plan.ls_go.enabled=true;},'BOOTSTRAP_NOT_SOURCE_SAFE');
 denied(x=>{x.bootstrap_plan.runtime_installed=true;},'BOOTSTRAP_NOT_SOURCE_SAFE');
 denied(x=>{x.bootstrap_plan.canonical_accepted=true;},'BOOTSTRAP_NOT_SOURCE_SAFE');
});
test('one wizard cannot add executable setup steps',()=>{
 denied(x=>{x.bootstrap_plan.steps[1].auto_run=true;},'BOOTSTRAP_NOT_SOURCE_SAFE');
 denied(x=>{x.bootstrap_plan.steps.push({id:'second_installer',auto_run:false,canonical_mutation:false});},
  'BOOTSTRAP_NOT_SOURCE_SAFE');
});
test('wrong child or parent FileSpace is held',()=>{
 denied(x=>{x.bootstrap_plan.family='Eco.cgx';},'BOOTSTRAP_NOT_SOURCE_SAFE');
 denied(x=>{x.request.parent_filespace='Romer.cgx';},'CROSSWALK_SCOPE_OR_IDENTITY_MISMATCH');
});
test('semantic review cannot forge DBR, lease, host or solver proof',()=>{
 for(const k of ['dbr_readback_verified','lease_verified','host_authenticated','solver_invoked'])
  denied(x=>{x.semantic_review[k]=true;},'SEMANTIC_HOST_REVIEW_UNQUALIFIED');
});
test('identity, capability and source revision must match across envelopes',()=>{
 denied(x=>{x.request.object_id='fixture:other';},'CROSSWALK_SCOPE_OR_IDENTITY_MISMATCH');
 denied(x=>{x.request.capability_id='other';},'CROSSWALK_SCOPE_OR_IDENTITY_MISMATCH');
 denied(x=>{x.request.source_revision='b'.repeat(40);},'CROSSWALK_SCOPE_OR_IDENTITY_MISMATCH');
});
test('source review rejects install, network, publication and transferred bytes',()=>{
 for(const k of ['execution_requested','install_requested','publish_requested','network_permission'])
  denied(x=>{x.request[k]=true;},'CROSSWALK_SCOPE_OR_IDENTITY_MISMATCH');
 denied(x=>{x.request.max_transfer_bytes=1;},'CROSSWALK_SCOPE_OR_IDENTITY_MISMATCH');
});
test('unsigned host claims cannot be smuggled into the envelope',()=>{
 denied(x=>{x.host_claim={accepted:true};},'UNTRUSTED_HOST_ASSERTION');
 denied(x=>{x.dbr_receipt={signed:true};},'UNTRUSTED_HOST_ASSERTION');
});
test('secret-bearing fields are rejected without echo',()=>{
 const x=fixture();x.request.session_token='DO_NOT_ECHO';
 const y=review(x);assert.equal(y.hold_code,'INVALID_OR_SENSITIVE_ENVELOPE');
 assert.equal(JSON.stringify(y).includes('DO_NOT_ECHO'),false);
});
test('no fake native admission or source-body copy',()=>{
 denied(x=>{x.semantic_review.native_admitted=true;},'SEMANTIC_HOST_REVIEW_UNQUALIFIED');
 denied(x=>{x.semantic_review.source_bytes_copied=1;},'SEMANTIC_HOST_REVIEW_UNQUALIFIED');
});
