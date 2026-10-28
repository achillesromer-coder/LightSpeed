import { test } from 'vitest';
import assert from 'node:assert/strict';
import {planUniSpaceLoadCommandSurface as plan} from './cgxUniSpaceLoadCommandSurface.mjs';
function fixture(){
 const id='fixture:romer:watchtower',filespace='Romer.cgx';
 return {
  context_plan:{schema:'UNISPACE-CGX-HOST-CONTEXT-GATE/0.1',state:'PLAN_ONLY_NOT_HYDRATED',object_id:id,filespace,requested_layer:'R0',native_admitted:false,host_context_readback_authenticated:false,private_hydration_authorized:false,public_publish_authorized:false,canonical_mutation:false,execution_performed:false},
  handoff_plan:{schema:'UNISPACE-CGX-SMART-SETUP-HANDOFF/0.1',state:'SOURCE_REVIEW_ONLY',parent_filespace:'Cognigrex.cgx',candidate_object_id:id,filespace,selected_view:'document',selected_hydration:'H2',evidence_class:'scientific',inventory:{load:'ALIAS_REFERENCE_ONLY_NOT_ACTIVATED',ccc_installed:'UNVERIFIED',runtime_installed:'UNVERIFIED'},native_admitted:false,host_authenticated:false,installed:false,network_fetch:false,canonical_mutation:false,execution_performed:false,public_release:false},
  client_permissions:{mode:'review_only',revoked:false,allowed_object_ids:[id],allowed_filespaces:[filespace]}
 };
}
test('one candidate and child FileSpace, no new parent',()=>{const a=plan(fixture());assert.equal(a.state,'SOURCE_REVIEW_ONLY');assert.equal(a.candidate_object_id,'fixture:romer:watchtower');assert.equal(a.filespace,'Romer.cgx');assert.equal(a.parent_filespace,'Cognigrex.cgx');assert.equal(a.alias,'LOAD.cgx')});
test('object context menu contains only scoped review commands',()=>{const a=plan(fixture());assert.equal(a.actions.length,6);assert.ok(a.actions.every(x=>!x.enabled&&!x.callback_bound&&x.mode==='HOST_PREFLIGHT_REQUIRED'))});
test('FileSpace menu includes LOAD equip and CCC discovery preflight',()=>{const x=fixture();x.target_kind='filespace';const a=plan(x);assert.equal(a.actions.length,9);assert.ok(a.actions.some(y=>y.id==='load.attach'));assert.ok(a.actions.some(y=>y.id==='ccc.discover'))});
test('long press has accessible labels and no callback',()=>{const x=fixture();x.surface='long-press';const a=plan(x);assert.equal(a.invocation_surface,'long-press');assert.equal(a.accessibility.mobile_long_press,true);assert.ok(a.actions.every(y=>y.keyboard_accessible))});
test('command palette is a descriptor, not executable',()=>{const x=fixture();x.surface='command-palette';const a=plan(x);assert.equal(a.actions.length,6);assert.equal(a.execution_performed,false)});
test('CCC launcher lists only CCC actions',()=>{const x=fixture();x.surface='ccc-launch';const a=plan(x);assert.deepEqual(a.actions.map(y=>y.id),['ccc.discover'])});
test('H0-H4 status explicitly separates execution',()=>{const a=plan(fixture());assert.equal(a.levels.H0,'CANDIDATE_IDENTITY_ONLY');assert.match(a.levels.H4,/DENIED/);assert.equal(a.host_authenticated,false)});
test('offline H0 FileSpace view restricts commands',()=>{const x=fixture();x.target_kind='filespace';x.offline=true;x.handoff_plan.selected_hydration='H0_OFFLINE_METADATA_ONLY';const a=plan(x);assert.deepEqual(a.actions.map(y=>y.id),['alexandria.open']);assert.equal(a.hydration,'H0_OFFLINE_METADATA_ONLY')});
test('offline with higher hydration rejected',()=>{const x=fixture();x.offline=true;assert.equal(plan(x).state,'HOLD')});
test('online cannot masquerade as offline cache',()=>{const x=fixture();x.handoff_plan.selected_hydration='H0_OFFLINE_METADATA_ONLY';assert.equal(plan(x).state,'HOLD')});
test('revoked client scope denied',()=>{const x=fixture();x.client_permissions.revoked=true;assert.equal(plan(x).hold_code,'EXACT_CLIENT_SCOPE_REQUIRED')});
test('different Object_ID denied',()=>{const x=fixture();x.handoff_plan.candidate_object_id='fixture:eco:tree';assert.equal(plan(x).state,'HOLD')});
test('domain-only ID denied',()=>{const x=fixture();x.context_plan.object_id='cgx:domain:romer';assert.equal(plan(x).state,'HOLD')});
test('cross-child FileSpace substitution denied',()=>{const x=fixture();x.handoff_plan.filespace='Eco.cgx';assert.equal(plan(x).state,'HOLD')});
test('fabricated native admission denied',()=>{const x=fixture();x.context_plan.native_admitted=true;assert.equal(plan(x).state,'HOLD')});
test('fabricated installed capability denied',()=>{const x=fixture();x.handoff_plan.installed=true;assert.equal(plan(x).state,'HOLD')});
test('source locator never echoed',()=>{const x=fixture();x.handoff_plan.source_locator='PRIVATE-TEST-MARKER';const a=plan(x);assert.equal(a.state,'HOLD');assert.ok(!JSON.stringify(a).includes('PRIVATE-TEST-MARKER'))});
test('credentials never echoed',()=>{const x=fixture();x.client_permissions.token='PRIVATE-TEST-MARKER';const a=plan(x);assert.equal(a.state,'HOLD');assert.ok(!JSON.stringify(a).includes('PRIVATE-TEST-MARKER'))});
test('unsupported target or action rejected',()=>{const x=fixture();x.target_kind='file';assert.equal(plan(x).state,'HOLD');const y=fixture();y.requested_action='run.now';assert.equal(plan(y).state,'HOLD')});
test('wrong action for context rejected',()=>{const x=fixture();x.requested_action='load.attach';assert.equal(plan(x).state,'HOLD');const y=fixture();y.surface='ccc-launch';y.requested_action='load.switch_view';assert.equal(plan(y).state,'HOLD')});
test('3d geometry remains Frontier, not fake render',()=>{const x=fixture();x.handoff_plan.selected_view='3d';assert.match(plan(x).geometry,/FRONTIER/)});
test('both security gates and zero transfer retained',()=>{const a=plan(fixture());assert.ok(a.holds.some(x=>x.includes('158')));assert.ok(a.holds.some(x=>x.includes('161')));assert.equal(a.source_bytes_transferred,0);assert.equal(a.public_release,false);assert.equal(a.network_fetch,false);assert.equal(a.asset_urls_returned,false)});
test('reject circular and deeply nested private input',()=>{const x=fixture();x.loop=x;assert.equal(plan(x).state,'HOLD')});
