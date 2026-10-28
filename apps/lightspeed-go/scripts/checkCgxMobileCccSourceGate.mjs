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
