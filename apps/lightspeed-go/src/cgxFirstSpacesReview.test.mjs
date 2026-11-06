import {test} from 'vitest';
import assert from 'node:assert/strict';
import {mountFirstSpacesReview} from './cgxFirstSpacesReview.mjs';
import {planFirstSpacesReview} from './cgxFirstSpacesReviewModel.mjs';

class Element{
 constructor(tag,doc){this.tagName=tag;this.ownerDocument=doc;this.children=[];this.attrs={};
  this.handlers={};this.textContent='';this.className='';}
 setAttribute(k,v){this.attrs[k]=String(v);}
 getAttribute(k){return Object.hasOwn(this.attrs,k)?this.attrs[k]:null;}
 append(...nodes){this.children.push(...nodes);}
 replaceChildren(...nodes){this.children=[...nodes];this.textContent='';}
 contains(x){return x===this||this.children.some(e=>e.contains(x));}
 addEventListener(k,fn){this.handlers[k]=fn;}
 removeEventListener(k,fn){if(this.handlers[k]===fn)delete this.handlers[k];}
 closest(sel){return sel==='button'&&this.tagName==='button'?this:null;}
}
const doc={createElement(tag){return new Element(tag,doc);}};
const mount=()=>new Element('main',doc);
const all=root=>[root,...root.children.flatMap(all)];
const find=(root,k,v)=>all(root).find(el=>el.getAttribute(k)===v);
const text=root=>all(root).map(x=>x.textContent).join(' ');
const click=(root,button)=>root.handlers.click({target:button});
const selectOrder=root=>all(root).filter(x=>x.getAttribute('data-cgx-select')!==null)
 .map(x=>x.getAttribute('data-cgx-select'));

test('initial lattice is one parent, one LOAD and provenance-held first spaces',()=>{
 const model=planFirstSpacesReview();
 assert.equal(model.state,'SOURCE_REVIEW_ONLY');
 assert.equal(model.nodes.length,11);
 assert.equal(model.nodes.filter(x=>x.kind==='canonical-parent').length,1);
 assert.equal(model.nodes.filter(x=>x.key==='facet.load').length,1);
 assert.equal(model.parent_identity_status,'SOURCE_DESIGN_NOT_NATIVE_ROOT');
 assert.equal(model.native_minted,false);
 assert.equal(model.may_sign,false);
 assert.equal(model.may_deploy,false);
 assert.equal(model.may_publish,false);
 for(const n of model.nodes){assert.equal(n.source_rights,'UNVERIFIED');assert.equal(n.candidate_object_id,null);}
});
test('GUI rearrangement and view switching are live but do not change press sequence',()=>{
 const root=mount();
 const handler=mountFirstSpacesReview(root);
 assert.equal(handler.state,'SOURCE_REVIEW_ONLY');
 assert.match(text(root),/CGX first-spaces lattice/);
 assert.match(text(root),/Mint, signing and deployment are held/);
 const order=selectOrder(root);
 click(root,find(root,'data-cgx-layout','space-grid'));
 assert.equal(find(root,'data-cgx-layout','space-grid').getAttribute('aria-pressed'),'true');
 click(root,all(root).find(x=>x.getAttribute('data-cgx-move')==='facet.load'&&x.getAttribute('data-cgx-step')==='1'));
 const after=selectOrder(root);
 assert.notDeepEqual(after,order);
 assert.deepEqual([...after].sort(),[...order].sort());
 assert.deepEqual(planFirstSpacesReview({order:after}).mint_sequence,planFirstSpacesReview().mint_sequence);
 click(root,find(root,'data-cgx-select','family.eco'));
 assert.match(text(root),/Parent: family.cognigrex/);
 click(root,find(root,'data-cgx-design','approve'));
 assert.match(text(root),/DESIGN_APPROVED_ONLY/);
 assert.match(text(root),/No authority, signed approval or native mint is created/);
 handler.dispose();
 assert.equal(root.handlers.click,undefined);
});
test('invalid host mount and forged mint or scope inputs fail closed',()=>{
 assert.equal(mountFirstSpacesReview({}).state,'HOLD');
 assert.equal(planFirstSpacesReview({layout:'mint'}).state,'HOLD');
 assert.equal(planFirstSpacesReview({order:['family.cognigrex']}).state,'HOLD');
 assert.equal(planFirstSpacesReview({decisions:{'family.eco':'sign'}}).state,'HOLD');
 const root=mount();mountFirstSpacesReview(root);
 assert.ok(!all(root).some(x=>['script','iframe','form','input'].includes(x.tagName)));
 assert.equal(find(root,'data-cgx-design','mint'),undefined);
});

test('export keeps visual choices but cannot grant native signing, mutation, mint or release',async()=>{
 const {makeFirstSpacesDesignExport}=await import('./cgxFirstSpacesReviewModel.mjs');
 const original=planFirstSpacesReview();
 const reverse=[...original.order].reverse();
 const receipt=makeFirstSpacesDesignExport({order:reverse,layout:'space-grid',
  focus:'family.eco',decisions:{'family.eco':'approve'}});
 assert.equal(receipt.state,'LOCAL_DESIGN_REVIEW_FOR_FOUNDER_RECONCILIATION');
 assert.deepEqual(receipt.visual_order,reverse);
 assert.deepEqual(receipt.dependency_pinned_press_order,original.mint_sequence);
 assert.equal(receipt.choices.find(x=>x.key==='family.eco').design_review_state,
  'DESIGN_APPROVED_ONLY');
 for(const key of ['founder_native_signoff','native_mint_authorised',
 'public_release_authorised','canonical_mutation','source_bytes_included']){
  assert.equal(receipt[key],false,key);
 }
 assert.equal(makeFirstSpacesDesignExport({decisions:{'family.eco':'mint'}}).state,'HOLD');
});

test('presentation variants never alter identity, dependencies or authority',async()=>{
 const {presentationPreferences,presentationStyle}=await import('./cgxPresentationPreferences.mjs');
 const original=planFirstSpacesReview();
 const preferences={locale:'en-AU',region:'AU',hue:145,background:'paper',density:'compact',motion:'reduced'};
 const view=planFirstSpacesReview({presentation:preferences});
 assert.equal(view.state,'SOURCE_REVIEW_ONLY');
 assert.deepEqual(view.presentation,preferences);
 assert.deepEqual(view.nodes,original.nodes);assert.deepEqual(view.edges,original.edges);
 assert.deepEqual(view.mint_sequence,original.mint_sequence);
 assert.equal(view.may_sign,false);assert.equal(view.may_publish,false);
 const {makeFirstSpacesDesignExport}=await import('./cgxFirstSpacesReviewModel.mjs');
 const output=makeFirstSpacesDesignExport({presentation:preferences});
 assert.deepEqual(output.presentation_preferences,preferences);
 assert.equal(output.geography_is_presentation_only,true);
 assert.equal(output.social_opt_in_granted,false);
 assert.equal(presentationStyle(preferences).background,'#f5f4ef');
 for(const bad of [{hue:NaN},{hue:360},{hue:-1},{region:'<script>'},{locale:'invalid_locale'},
   {background:'url(https://example.com)'},{mint:true},{social_opt_in:true},null,[]]){
   assert.throws(()=>presentationPreferences(bad));
   assert.equal(planFirstSpacesReview({presentation:bad}).state,'HOLD');
 }
});
test('appearance controls update scoped preview and unregister on disposal',()=>{
 const root=mount();const controller=mountFirstSpacesReview(root);
 let select=find(root,'data-cgx-preference','background');select.value='paper';
 root.handlers.change({target:select});
 assert.match(find(root,'data-cgx-press','SOURCE_REVIEW_ONLY').getAttribute('style'),/#f5f4ef/);
 select=find(root,'data-cgx-preference','region');select.value='AU';root.handlers.change({target:select});
 assert.match(text(root),/no location, legal or SocialSpace permissions/);
 const baseline=selectOrder(root);
 select=find(root,'data-cgx-preference','hue');select.value='not-a-number';root.handlers.change({target:select});
 assert.deepEqual(selectOrder(root),baseline);
 controller.dispose();assert.equal(root.handlers.change,undefined);
});
