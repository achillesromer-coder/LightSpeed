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
 assert.match(text,/ADMITTED — HOLD/);
 assert.match(text,/LIVE_VERIFIED — HOLD/);
 assert.match(text,/No host command/);
 assert.ok(!text.includes(source.source_id));
 assert.ok(!text.includes(source.sha256));
 assert.ok(!tags(mount).some(t=>['button','a','input','script','iframe'].includes(t)));
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
