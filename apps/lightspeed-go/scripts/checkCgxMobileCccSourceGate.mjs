import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { planCgxMobileCccSourceCapability as plan } from '../src/cgxMobileCccSourceGate.mjs';

// Uses the actual checked-in canonical source-blueprint files, not invented registry shapes.
const registry = JSON.parse(readFileSync(new URL('../../../cgx/domain_templates/toolkit_registry.json', import.meta.url)));
const topology = JSON.parse(readFileSync(new URL('../../../cgx/domain_templates/cognigrex_parent_topology.json', import.meta.url)));
const make = () => ({
  toolkit_registry: structuredClone(registry), parent_topology: structuredClone(topology),
  candidate: {
    schema: 'CGX-CCC-CAPABILITY-CANDIDATE/0.1', package_id: 'lsgo-mobile',
    capability_id: 'mobile-origin-plan', version: '0.1.0',
    abi: 'CGX-CCC-METADATA-PLAN/0.1',
    parent_filespace: 'EMASSC.cgx', filespace: 'LS.cgx',
    ccc_location: 'Cognigrex.cgx:/ccc',
    source: {provider:'github',repository:'achillesromer-coder/LightSpeed',
      path:'apps/lightspeed-go/src/desktopBridge.ts',
      revision:'d40aa0fcdcc297aaba881ee3ae2d6316f8f809cb',
      blob_sha:'eb573a4ec14b6c1493393d3a0474ae88aeff8221',
      content_sha256:'a'.repeat(64)},
    licence_ref: 'repository licence review pending', rights_review_state:'unverified',
    permissions:['metadata:read'],
  },
  request:{operation:'plan',requested_scope:'metadata_only',execution_requested:false,
    authority_transfer:false,canonical_mutation:false,public_publish_authorized:false},
});
const expectHold = (mutate, code) => {
  const x=make(); mutate(x); assert.equal(plan(x).hold_code,code);
};
test('real parent CCC and LS child produce source-only metadata plan',()=>{
  const x=plan(make()); assert.equal(x.state,'PLAN_ONLY');
  assert.equal(x.filespace,'LS.cgx'); assert.equal(x.ccc_location,'Cognigrex.cgx:/ccc');
  for (const key of ['native_admitted','capability_installed','execution_performed',
    'owner_authorized','source_rights_verified','abi_conformance_verified',
    'provider_readback_authenticated','canonical_mutation','public_publish_authorized'])
    assert.equal(x[key],false,key);
});
test('discovery only never installs',()=>{const x=make();x.request.operation='discover';assert.equal(plan(x).state,'DISCOVERY_ONLY');});
test('no CCC registry means HOLD',()=>expectHold(x=>{x.toolkit_registry.toolkits=x.toolkit_registry.toolkits.filter(t=>t.id!=='ccc');},'CCC_PARENT_BINDING_UNVERIFIED'));
test('duplicate CCC registry means HOLD',()=>expectHold(x=>{x.toolkit_registry.toolkits.push(structuredClone(x.toolkit_registry.toolkits.find(t=>t.id==='ccc')));},'CCC_PARENT_BINDING_UNVERIFIED'));
test('registry secrets policy cannot be weakened',()=>expectHold(x=>{x.toolkit_registry.secrets_policy='embedded-tokens';},'CCC_REGISTRY_SCHEMA_UNVERIFIED'));
test('LS cannot become a parent or sibling master',()=>expectHold(x=>{x.parent_topology.root.children.find(v=>v.id==='emassc').children=[];},'CHILD_OR_CCC_TOPOLOGY_UNVERIFIED'));
test('CCC must remain at parent',()=>expectHold(x=>{x.parent_topology.shared_root_services.find(v=>v.id==='ccc').location='LS.cgx:/ccc';},'CHILD_OR_CCC_TOPOLOGY_UNVERIFIED'));
test('candidate cannot claim Romer or Eco owner filespace',()=>expectHold(x=>{x.candidate.filespace='Romer.cgx';},'WRONG_CHILD_FILESPACE'));
test('candidate must declare explicit ABI and version',()=>expectHold(x=>{x.candidate.version='latest';},'CANDIDATE_ID_VERSION_OR_ABI_INVALID'));
test('source provider must retain revision and two hash classes',()=>expectHold(x=>{x.candidate.source.blob_sha='not-a-hash';},'SOURCE_IDENTITY_OR_HASH_INVALID'));
test('source path traversal rejected',()=>expectHold(x=>{x.candidate.source.path='../private/credentials';},'SOURCE_IDENTITY_OR_HASH_INVALID'));
test('licence and permission cannot be silently promoted',()=>expectHold(x=>{x.candidate.permissions=['metadata:read','execute'];},'RIGHTS_OR_PERMISSIONS_UNVERIFIED'));
test('apply and unapply cannot execute from mobile source review',()=>{
  for(const op of ['apply','unapply','verify','receipts']) expectHold(x=>{x.request.operation=op;},'OPERATION_NOT_MOBILE_SOURCE_SAFE');
});
test('execution, publication, authority and mutation flags fail closed',()=>{
  for(const k of ['execution_requested','authority_transfer','canonical_mutation','public_publish_authorized'])
    expectHold(x=>{x.request[k]=true;},'EXECUTION_OR_AUTHORITY_REQUESTED');
});
test('secret-bearing input is rejected and not echoed',()=>{
  const x=make();x.candidate.session_token='SHOULD_NOT_ECHO';
  const y=plan(x);assert.equal(y.hold_code,'SENSITIVE_OR_UNBOUNDED_INPUT');
  assert.equal(JSON.stringify(y).includes('SHOULD_NOT_ECHO'),false);
});
test('metadata plan does not echo sensitive source path',()=>{
  const x=make();x.candidate.source.path='private/owner-material.txt';
  const y=plan(x);assert.equal(y.state,'PLAN_ONLY');
  assert.equal(JSON.stringify(y).includes('private/owner-material'),false);
});
test('null or cyclic candidate is held',()=>{
  assert.equal(plan(null).hold_code,'INVALID_INPUT');
  const x=make();x.candidate.self=x.candidate;
  assert.equal(plan(x).hold_code,'SENSITIVE_OR_UNBOUNDED_INPUT');
});

import { reviewCgxMobileHostCapabilityClaim as reviewHost } from '../src/cgxMobileHostAssessmentReview.mjs';

const hostCase = () => {
  const p = plan(make());
  const request = {
    schema_version:'cgx-roaming-request-v1', request_id:'neo-host-claim-001',
    required_capability_id:p.capability_id, expected_revision_or_cursor:p.source_revision,
    input_content_hashes:['b'.repeat(64)], status:'staged', requested_intent:'metadata_only',
    created_utc:'2026-10-28T03:00:00Z', expires_utc:'2026-10-28T04:00:00Z',
  };
  return {preflight:p, request, now_utc:'2026-10-28T03:15:00Z'};
};
const claimed = x => ({
  schema:'CGX-ROAMING-ASSESSMENT-CANDIDATE/0.1', request_id:x.request.request_id,
  required_capability_id:x.request.required_capability_id,
  source_revision:x.request.expected_revision_or_cursor,
  input_content_hashes:[...x.request.input_content_hashes],
  decision:'CAN_DO', operation_state:'assessed',
});
test('without host claim preflight remains WAIT_HOST and HELD',()=>{
  const r=reviewHost(hostCase());assert.equal(r.state,'WAIT_HOST');
  assert.equal(r.effective_decision,'HELD');assert.equal(r.execution_performed,false);
});
test('claimed CAN_DO never becomes host permission, DBR or installed runtime',()=>{
  const x=hostCase();x.assessment=claimed(x);
  const r=reviewHost(x);assert.equal(r.state,'UNVERIFIED_HOST_CLAIM');
  assert.equal(r.reported_decision,'CAN_DO');assert.equal(r.effective_decision,'HELD');
  for(const key of ['host_readback_authenticated','owner_lease_verified','native_admitted',
    'execution_performed','dbr_receipt_verified','drive_backup_verified'])
    assert.equal(r[key],false,key);
});
test('claimed CAN_DO_WHEN_READY and UNSUPPORTED remain source-only',()=>{
  for(const decision of ['CAN_DO_WHEN_READY','UNSUPPORTED']){
    const x=hostCase();x.assessment={...claimed(x),decision};
    const r=reviewHost(x);assert.equal(r.reported_decision,decision);
    assert.equal(r.effective_decision,'HELD');
  }
});
test('claimed HELD is held, not promoted',()=>{
  const x=hostCase();x.assessment={...claimed(x),decision:'HELD',operation_state:'held'};
  assert.equal(reviewHost(x).hold_code,'HOST_REPORTS_HELD');
});
test('claim with different request id is rejected',()=>{
  const x=hostCase();x.assessment={...claimed(x),request_id:'different'};
  assert.equal(reviewHost(x).hold_code,'HOST_CLAIM_IDENTITY_OR_HASH_MISMATCH');
});
test('claim with different source revision is rejected',()=>{
  const x=hostCase();x.assessment={...claimed(x),source_revision:'c'.repeat(40)};
  assert.equal(reviewHost(x).hold_code,'HOST_CLAIM_IDENTITY_OR_HASH_MISMATCH');
});
test('claim with conflicting input hash is rejected',()=>{
  const x=hostCase();x.assessment={...claimed(x),input_content_hashes:['c'.repeat(64)]};
  assert.equal(reviewHost(x).hold_code,'HOST_CLAIM_IDENTITY_OR_HASH_MISMATCH');
});
test('expired or premature request is held at deterministic fixture clock',()=>{
  for(const now of ['2026-10-28T02:59:59Z','2026-10-28T04:00:00Z']){
    const x=hostCase();x.now_utc=now;
    assert.equal(reviewHost(x).hold_code,'REQUEST_NOT_CURRENT_AT_FIXTURE_CLOCK');
  }
});
test('replayed request ID is held',()=>{
  const x=hostCase();x.seen_request_ids=[x.request.request_id];
  assert.equal(reviewHost(x).hold_code,'DUPLICATE_REQUEST_ID');
});
test('host claims of execution or running cannot pass review',()=>{
  for(const variant of [{execution_performed:true},{operation_state:'running'},{operation_state:'executed'}]){
    const x=hostCase();x.assessment={...claimed(x),...variant};
    assert.equal(reviewHost(x).hold_code,'HOST_CLAIM_NOT_REVIEWABLE');
  }
});
test('secret-bearing claim is rejected without echo',()=>{
  const x=hostCase();x.assessment={...claimed(x),session_token:'DO_NOT_ECHO'};
  const r=reviewHost(x);assert.equal(r.hold_code,'SENSITIVE_OR_UNBOUNDED_INPUT');
  assert.equal(JSON.stringify(r).includes('DO_NOT_ECHO'),false);
});
test('source gate HOLD cannot be upgraded by a forged host claim',()=>{
  const x=hostCase();x.preflight={...x.preflight,state:'HOLD'};
  x.assessment=claimed(x);
  assert.equal(reviewHost(x).hold_code,'SOURCE_PREFLIGHT_NOT_QUALIFIED');
});
test('untrusted clock and wrong capability never create a runnable state',()=>{
  const x=hostCase();x.request.required_capability_id='other';
  assert.equal(reviewHost(x).hold_code,'REQUEST_IDENTITY_OR_SCOPE_INVALID');
  const y=hostCase();y.now_utc='not-a-clock';
  assert.equal(reviewHost(y).hold_code,'CLOCK_OR_EXPIRY_FORMAT_INVALID');
});


// LOAD.cgx draft PR #205 -> Neo LS.cgx source-only host-hydration crosswalk.
// Fixture pins are read from the provider's review branch; a matching string is
// NOT authenticated provider readback, a licence grant or native S92 acceptance.
import {reviewCgxLoadHostHydration as reviewLoad} from '../src/cgxLoadHostHydrationReview.mjs';
const loadCase=()=>{
 const candidate=make();
 candidate.candidate.capability_id='load-hydration-review';
 candidate.candidate.source.path='cgx/load_minimum/loadOnlineRegistry.mjs';
 candidate.candidate.source.revision='4c65cbf2d069579ea24ca4f6466901d4530253bb';
 candidate.candidate.source.blob_sha='f6f2ada9b46a72eefe3904bf410ad2d8b4e56a49';
 // Synthetic content hash: test fixture only, not verified source proof.
 candidate.candidate.source.content_sha256='a'.repeat(64);
 const c=plan(candidate),objectId='cgx:domain:lightspeed';
 return {
  source_pin:{schema:'LOAD-ALEXANDRIA-SOURCE-REGISTRY-PROJECTION/0.1',
   state:'GIT_SOURCE_ONLY_NOT_CANONICAL',repository:'achillesromer-coder/LightSpeed',
   revision:'4c65cbf2d069579ea24ca4f6466901d4530253bb',
   registry_blob:'6cb487d8a10827b14284dc63088d908138cc7f80',
   native_accepted:0,native_host_verified:false,source_bodies_copied:0},
  mapping:{category:'filespace_action',source_key:'load.hydrate',
   source_registry:'cgx/load_minimum/filespace_feature_registry.json',
   source_git_blob:'31ab6c546f17d086424a42b7821796bc80128b94',
   admission:'SOURCE_REGISTRY_ONLY',installed_online:false},
  feature_plan:{schema:'CGX-UNISPACE-FILESPACE-FEATURE-PLAN/0.1',
   action:'load.hydrate',status:'REVIEW_ONLY',
   target:{kind:'filespace',fileSpace:'LS.cgx',parentFileSpace:'EMASSC.cgx',
    owner:'Neo',objectId},
   requestedHydration:'minimal',requestedMode:'TRACK',sourceByteCount:0,
   blockers:[],sourceCopied:false,canonicalMutation:false,
   networkFetch:false,install:false,execute:false,publish:false},
  scoped_plan:{schema:'LOAD-SCOPED-FILESPACE-PLAN/0.1',
   state:'HOST_PREFLIGHT_REQUIRED',target:{fileSpace:'LS.cgx',owner:'Neo',objectId},
   source_metadata_only:true,external_fetch:false,source_bodies_copied:0,
   created_object_ids:0,ccc_installed:false,dbr_mutated:false},
  ccc_preflight:c,
  request:{mode:'metadata_only',requested_hydration:'minimal',operation:'load.hydrate',
   owner:'Neo',object_id:objectId,capability_id:c.capability_id,
   expected_load_revision:'4c65cbf2d069579ea24ca4f6466901d4530253bb',
   expected_load_registry_blob:'6cb487d8a10827b14284dc63088d908138cc7f80',
   expected_source_registry_blob:'31ab6c546f17d086424a42b7821796bc80128b94',
   max_transfer_bytes:0,network_permission:false,execution_requested:false,
   install_requested:false,publish_requested:false,canonical_mutation_requested:false},
 };
};
const expectLoadHold=(mutate,code)=>{
 const x=loadCase();mutate(x);assert.equal(reviewLoad(x).hold_code,code);
};
test('LOAD source pin and CCC plan produce only a host-handshake proposal',()=>{
 const x=reviewLoad(loadCase());assert.equal(x.state,'HOST_HANDSHAKE_REQUIRED');
 assert.equal(x.target_filespace,'LS.cgx');assert.equal(x.parent_ccc,'Cognigrex.cgx:/ccc');
 for(const k of ['native_admitted','capability_installed','host_authenticated',
  'owner_lease_verified','dbr_readback_verified','hydration_performed',
  'network_fetch','canonical_mutation','source_proof_independently_verified',
  'source_rights_verified'])assert.equal(x[k],false,k);
 assert.equal(x.source_bytes_copied,0);
});
test('LOAD source registry must remain source-only',()=>expectLoadHold(
 x=>{x.source_pin.native_accepted=1;},'LOAD_SOURCE_PROOF_NOT_QUALIFIED'));
test('LOAD source revision must match caller pin',()=>expectLoadHold(
 x=>{x.request.expected_load_revision='f'.repeat(40);},'SOURCE_MAPPING_OR_PIN_MISMATCH'));
test('LOAD registry Git blob must match pinned review blob',()=>expectLoadHold(
 x=>{x.request.expected_load_registry_blob='f'.repeat(40);},'SOURCE_MAPPING_OR_PIN_MISMATCH'));
test('LOAD action mapping source Git blob mismatch is held',()=>expectLoadHold(
 x=>{x.mapping.source_git_blob='f'.repeat(40);},'SOURCE_MAPPING_OR_PIN_MISMATCH'));
test('legacy/other action cannot masquerade as load.hydrate',()=>expectLoadHold(
 x=>{x.mapping.source_key='ccc.install';},'SOURCE_MAPPING_OR_PIN_MISMATCH'));
test('Römer or Eco child cannot be silently substituted for Neo LS',()=>expectLoadHold(
 x=>{x.feature_plan.target.fileSpace='Eco.cgx';},'FEATURE_PLAN_NOT_SOURCE_SAFE'));
test('feature planning cannot install, mutate, publish or execute',()=>{
 for(const k of ['sourceCopied','canonicalMutation','networkFetch','install','execute','publish'])
  expectLoadHold(x=>{x.feature_plan[k]=true;},'FEATURE_PLAN_NOT_SOURCE_SAFE');
});
test('LOAD review forbids full-approved network hydration',()=>expectLoadHold(
 x=>{x.feature_plan.requestedHydration='full-approved';},'FEATURE_PLAN_NOT_SOURCE_SAFE'));
test('LOAD review forbids unaccepted EMBED and PIN composition',()=>{
 for(const mode of ['EMBED','PIN'])
  expectLoadHold(x=>{x.feature_plan.requestedMode=mode;},'FEATURE_PLAN_NOT_SOURCE_SAFE');
});
test('scoped plan cannot claim DBR mutation or installed CCC',()=>{
 for(const k of ['dbr_mutated','ccc_installed'])
  expectLoadHold(x=>{x.scoped_plan[k]=true;},'SCOPED_HYDRATION_PLAN_INVALID');
});
test('CCC ABI/version mismatch is rejected',()=>{
 expectLoadHold(x=>{x.ccc_preflight.candidate_abi='native/999';},'CCC_REVIEW_GATE_INVALID');
 expectLoadHold(x=>{x.ccc_preflight.candidate_version='latest';},'CCC_REVIEW_GATE_INVALID');
});
test('CCC cannot claim verified rights, native admission or authenticated provider readback',()=>{
 for(const k of ['source_rights_verified','native_admitted','provider_readback_authenticated'])
  expectLoadHold(x=>{x.ccc_preflight={...x.ccc_preflight,[k]:true};},'CCC_REVIEW_GATE_INVALID');
});
test('request cannot transfer R0 bytes, execute, install, publish or access network',()=>{
 expectLoadHold(x=>{x.request.max_transfer_bytes=1;},'REQUEST_EXCEEDS_REVIEW_SCOPE');
 for(const k of ['network_permission','execution_requested','install_requested','publish_requested'])
  expectLoadHold(x=>{x.request[k]=true;},'REQUEST_EXCEEDS_REVIEW_SCOPE');
});
test('untrusted matching host claim cannot become authenticated host proof',()=>{
 const x=loadCase();x.host_claim={object_id:x.request.object_id,
  capability_id:x.request.capability_id,load_revision:x.source_pin.revision,
  decision:'CAN_DO',dbr_verified:true};
 const result=reviewLoad(x);assert.equal(result.state,'HOST_HANDSHAKE_REQUIRED');
 assert.equal(result.host_authenticated,false);assert.equal(result.dbr_readback_verified,false);
});
test('mismatched or credential-bearing host claims fail closed without echo',()=>{
 expectLoadHold(x=>{x.host_claim={object_id:'other'};},'UNTRUSTED_OR_MISMATCHED_HOST_CLAIM');
 const x=loadCase();x.host_claim={session_token:'SECRET_FIXTURE'};
 const result=reviewLoad(x);assert.equal(result.hold_code,'SENSITIVE_OR_UNBOUNDED_INPUT');
 assert.equal(JSON.stringify(result).includes('SECRET_FIXTURE'),false);
});
