import test from 'node:test';
import assert from 'node:assert/strict';
import {reviewNativeRuntimeReadback as review} from '../src/cgxNativeRuntimeReadbackReview.mjs';
// Synthetic untrusted Python-output shapes. No host, runtime or DBR is contacted.
const rev='a'.repeat(40),id='fixture:ls:child',cap='fixture:load:viewport';
const floors={
 Trinity:'Z+3_Trinity',Neo:'Z+2_Neo',Architect:'Z+1_Architect',
 TheConstruct:'Z0_TheConstruct',Morpheus:'Z-1_Morpheus',
 Oracle:'Z-2_Oracle',Smith:'Z-3_Smith',Merovingian:'Z-4_Merovingian'
};
function fixture(){
 return {
  bootstrap_review:{schema:'CGX-LS-UNIFIED-BOOTSTRAP-REVIEW/0.1',
   state:'HOST_NEGATIVE_TESTS_REQUIRED',candidate_filespace:'LS.cgx',
   parent_filespace:'EMASSC.cgx',parent_ccc:'Cognigrex.cgx:/ccc',
   candidate_object_id:id,capability_id:cap,load_source_revision:rev,
   bootstrap_source_head:'34f45718c13a1667bdb49fb6aea6736f4bf703eb',
   bootstrap_source_blob:'dde0600c354799dbb428183c83ece7403b933b45',
   runtime_owner:'lightspeed_runtime.runtime_productization',
   startup_owner:'lightspeed_runtime.startup_options',
   native_admitted:false,capability_installed:false,host_authenticated:false,
   lease_verified:false,dbr_readback_verified:false,canonical_mutation:false,
   ls_go_enabled:false,source_bytes_copied:0},
  runtime_status:{schema:'LIGHTSPEED-RUNTIME-PRODUCTIZATION-STATUS/0.1',
   slot:'neo-review',source_head:'b'.repeat(40),managed_root:'D:/review',
   slot_root:'D:/review/neo-review',managed_marker:false,configured:false,
   profile:'core',installed:false,python:'D:/review/venv/Scripts/python.exe',
   recent_receipts:[],authority:'status-only'},
  startup_profile:{root:'D:/LightSpeed/App',
   source_files:{settings:'D:/LightSpeed/App/config/settings.json'},
   global_options:{first_run_complete:false,show_splash_screen:true,
    max_concurrent_jobs:4},
   floors:Object.fromEntries(Object.entries(floors).map(([name,canonical_id])=>
    [name,{floor:name,canonical_id,enabled:false,autostart:false}]))},
  request:{family:'LS.cgx',object_id:id,capability_id:cap,source_revision:rev,
   slot:'neo-review',intent:'review',execution_requested:false,
   install_requested:false,canonical_mutation_requested:false}
 };
}
const denied=(change,code)=>{const x=fixture();change(x);assert.equal(review(x).hold_code,code);};
test('synthetic Python shapes request authenticated host, never assert install',()=>{
 const y=review(fixture());assert.equal(y.state,'AUTHENTICATED_HOST_READBACK_REQUIRED');
 assert.equal(y.runtime_status_shape_checked,true);
 assert.equal(y.startup_profile_shape_checked,true);
 for(const k of ['runtime_installed_verified','host_authenticated','lease_verified',
  'dbr_readback_verified','native_admitted','capability_installed','canonical_mutation'])
  assert.equal(y[k],false,k);
 assert.equal(y.source_bytes_copied,0);
});
test('caller-reported installed=true never upgrades evidence',()=>{
 const x=fixture();x.runtime_status.installed=true;
 const y=review(x);assert.equal(y.state,'AUTHENTICATED_HOST_READBACK_REQUIRED');
 assert.equal(y.runtime_installed_verified,false);
});
test('runtime source revision is observed shape, not the PR bootstrap pin',()=>{
 const x=fixture();x.runtime_status.source_head='c'.repeat(40);
 assert.equal(review(x).state,'AUTHENTICATED_HOST_READBACK_REQUIRED');
});
test('incorrect status schema and authority fail closed',()=>{
 denied(x=>{x.runtime_status.schema='RUNTIME-RECEIPT/0.1';},'RUNTIME_STATUS_SHAPE_INVALID');
 denied(x=>{x.runtime_status.authority='host-execution';},'RUNTIME_STATUS_SHAPE_INVALID');
});
test('mismatched slot and invalid runtime source hash fail closed',()=>{
 denied(x=>{x.runtime_status.slot='another';},'RUNTIME_STATUS_SHAPE_INVALID');
 denied(x=>{x.runtime_status.source_head='unverified';},'RUNTIME_STATUS_SHAPE_INVALID');
});
test('status receipt paths are references only and cannot smuggle authority',()=>{
 const x=fixture();x.runtime_status.recent_receipts=['D:/review/receipt.json'];
 assert.equal(review(x).dbr_readback_verified,false);
 denied(x=>{x.runtime_status.signed_lease=true;},'RUNTIME_STATUS_SHAPE_INVALID');
});
test('missing managed-runtime flags or invalid profile are held',()=>{
 denied(x=>{delete x.runtime_status.installed;},'RUNTIME_STATUS_SHAPE_INVALID');
 denied(x=>{x.runtime_status.profile='arbitrary';},'RUNTIME_STATUS_SHAPE_INVALID');
});
test('eight Z floors must match existing startup_options canonical identities',()=>{
 denied(x=>{delete x.startup_profile.floors.Neo;},'STARTUP_PROFILE_SHAPE_INVALID');
 denied(x=>{x.startup_profile.floors.Neo.canonical_id='Z+3_Neo';},
  'STARTUP_PROFILE_SHAPE_INVALID');
});
test('startup flags must be typed; no auto-start implied',()=>{
 denied(x=>{x.startup_profile.global_options.first_run_complete='yes';},
  'STARTUP_PROFILE_SHAPE_INVALID');
 denied(x=>{x.startup_profile.floors.Oracle.autostart='yes';},
  'STARTUP_PROFILE_SHAPE_INVALID');
});
test('request object, capability and source identity must agree',()=>{
 denied(x=>{x.request.object_id='fixture:other';},'REQUEST_SCOPE_MISMATCH');
 denied(x=>{x.request.capability_id='fixture:other';},'REQUEST_SCOPE_MISMATCH');
 denied(x=>{x.request.source_revision='d'.repeat(40);},'REQUEST_SCOPE_MISMATCH');
});
test('execution, install, mutation and wrong family are rejected',()=>{
 denied(x=>{x.request.execution_requested=true;},'REQUEST_SCOPE_MISMATCH');
 denied(x=>{x.request.install_requested=true;},'REQUEST_SCOPE_MISMATCH');
 denied(x=>{x.request.canonical_mutation_requested=true;},'REQUEST_SCOPE_MISMATCH');
 denied(x=>{x.request.family='Eco.cgx';},'REQUEST_SCOPE_MISMATCH');
});
test('forged bootstrap host/DBR proof and source bytes are held',()=>{
 denied(x=>{x.bootstrap_review.host_authenticated=true;},'BOOTSTRAP_REVIEW_NOT_QUALIFIED');
 denied(x=>{x.bootstrap_review.dbr_readback_verified=true;},'BOOTSTRAP_REVIEW_NOT_QUALIFIED');
 denied(x=>{x.bootstrap_review.source_bytes_copied=1;},'BOOTSTRAP_REVIEW_NOT_QUALIFIED');
});
test('secret-bearing keys and untrusted host receipts never echo',()=>{
 const x=fixture();x.runtime_status.session_token='NEVER_ECHO';
 const y=review(x);assert.equal(y.hold_code,'INVALID_OR_SENSITIVE_ENVELOPE');
 assert.equal(JSON.stringify(y).includes('NEVER_ECHO'),false);
 denied(x=>{x.host_receipt={signed:true};},'INVALID_OR_SENSITIVE_ENVELOPE');
});

test('managed slot ABI rejects path-like and non-native names before host status',()=>{
 // Python runtime_productization.SLOT_RE: ^[A-Za-z0-9][A-Za-z0-9_.-]{0,47}$
 for(const bad of ['neo/review','neo:review','neo\\\\review',' neo',
                   '.neo','neo review','neo/review/child','éneo']){
  denied(x=>{x.request.slot=bad;x.runtime_status.slot=bad;},'REQUEST_SCOPE_MISMATCH');
 }
});
test('managed slot ABI preserves the 48-character bound, rejects 49',()=>{
 const good=fixture();good.request.slot='n'.repeat(48);
 good.runtime_status.slot=good.request.slot;
 assert.equal(review(good).state,'AUTHENTICATED_HOST_READBACK_REQUIRED');
 denied(x=>{x.request.slot='n'.repeat(49);x.runtime_status.slot=x.request.slot;},
  'REQUEST_SCOPE_MISMATCH');
});
