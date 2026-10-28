import test from 'node:test';
import assert from 'node:assert/strict';
import {planUniSpaceSmartSetupHandoff as plan} from './cgxUniSpaceSmartSetupHandoffPlan.mjs';
function fixture({mode='first-run',offline=false,action='smart_setup.open'}={}){
 const id='fixture:romer:watchtower',filespace='Romer.cgx';
 return {requested_action:action,offline,
 context_plan:{schema:'UNISPACE-CGX-HOST-CONTEXT-GATE/0.1',state:'PLAN_ONLY_NOT_HYDRATED',object_id:id,filespace,requested_layer:'R0',native_admitted:false,host_context_readback_authenticated:false,private_hydration_authorized:false,public_publish_authorized:false,canonical_mutation:false,execution_performed:false},
 inspector_plan:{schema:'UNISPACE-LOAD-VIEWPORT-INSPECTOR-PLAN/0.1',state:'SOURCE_REVIEW_ONLY',object_id:id,filespace,parent_filespace:'Cognigrex.cgx',alias:'LOAD.cgx',evidence_class:'scientific',view:'document',hydration:offline?'H0_OFFLINE_METADATA_ONLY':'H2',native_admitted:false,host_authenticated:false,rendered:false,network_fetch:false,canonical_mutation:false,public_release:false,execution_performed:false},
 setup_plan:{schema:'CGX-UNIFIED-BOOTSTRAP-PLAN/0.1',state:'REVIEW_ONLY',family:filespace,mode,device:'browser',offline_minimum:true,canonical_accepted:false,runtime_installed:false,source_ingested:false,independent_host_acceptance:false,published:false,website_deployed:false,library:{name:'LOAD.cgx',bind:'EXISTING_IDENTITY_ONLY',install:false,network_hydration:false},ls_go:{product:'Grex-scoped LS GO',separate_product:'UniSpace',enabled:false,actual_toggle_write:false},steps:Array.from({length:11},(_,j)=>({id:String(j),canonical_mutation:false,auto_run:false}))},
 client_permissions:{mode:'review_only',revoked:false,allowed_object_ids:[id],allowed_filespaces:[filespace]}
 };
}
const state=x=>plan(x).state;
test('one exact candidate and correct child retained, never admitted',()=>{const a=plan(fixture());assert.equal(a.state,'SOURCE_REVIEW_ONLY');assert.equal(a.candidate_object_id,'fixture:romer:watchtower');assert.equal(a.filespace,'Romer.cgx');assert.equal(a.native_admitted,false)});
test('LOAD remains alias, not parent',()=>{const a=plan(fixture());assert.equal(a.parent_filespace,'Cognigrex.cgx');assert.equal(a.inventory.load,'ALIAS_REFERENCE_ONLY_NOT_ACTIVATED')});
test('no installed or release claims',()=>{const a=plan(fixture());assert.equal(a.installed,false);assert.equal(a.public_release,false);assert.equal(a.products.grex_ls_go,'PRIVATE_OPERATOR_OFF_UNVERIFIED')});
test('CCC and runtime are unverified, not installed',()=>{const a=plan(fixture());assert.equal(a.inventory.ccc_installed,'UNVERIFIED');assert.equal(a.inventory.runtime_installed,'UNVERIFIED')});
test('offline only H0 and zero transfer',()=>{const a=plan(fixture({offline:true}));assert.equal(a.selected_hydration,'H0_OFFLINE_METADATA_ONLY');assert.equal(a.source_bytes_transferred,0)});
test('offline H2 rejected',()=>{const x=fixture({offline:true});x.inspector_plan.hydration='H2';assert.equal(state(x),'HOLD')});
test('online flag cannot bypass offline inspector',()=>{const x=fixture();x.inspector_plan.hydration='H0_OFFLINE_METADATA_ONLY';assert.equal(state(x),'HOLD')});
test('revoked client scope rejected',()=>{const x=fixture();x.client_permissions.revoked=true;assert.equal(plan(x).reason,'CLIENT_SCOPE_DENIED')});
test('cross-Grex family substitution rejected',()=>{const x=fixture();x.setup_plan.family='Eco.cgx';assert.equal(plan(x).reason,'UNTRUSTED_SETUP_PLAN_OR_CROSS_PRODUCT_MISMATCH')});
test('domain-only Object_ID rejected',()=>{const x=fixture();x.context_plan.object_id='cgx:domain:romer';assert.equal(state(x),'HOLD')});
test('Object_ID mismatch rejected',()=>{const x=fixture();x.inspector_plan.object_id='fixture:eco:tree';assert.equal(state(x),'HOLD')});
test('fake host admission rejected',()=>{const x=fixture();x.context_plan.native_admitted=true;assert.equal(state(x),'HOLD')});
test('fake installation rejected',()=>{const x=fixture();x.setup_plan.runtime_installed=true;assert.equal(state(x),'HOLD')});
test('fake LS GO toggle rejected',()=>{const x=fixture();x.setup_plan.ls_go.enabled=true;assert.equal(state(x),'HOLD')});
test('private source locator rejected without reflection',()=>{const x=fixture();x.inspector_plan.source_locator='C:/secret/LOAD';const a=plan(x);assert.equal(a.state,'HOLD');assert.equal(JSON.stringify(a).includes('C:/secret'),false)});
test('embedded credentials rejected without reflection',()=>{const x=fixture();x.setup_plan.token='PRIVATEKEY';const a=plan(x);assert.equal(a.state,'HOLD');assert.equal(JSON.stringify(a).includes('PRIVATEKEY'),false)});
test('resume action requires resume mode',()=>{const x=fixture({action:'smart_setup.resume'});assert.equal(plan(x).reason,'ACTION_MODE_MISMATCH')});
test('resume/repair/upgrade modes are read-only',()=>{for(const [action,mode] of [['smart_setup.resume','resume'],['smart_setup.repair','repair'],['smart_setup.upgrade','upgrade']]){const a=plan(fixture({action,mode}));assert.equal(a.state,'SOURCE_REVIEW_ONLY');assert.equal(a.installed,false);assert.equal(a.canonical_mutation,false)}});
test('unsupported execution action denied',()=>{const x=fixture();x.requested_action='install.now';assert.equal(state(x),'HOLD')});
test('notices retain both security holds',()=>{const a=plan(fixture());assert.equal(a.notices.some(x=>x.includes('ISSUE_158')),true);assert.equal(a.notices.some(x=>x.includes('ISSUE_161')),true)});
test('viewport replan remains explicit',()=>{const x=fixture();x.inspector_plan.state='REPLAN_REQUIRED';assert.equal(plan(x).notices.includes('VIEWPORT_CONTROLS_REPLAN_REQUIRED'),true)});
test('no network or execution from menu descriptors',()=>{const a=plan(fixture());assert.equal(a.network_fetch,false);assert.equal(a.execution_performed,false);assert.equal(a.actions.every(x=>x.enabled===false),true)});
