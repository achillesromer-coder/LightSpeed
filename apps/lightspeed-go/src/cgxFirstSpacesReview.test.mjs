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
