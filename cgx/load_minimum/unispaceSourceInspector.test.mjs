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
const source_envelopes=[{source_id:'fixture:eco:source',sha256:h,version:'fixture-v1',owner:'fixture-owner',rights:'OWNER_PRIVATE',proof_class:'scientific',rights_state:'ACTIVE'},
 {source_id:'fixture:romer:private-source',sha256:'b'.repeat(64),version:'secret',owner:'secret',rights:'OWNER_PRIVATE',proof_class:'engineering'}];
const args={nodes,focus_id:'fixture:eco:one',access,file_space:'Eco.cgx',source_envelopes,surface:'private'};
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

test('explicit cross-domain budget cannot override Object_ID/source ACL or leak sibling provenance',()=>{
 const budget={max_cross_domains:1,max_cross_edges:1,max_hops:1};
 // A requested cross-domain halo is not itself an access grant.
 const denied=inspect({...args,budgets:budget});
 assert.equal(denied.status,'SOURCE_REVIEW_ONLY');
 assert.deepEqual(denied.h1.object_ids,['fixture:eco:one']);
 assert.equal(denied.h1.edges.length,0);
 assert.ok(!JSON.stringify(denied).includes('fixture:romer:private-source'));
 // Even an authorised object does not expose source evidence without its own ACL.
 const objectOnly=inspect({...args,budgets:budget,access:{
  authorized_object_ids:['fixture:eco:one','fixture:romer:private'],
  authorized_source_ids:['fixture:eco:source']
 }});
 assert.deepEqual(objectOnly.h1.object_ids,['fixture:eco:one','fixture:romer:private']);
 assert.ok(!JSON.stringify(objectOnly).includes('fixture:romer:private-source'));
 assert.deepEqual(objectOnly.h2.source_claims.map(x=>x.source_id),['fixture:eco:source']);
 // An explicit grant to both source and object can expand H1, never H4 authority.
 const permitted=inspect({...args,budgets:budget,access:{
  authorized_object_ids:['fixture:eco:one','fixture:romer:private'],
  authorized_source_ids:['fixture:eco:source','fixture:romer:private-source']
 }});
 assert.deepEqual(permitted.h1.object_ids,['fixture:eco:one','fixture:romer:private']);
 assert.equal(permitted.h1.edges.length,1);
 assert.equal(permitted.h4.installed,false);
 assert.equal(permitted.provider_readback,false);
 assert.equal(permitted.public_release,false);
});

test('known Grex domain cannot be impersonated by a different child FileSpace',()=>{
 const wrong=[{...nodes[0],domain:'romer'},nodes[1]];
 const x=inspect({...args,nodes:wrong});
 assert.equal(x.status,'DENIED');
 assert.equal(x.reason,'FILESPACE_OR_ID_UNRESOLVED');
 assert.equal(x.canonical_mutation,false);
 assert.equal(x.public_release,false);
 assert.ok(!JSON.stringify(x).includes('fixture:romer:private-source'));
 // The original authorised Eco fixture remains an R3 private proposal only.
 const valid=inspect(args);
 assert.equal(valid.status,'SOURCE_REVIEW_ONLY');
 assert.equal(valid.admission_stage,'R3_VIEW_PROPOSAL');
 assert.equal(valid.host_authenticated,false);
});


test('cross-Grex authorized halo refuses a sibling spoofed into the wrong child FileSpace',()=>{
 const budgets={max_cross_domains:1,max_cross_edges:1,max_hops:1};
 const accessBoth={authorized_object_ids:['fixture:eco:one','fixture:romer:private'],
  authorized_source_ids:['fixture:eco:source','fixture:romer:private-source']};
 const spoofed=[nodes[0],{...nodes[1],file_space:'Eco.cgx'}];
 const denied=inspect({...args,nodes:spoofed,budgets,access:accessBoth});
 assert.equal(denied.status,'DENIED');
 assert.equal(denied.reason,'CHILD_FILESPACE_SCOPE_CONFLICT');
 assert.equal(denied.canonical_mutation,false);
 assert.equal(denied.public_release,false);
 assert.ok(!JSON.stringify(denied).includes('fixture:romer:private'));
 const valid=inspect({...args,budgets,access:accessBoth});
 assert.equal(valid.status,'SOURCE_REVIEW_ONLY');
 assert.deepEqual(valid.h1.object_ids,['fixture:eco:one','fixture:romer:private']);
});

// #158: a source-only inspector cannot become a public Vite data source via
// caller-declared PUBLIC_SAFE rights or by omitting the surface selection.
test('public, omitted and unknown surfaces fail closed without H0-H4 or private provenance',()=>{
 for(const surface of ['public','untrusted',null]){
  const x=inspect({...args,surface,source_envelopes:[{...source_envelopes[0],rights:'PUBLIC_SAFE'}]});
  assert.equal(x.status,'DENIED');
  assert.equal(x.reason,'PRIVATE_INSPECTOR_SURFACE_REQUIRED');
  assert.equal(x.public_release,false);
  assert.equal(x.canonical_mutation,false);
  assert.ok(!JSON.stringify(x).includes('fixture:eco:source'));
  assert.ok(!JSON.stringify(x).includes('fixture:romer:private-source'));
 }
 const omitted={...args};delete omitted.surface;
 assert.equal(inspect(omitted).status,'DENIED');
 assert.equal(inspect(args).status,'SOURCE_REVIEW_ONLY');
});

// #158 / C33: rights revocation or supersession must invalidate a previously
// qualified private R3 review candidate; no provider/host claim is made.
// An absent grant state must not look like a qualified R3 private viewport.
test('missing rights-state is Frontier despite a syntactically valid source envelope',()=>{
 const envelope={...source_envelopes[0]};delete envelope.rights_state;
 const x=inspect({...args,source_envelopes:[envelope]});
 assert.equal(x.status,'SOURCE_REVIEW_ONLY');
 assert.equal(x.viewport.state,'FRONTIER');
 assert.equal(x.admission_stage,'R2_REVIEW_FRONTIER');
 assert.equal(x.h2.source_claims[0].qualification,'FRONTIER_RIGHTS_REVOKED_OR_UNRESOLVED');
 assert.equal(x.h2.source_claims[0].sha256,null);
 assert.equal(x.host_authenticated,false);
 assert.equal(x.provider_readback,false);
 assert.equal(x.public_release,false);
});

test('revoked superseded or non-ACTIVE source envelopes cannot support R3',()=>{
 for(const signal of [
  {rights_state:'REVOKED'},{rights_state:'SUPERSEDED'},{rights_state:'UNRESOLVED'},
  {rights_state:'VALID'},{revoked:true},{rights_revoked:true},
  {revoked_at:'2026-10-30T00:00:00Z'},{superseded_by:'next-grant'}
 ]){
  const x=inspect({...args,source_envelopes:[{...source_envelopes[0],...signal}]});
  assert.equal(x.status,'SOURCE_REVIEW_ONLY');
  assert.equal(x.viewport.state,'FRONTIER');
  assert.equal(x.admission_stage,'R2_REVIEW_FRONTIER');
  assert.equal(x.h2.source_claims[0].qualification,'FRONTIER_RIGHTS_REVOKED_OR_UNRESOLVED');
  assert.equal(x.h2.source_claims[0].sha256,null);
  assert.equal(x.h4.installed,false);
  assert.equal(x.provider_readback,false);
  assert.equal(x.public_release,false);
 }
 const stillReview=inspect({...args,source_envelopes:[{...source_envelopes[0],rights_state:'ACTIVE'}]});
 assert.equal(stillReview.admission_stage,'R3_VIEW_PROPOSAL');
 assert.equal(stillReview.host_authenticated,false);
});

test('#209 metric 3D stop-ship rejects claimed verification and decorative geometry',()=>{
 const forged={...source_envelopes[0],provider_readback:true,hash_verified:true,
  metric_verified:true,independent_numeric_validation:true,native_admitted:true,
  host_authenticated:true,signed_handshake:true};
 for(const proof_class of ['scientific','engineering','operational','creative']){
  const x=inspect({...args,view:'3d',source_envelopes:[{...forged,proof_class}]});
  assert.equal(x.status,'SOURCE_REVIEW_ONLY');
  assert.equal(x.viewport.state,'FRONTIER');
  assert.equal(x.admission_stage,'R2_REVIEW_FRONTIER');
  assert.ok(x.viewport.frontier.includes('METRIC_GEOMETRY_PROVIDER_AND_INDEPENDENT_VALIDATION_REQUIRED'));
  assert.equal(x.viewport.geometry_ref,null);
  assert.equal(x.viewport.metric_authority,'NOT_VERIFIED');
  assert.equal(x.viewport.rendered,false);
  assert.equal(x.host_authenticated,false);
  assert.equal(x.provider_readback,false);
  assert.equal(x.h4.installed,false);
  assert.equal(x.public_release,false);
 }
 const doc=inspect({...args,view:'document'});
 assert.equal(doc.admission_stage,'R3_VIEW_PROPOSAL');
 assert.equal(doc.viewport.metric_authority,'NOT_VERIFIED');
});
