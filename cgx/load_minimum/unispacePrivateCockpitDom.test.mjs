import test from 'node:test';
import assert from 'node:assert/strict';
import {planUniSpaceSourceInspector} from './unispaceSourceInspector.mjs';
import {renderUniSpacePrivateStatus as render} from './unispacePrivateCockpitDom.mjs';

// Synthetic source and DOM fixtures only; no provider, browser or host receipts.
class FakeElement {
 constructor(tag,doc){this.tagName=tag;this.ownerDocument=doc;this.children=[];this.attributes={};this.textContent='';}
 setAttribute(k,v){this.attributes[k]=v;}
 append(...children){this.children.push(...children);}
 replaceChildren(...children){this.children=[...children];this.textContent='';}
}
const fakeMount=()=>{
 const doc={createElement(tag){return new FakeElement(tag,doc);}};
 return new FakeElement('main',doc);
};
const flatten=node=>node.textContent+node.children.map(flatten).join(' ');
const tags=node=>[node.tagName,...node.children.flatMap(tags)];
const objectId='fixture:eco:one';
const node={object_id:objectId,file_space:'Eco.cgx',domain:'eco',owner:'Eco-Grex',
 kind:'observation',source_refs:['fixture:eco:source'],edges:[]};
const source={source_id:'fixture:eco:source',sha256:'a'.repeat(64),version:'v1',
 owner:'source-owner',rights:'OWNER_PRIVATE',rights_state:'ACTIVE',proof_class:'scientific'};
const inspectInput={nodes:[node],focus_id:objectId,file_space:'Eco.cgx',surface:'private',
 access:{authorized_object_ids:[objectId],authorized_source_ids:['fixture:eco:source']},
 source_envelopes:[source]};
const selection={object_id:objectId,file_space:'Eco.cgx',parent_file_space:'Cognigrex.cgx',domain:'eco'};
const input={surface:'private',selection,inspector:planUniSpaceSourceInspector(inspectInput)};

test('one private source-review DOM status has accessible labels and no active controls',()=>{
 const mount=fakeMount();
 const x=render({...input,mount});
 assert.equal(x.status,'RENDERED_SOURCE_REVIEW');
 assert.equal(x.presentation_stage,'R3_VIEW_PROPOSAL');
 assert.equal(x.host_authenticated,false);
 assert.equal(x.rendered_live,false);
 assert.equal(x.public_release,false);
 const section=mount.children[0];
 assert.equal(section.attributes.role,'status');
 assert.equal(section.attributes['aria-live'],'polite');
 assert.equal(section.attributes['data-cgx-authority'],'SOURCE_REVIEW_ONLY');
 const text=flatten(mount);
 assert.match(text,/UniSpace — private source review only/);
 assert.match(text,/fixture:eco:one/);
 assert.match(text,/Evidence ceiling R3_PRESENTATION_ONLY_NO_SCIENTIFIC_OR_METRIC_AUTHORITY/);
 assert.match(text,/Source rights NOT_PROVIDER_VERIFIED/);
 assert.match(text,/Root authority NOT_NATIVE_VERIFIED/);
 assert.match(text,/Cross-platform sync NOT_VERIFIED/);
 assert.match(text,/ADMITTED — HOLD/);
 assert.match(text,/LIVE_VERIFIED — HOLD/);
 assert.match(text,/No host command/);
 assert.ok(!text.includes(source.source_id));
 assert.ok(!text.includes(source.sha256));
 assert.ok(!tags(mount).some(t=>['button','a','input','script','iframe'].includes(t)));
});

test('H0–H4 and all six viewport intents render as inert accessible review metadata',()=>{
 const mount=fakeMount();
 const x=render({...input,mount});
 assert.equal(x.status,'RENDERED_SOURCE_REVIEW');
 const txt=flatten(mount);
 for(const layer of ['H0 Identity','H1 Semantic edges','H2 Source and provenance',
                     'H3 Qualified capabilities','H4 Permissioned execution'])
  assert.ok(txt.includes(layer),layer);
 for(const view of ['document','3d','chat','graph','interactive','matrix'])
  assert.match(txt,new RegExp(view+' — '));
 assert.match(txt,/document — REVIEW_REQUEST_ONLY — selected/);
 assert.match(txt,/3d — METRIC_GEOMETRY_FRONTIER/);
 assert.match(txt,/Denied — signed root, ACL, lease and DBR not verified/);
 assert.ok(!txt.includes(source.source_id));
 assert.ok(!txt.includes(source.sha256));
 assert.ok(!tags(mount).some(t=>['button','a','input','script','iframe'].includes(t)));
 const offlineMount=fakeMount();
 const offline=planUniSpaceSourceInspector({...inspectInput,offline:true});
 const y=render({...input,mount:offlineMount,inspector:offline,offline:true});
 assert.equal(y.status,'RENDERED_SOURCE_REVIEW');
 assert.match(flatten(offlineMount),/H0 metadata only/);
 assert.match(flatten(offlineMount),/3d — OFFLINE_UNAVAILABLE/);
 assert.ok(!flatten(offlineMount).includes(' — selected'));
 assert.equal(y.may_execute,false);
});

test('#158 public route transition erases stale private DOM without disclosing identity',()=>{
 const mount=fakeMount();
 assert.equal(render({...input,mount}).status,'RENDERED_SOURCE_REVIEW');
 const denied=render({...input,mount,surface:'public'});
 assert.equal(denied.status,'DENIED');
 assert.equal(denied.reason,'PRIVATE_OPERATOR_SURFACE_REQUIRED');
 assert.equal(flatten(mount),'');
 assert.equal(mount.children.length,0);
});

test('#158 invalid document boundary clears stale private identity before denial',()=>{
 const mount=fakeMount();
 assert.equal(render({...input,mount}).status,'RENDERED_SOURCE_REVIEW');
 assert.match(flatten(mount),/fixture:eco:one/);
 // Simulates a re-bound or invalidated host document during a route change.
 // The existing private DOM must be erased even though a new view cannot mount.
 mount.ownerDocument=null;
 const result=render({...input,mount,surface:'public'});
 assert.equal(result.status,'DENIED');
 assert.equal(result.reason,'INVALID_MOUNT');
 assert.equal(flatten(mount),'');
 assert.equal(mount.children.length,0);
 assert.equal(result.host_authenticated,false);
 assert.equal(result.public_release,false);
});

test('claimed signed host receipt never becomes a badge or is serialized',()=>{
 const mount=fakeMount();
 const secret='DO_NOT_ECHO_SESSION_SECRET';
 const x=render({...input,mount,hostReceipt:{signed:true,session:secret,verified:true}});
 assert.equal(x.status,'RENDERED_SOURCE_REVIEW');
 assert.equal(x.host_authenticated,false);
 assert.ok(!flatten(mount).includes(secret));
 assert.match(flatten(mount),/Host authentication NOT_AUTHENTICATED/);
});

test('offline mode renders H0 metadata only and retains non-live proof gates',()=>{
 const mount=fakeMount();
 const offline=planUniSpaceSourceInspector({...inspectInput,offline:true});
 const x=render({...input,mount,inspector:offline,offline:true});
 assert.equal(x.status,'RENDERED_SOURCE_REVIEW');
 assert.equal(x.presentation_stage,'H0_OFFLINE_UNVERIFIED');
 assert.match(flatten(mount),/Evidence ceiling H0_IDENTITY_METADATA_UNVERIFIED/);
 assert.match(flatten(mount),/metadata-only/);
 assert.ok(!flatten(mount).includes(source.source_id));
 assert.equal(x.may_execute,false);
});

test('untrusted Object_ID text cannot create DOM nodes or event handlers',()=>{
 const injection='fixture:eco:<img src=x onerror=alert(1)>';
 const n={...node,object_id:injection};
 const inspector=planUniSpaceSourceInspector({...inspectInput,nodes:[n],focus_id:injection,
  access:{authorized_object_ids:[injection],authorized_source_ids:[source.source_id]}});
 const mount=fakeMount();
 const x=render({...input,mount,selection:{...selection,object_id:injection},inspector});
 assert.equal(x.status,'RENDERED_SOURCE_REVIEW');
 assert.ok(flatten(mount).includes(injection));
 assert.ok(!tags(mount).includes('img'));
 assert.ok(!tags(mount).includes('script'));
});

test('invalid mount and forged authority plan fail closed without rendering',()=>{
 assert.equal(render({...input,mount:{}}).reason,'INVALID_MOUNT');
 const mount=fakeMount();
 const forged={...input.inspector,host_authenticated:true};
 const x=render({...input,mount,inspector:forged});
 assert.equal(x.status,'DENIED');
 assert.equal(x.reason,'UNTRUSTED_ELEVATED_REVIEW_PLAN');
 assert.equal(flatten(mount),'');
});

test('rights revocation after an R3 review render clears stale status before R2 Frontier',()=>{
 const mount=fakeMount();
 const initial=render({...input,mount});
 assert.equal(initial.status,'RENDERED_SOURCE_REVIEW');
 assert.equal(initial.presentation_stage,'R3_VIEW_PROPOSAL');
 assert.match(flatten(mount),/R3_VIEW_PROPOSAL/);
 // A fresh caller-declared rights veto must downgrade presentation even
 // when an earlier private projection occupied the same DOM mount.
 const revoked=planUniSpaceSourceInspector({
  ...inspectInput,source_envelopes:[{...source,rights_state:'REVOKED'}]
 });
 assert.equal(revoked.viewport.state,'FRONTIER');
 const downgraded=render({...input,mount,inspector:revoked});
 assert.equal(downgraded.status,'RENDERED_SOURCE_REVIEW');
 assert.equal(downgraded.presentation_stage,'R2_REVIEW_FRONTIER');
 assert.match(flatten(mount),/Evidence ceiling R2_FRONTIER_NO_QUALIFIED_VIEW/);
 const visible=flatten(mount);
 assert.match(visible,/R2_REVIEW_FRONTIER/);
 assert.ok(!visible.includes('R3_VIEW_PROPOSAL'));
 assert.ok(!visible.includes(source.source_id));
 assert.ok(!visible.includes(source.sha256));
 assert.ok(!tags(mount).some(t=>['button','a','input','script','iframe'].includes(t)));
 assert.equal(downgraded.host_authenticated,false);
 assert.equal(downgraded.public_release,false);
 // A subsequent unauthorised route must erase the remaining H0 projection.
 const denied=render({...input,mount,inspector:revoked,surface:'public'});
 assert.equal(denied.status,'DENIED');
 assert.equal(flatten(mount),'');
});


// Source-only DOM regression: changing a selection to another Grex or an
// incorrect parent must erase the previous private status, not leave stale H0.
test('#158 cross-Grex or wrong-parent selection clears stale private status before denial',()=>{
 for(const invalid of [
  {...selection,domain:'romer'},
  {...selection,parent_file_space:'Romer.cgx'},
  {...selection,file_space:'Romer.cgx'}
 ]){
  const mount=fakeMount();
  assert.equal(render({...input,mount}).status,'RENDERED_SOURCE_REVIEW');
  assert.match(flatten(mount),/fixture:eco:one/);
  const result=render({...input,mount,selection:invalid});
  assert.equal(result.status,'DENIED');
  assert.equal(result.reason,'EXACT_CHILD_IDENTITY_REQUIRED');
  assert.equal(flatten(mount),'');
  assert.equal(mount.children.length,0);
  assert.equal(result.host_authenticated,false);
  assert.equal(result.public_release,false);
  assert.equal(result.may_execute,false);
  assert.ok(!JSON.stringify(result).includes(source.source_id));
 }
});


// Synthetic same-child identity switch: a stale inspector is not an authority
// token, and a new caller-declared ACL is never proof of a host session.
test('#158 same-child Object_ID switch clears stale private review before scope rebind',()=>{
 const mount=fakeMount();
 assert.equal(render({...input,mount}).status,'RENDERED_SOURCE_REVIEW');
 assert.match(flatten(mount),/fixture:eco:one/);
 const secondId='fixture:eco:two';
 const secondSource={...source,source_id:'fixture:eco:second-source'};
 const secondNode={...node,object_id:secondId,source_refs:[secondSource.source_id]};
 const secondSelection={...selection,object_id:secondId};
 const stale=render({...input,mount,selection:secondSelection});
 assert.equal(stale.status,'DENIED');
 assert.equal(stale.reason,'INSPECTOR_SELECTION_OR_SCHEMA_MISMATCH');
 assert.equal(flatten(mount),'');
 const secondInspector=planUniSpaceSourceInspector({
  ...inspectInput,nodes:[secondNode],focus_id:secondId,
  access:{authorized_object_ids:[secondId],authorized_source_ids:[secondSource.source_id]},
  source_envelopes:[secondSource]
 });
 assert.equal(secondInspector.status,'SOURCE_REVIEW_ONLY');
 const rebound=render({...input,mount,selection:secondSelection,inspector:secondInspector});
 assert.equal(rebound.status,'RENDERED_SOURCE_REVIEW');
 assert.match(flatten(mount),/fixture:eco:two/);
 assert.ok(!flatten(mount).includes('fixture:eco:one'));
 assert.ok(!flatten(mount).includes(secondSource.source_id));
 assert.equal(rebound.host_authenticated,false);
 assert.equal(rebound.may_execute,false);
 const revokedScope=planUniSpaceSourceInspector({
  ...inspectInput,nodes:[secondNode],focus_id:secondId,
  access:{authorized_object_ids:[],authorized_source_ids:[]},
  source_envelopes:[secondSource]
 });
 assert.equal(revokedScope.status,'DENIED');
 const denied=render({...input,mount,selection:secondSelection,inspector:revokedScope});
 assert.equal(denied.status,'DENIED');
 assert.equal(flatten(mount),'');
 assert.equal(mount.children.length,0);
 assert.equal(denied.public_release,false);
 assert.ok(!JSON.stringify(denied).includes(secondSource.source_id));
});


// NOV-01: one source-only route contract, not a second UI or runtime.
test('existing public CGX facets remain synthetic and never receive a private Object_ID',async()=>{
 const {planUniSpaceFacetConvergence:plan}=await import('./unispaceFacetConvergence.mjs');
 const expected={
  '/cgx':'PUBLIC_SAFE_SYNTHETIC',
  '/cgx/fs':'PUBLIC_SAFE_SYNTHETIC',
  '/cgx/ds':'SIMULATED_NOT_AUTHENTICATED',
  '/cgx/ps':'NUMERIC_DEMO_NOT_PHYSICAL',
  '/cgx/doom':'CREATIVE_REFERENCE_NOT_GAME_ENGINE',
  '/cgx/romer':'PUBLIC_SAFE_SYNTHETIC',
  '/cgx/eco':'PUBLIC_SAFE_SYNTHETIC'
 };
 for(const [route,proof] of Object.entries(expected)){
  const p=plan({surface:'public',route});
  assert.equal(p.status,'SOURCE_REVIEW_ONLY',route);
  assert.equal(p.evidence_ceiling,proof,route);
  assert.deepEqual(p.source_prs,[174,188]);
  assert.equal(p.selected_object_id,null);
  assert.equal(p.selected_file_space,null);
  assert.equal(p.may_execute,false);
  assert.equal(p.deployed,false);
  assert.equal(p.public_release,false);
  assert.ok(!JSON.stringify(p).includes(objectId));
  assert.ok(!JSON.stringify(p).includes(source.source_id));
 }
});

test('#158 public-static facet cannot accept private inspector, host token or ambiguous route',async()=>{
 const {planUniSpaceFacetConvergence:plan}=await import('./unispaceFacetConvergence.mjs');
 for(const patch of [
  {selection},{inspector:input.inspector},{hostReceipt:{session:'PRIVATE_SESSION'}},
  {offline:true}
 ]){
  const p=plan({surface:'public',route:'/cgx/fs',...patch});
  assert.equal(p.status,'DENIED');
  assert.equal(p.reason,'PUBLIC_ROUTE_PRIVATE_CONTEXT_FORBIDDEN');
  assert.ok(!JSON.stringify(p).includes(objectId));
  assert.ok(!JSON.stringify(p).includes('PRIVATE_SESSION'));
 }
 for(const route of ['/operator/objects','/cgx/private','/cgx/../review',
                     '/cgx/%2e%2e/review','/cgx/fs?source=private','/cgx/fs/']){
  assert.equal(plan({surface:'public',route}).status,'DENIED',route);
 }
});

test('private Objects facet delegates exact child identity and never upgrades source review',async()=>{
 const {planUniSpaceFacetConvergence:plan}=await import('./unispaceFacetConvergence.mjs');
 const receipt={verified:true,signed:true,session:'DO_NOT_EXPOSE_PRIVATE_TOKEN'};
 const p=plan({surface:'private',route:'/operator/objects',
  selection,inspector:input.inspector,hostReceipt:receipt});
 assert.equal(p.status,'SOURCE_REVIEW_ONLY');
 assert.equal(p.selected_object_id,objectId);
 assert.equal(p.selected_file_space,'Eco.cgx');
 assert.equal(p.presentation_stage,'R3_VIEW_PROPOSAL');
 assert.deepEqual(p.source_prs,[192,205]);
 assert.equal(p.host_authenticated,false);
 assert.equal(p.native_admitted,false);
 assert.equal(p.deployed,false);
 assert.equal(p.may_execute,false);
 assert.ok(!JSON.stringify(p).includes(source.source_id));
 assert.ok(!JSON.stringify(p).includes(receipt.session));
 const cross=plan({surface:'private',route:'/operator/objects',
  selection:{...selection,file_space:'Romer.cgx'},inspector:input.inspector});
 assert.equal(cross.status,'DENIED');
 assert.equal(cross.reason,'EXACT_CHILD_IDENTITY_REQUIRED');
 const offlineInspector=planUniSpaceSourceInspector({...inspectInput,offline:true});
 const fallback=plan({surface:'private',route:'/operator/objects',
  selection,inspector:offlineInspector,offline:true});
 assert.equal(fallback.status,'SOURCE_REVIEW_ONLY');
 assert.equal(fallback.presentation_stage,'H0_OFFLINE_UNVERIFIED');
 assert.equal(fallback.may_execute,false);
});


const heldOwnerReview={
 object_id:objectId,file_space:'Eco.cgx',
 bridge_status:'BRIDGE_REACHABLE',consumer_status:'CONSUMER_HELD',
 r1_status:'PRIVATE_R1_CANDIDATE',r2_status:'R2_DISCOVERY_ONLY',
 // Untrusted private material must never be projected into a DOM or response.
 raw_chat:'PRIVATE_CONVERSATION_MUST_NOT_RENDER',
 token_url:'PRIVATE_LOCALHOST_TOKEN_MUST_NOT_RENDER',
 command_history:'PRIVATE_REMOTE_COMMAND_MUST_NOT_RENDER',
 source_hash:'PRIVATE_SHA_MUST_NOT_RENDER'
};

test('Achilles source-review owner progress separates bridge reachability from held Smith consumer',()=>{
 const mount=fakeMount();
 const result=render({...input,mount,ownerReview:heldOwnerReview});
 assert.equal(result.status,'RENDERED_SOURCE_REVIEW');
 const txt=flatten(mount);
 assert.match(txt,/Bridge report BRIDGE_REACHABLE — caller reported; current authentication unverified/);
 assert.match(txt,/Smith consumer report CONSUMER_HELD — no execution readiness inferred/);
 assert.match(txt,/R1 FileSpace evidence PRIVATE_R1_CANDIDATE — not native admitted/);
 assert.match(txt,/R2 relation evidence R2_DISCOVERY_ONLY — not independently accepted/);
 assert.match(txt,/CALLER_REPORTED_NOT_PROVIDER_READBACK/);
 assert.match(txt,/Host authentication NOT_AUTHENTICATED/);
 assert.match(txt,/Live deployment HOLD — not verified/);
 for(const privateValue of ['PRIVATE_CONVERSATION_MUST_NOT_RENDER','PRIVATE_LOCALHOST_TOKEN_MUST_NOT_RENDER',
   'PRIVATE_REMOTE_COMMAND_MUST_NOT_RENDER','PRIVATE_SHA_MUST_NOT_RENDER'])
  assert.ok(!txt.includes(privateValue));
 assert.ok(!tags(mount).some(t=>['button','a','input','script','iframe'].includes(t)));
 assert.equal(result.may_execute,false);
 assert.equal(result.host_authenticated,false);
 assert.equal(result.public_release,false);
});

test('owner progress cannot claim execute-ready or cross-child identity and clears stale private status',()=>{
 const invalid=[
  {...heldOwnerReview,consumer_status:'CONSUMER_READY'},
  {...heldOwnerReview,bridge_status:'AUTHENTICATED'},
  {...heldOwnerReview,r1_status:'NATIVE_ADMITTED'},
  {...heldOwnerReview,r2_status:'R2_ACCEPTED'},
  {...heldOwnerReview,object_id:'fixture:romer:private'},
  {...heldOwnerReview,file_space:'Romer.cgx'}
 ];
 for(const ownerReview of invalid){
  const mount=fakeMount();
  assert.equal(render({...input,mount,ownerReview:heldOwnerReview}).status,'RENDERED_SOURCE_REVIEW');
  const denied=render({...input,mount,ownerReview});
  assert.equal(denied.status,'DENIED');
  assert.equal(denied.reason,'OWNER_REVIEW_SCOPE_OR_STATUS_INVALID');
  assert.equal(flatten(mount),'');
  assert.equal(denied.may_execute,false);
  assert.equal(denied.host_authenticated,false);
 }
});

test('offline and public surfaces cannot replay a historical owner progress report',()=>{
 const offline=planUniSpaceSourceInspector({...inspectInput,offline:true});
 const mount=fakeMount();
 const denied=render({...input,mount,offline:true,inspector:offline,ownerReview:heldOwnerReview});
 assert.equal(denied.status,'DENIED');
 assert.equal(denied.reason,'OFFLINE_OWNER_REVIEW_UNAVAILABLE');
 assert.equal(flatten(mount),'');
 const publicMount=fakeMount();
 const publicResult=render({...input,mount:publicMount,surface:'public',ownerReview:heldOwnerReview});
 assert.equal(publicResult.status,'DENIED');
 assert.equal(flatten(publicMount),'');
 const offlineH0=render({...input,mount,offline:true,inspector:offline});
 assert.equal(offlineH0.status,'RENDERED_SOURCE_REVIEW');
 assert.ok(!flatten(mount).includes('BRIDGE_REACHABLE'));
});
