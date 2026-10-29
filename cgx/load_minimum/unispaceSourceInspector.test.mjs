import test from 'node:test';
import assert from 'node:assert/strict';
import {planUniSpaceSourceInspector as inspect} from './unispaceSourceInspector.mjs';
const h='a'.repeat(64);
// Synthetic fixtures only; not native Object_IDs, real R0 bytes, or live ACLs.
const nodes=[
 {object_id:'fixture:eco:one',file_space:'Eco.cgx',owner:'Eco-Grex',domain:'eco',kind:'observation',
  source_refs:['fixture:eco:source'],edges:[{to:'fixture:romer:private',relation:'HAS_SITE'}],
  geometry:{source_ref:'fixture:eco:source',frame:'EPSG:7856',units:'m'},evidence_ceiling:'synthetic'},
 {object_id:'fixture:romer:private',file_space:'Romer.cgx',owner:'Römer-Grex',domain:'romer',
  source_refs:['fixture:romer:private-source'],edges:[]}
];
const access={authorized_object_ids:['fixture:eco:one'],authorized_source_ids:['fixture:eco:source']};
const source_envelopes=[{source_id:'fixture:eco:source',sha256:h,version:'fixture-v1',owner:'fixture-owner',rights:'OWNER_PRIVATE',proof_class:'scientific'},
 {source_id:'fixture:romer:private-source',sha256:'b'.repeat(64),version:'secret',owner:'secret',rights:'OWNER_PRIVATE',proof_class:'engineering'}];
const args={nodes,focus_id:'fixture:eco:one',access,file_space:'Eco.cgx',source_envelopes};
test('one exact child FileSpace and Object_ID, no parent alias or cross-domain leak',()=>{
 const x=inspect(args);assert.equal(x.identity,'fixture:eco:one');assert.equal(x.selected_file_space,'Eco.cgx');
 assert.deepEqual(x.h1.object_ids,['fixture:eco:one']);assert.ok(!JSON.stringify(x).includes('fixture:romer:private'));
 assert.equal(inspect({...args,file_space:'Romer.cgx'}).status,'DENIED');
});
test('H0–H4 and R3 are presentation plans, never installed or authenticated',()=>{
 const x=inspect(args);assert.equal(x.admission_stage,'R3_VIEW_PROPOSAL');
 assert.equal(x.h0.accepted,false);assert.equal(x.h3.qualified_capabilities.length,0);
 assert.equal(x.h4.installed,false);assert.equal(x.host_authenticated,false);
 assert.equal(x.provider_readback,false);assert.equal(x.public_release,false);
});
test('missing or unqualified source envelope becomes Frontier',()=>{
 for(const envelopes of [[],[{...source_envelopes[0],sha256:'wrong'}],
  [{...source_envelopes[0],rights:'LICENSE_RESTRICTED'}]]){
  const x=inspect({...args,source_envelopes:envelopes});
  assert.equal(x.viewport.state,'FRONTIER');assert.equal(x.admission_stage,'R2_REVIEW_FRONTIER');
 }
});
test('3D without source-qualified geometry is Frontier rather than fake model',()=>{
 const x=inspect({...args,view:'3d',source_envelopes:[]});
 assert.equal(x.viewport.state,'FRONTIER');assert.equal(x.viewport.geometry_ref,null);
 assert.equal(x.viewport.rendered,false);
});
test('no source ACL or wrong Object_ID denies without disclosing graph',()=>{
 assert.equal(inspect({...args,access:{}}).status,'DENIED');
 const x=inspect({...args,focus_id:'fixture:romer:private'});
 assert.equal(x.status,'DENIED');assert.ok(!JSON.stringify(x).includes('fixture:romer:private-source'));
});
test('creative and scientific classes remain typed, not averaged',()=>{
 const x=inspect({...args,source_envelopes:[{...source_envelopes[0],proof_class:'creative'}]});
 assert.deepEqual(x.h2.proof_classes,['creative']);assert.equal(x.h2.source_proof,'CALLER_DECLARATIONS_ONLY');
});
test('offline and constrained budgets do not trigger hydration or writes',()=>{
 const x=inspect({...args,budgets:{max_nodes:1,max_hops:0,max_transfer_bytes:0}});
 assert.equal(x.offline_fallback,'H0_H2_DECLARED_METADATA_ONLY');assert.equal(x.network_fetch,false);
 assert.equal(x.canonical_mutation,false);assert.equal(x.budgets.max_transfer_bytes,0);
});
test('R3 proposal cannot omit a denied or budget-truncated focus source',()=>{
 const extra='fixture:eco:restricted-source';
 const restrictedNodes=[{...nodes[0],source_refs:['fixture:eco:source',extra]},nodes[1]];
 const x=inspect({...args,nodes:restrictedNodes});
 assert.equal(x.viewport.state,'FRONTIER');
 assert.equal(x.admission_stage,'R2_REVIEW_FRONTIER');
 assert.ok(!JSON.stringify(x).includes(extra));
 const budgeted=inspect({...args,budgets:{max_evidence_refs:0}});
 assert.equal(budgeted.viewport.state,'FRONTIER');
 assert.equal(budgeted.admission_stage,'R2_REVIEW_FRONTIER');
});

test('conflicting duplicate source envelope holds rather than taking first record',()=>{
 const x=inspect({...args,source_envelopes:[source_envelopes[0],{...source_envelopes[0],sha256:'b'.repeat(64)}]});
 assert.equal(x.viewport.state,'FRONTIER');assert.equal(x.h2.source_claims[0].qualification,'FRONTIER_COLLIDING_SOURCE');
});

test('invalid view, budget, or graph fails closed without disclosing private sibling',()=>{
 const invalid=[
  {...args,view:'unregistered-view'},
  {...args,budgets:{max_nodes:0}},
  {...args,budgets:null},
  {...args,nodes:[...nodes,nodes[0]]},
  {...args,nodes:[{...nodes[0],edges:[{to:'fixture:romer:private'}]},nodes[1]]}
 ];
 for(const input of invalid){
  let result;
  assert.doesNotThrow(()=>{result=inspect(input)});
  assert.equal(result.status,'DENIED');
  assert.equal(result.canonical_mutation,false);
  assert.equal(result.public_release,false);
  assert.ok(!JSON.stringify(result).includes('fixture:romer:private-source'));
 }
});
