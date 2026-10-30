import test from 'node:test';
import assert from 'node:assert/strict';
import {planUniSpaceSourceInspector as inspect,planUniSpaceOperatorCockpit as cockpit} from './unispaceSourceInspector.mjs';
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

// #158: ambiguous revocation values must not silently grant a private R3
// source proposal. Only an absent flag or explicit boolean false is non-veto.
test('ambiguous explicit revocation flags fail closed before R3 proposal',()=>{
 const clean=inspect(args);
 assert.equal(clean.admission_stage,'R3_VIEW_PROPOSAL');
 for(const field of ['revoked','rights_revoked']){
  const allowed=inspect({...args,source_envelopes:[{...source_envelopes[0],[field]:false}]});
  assert.equal(allowed.admission_stage,'R3_VIEW_PROPOSAL',field);
  for(const value of ['true','false',1,0,null,undefined,{},[]]){
   const denied=inspect({...args,source_envelopes:[{...source_envelopes[0],[field]:value}]});
   assert.equal(denied.status,'SOURCE_REVIEW_ONLY',field);
   assert.equal(denied.viewport.state,'FRONTIER',field);
   assert.equal(denied.admission_stage,'R2_REVIEW_FRONTIER',field);
   assert.equal(denied.h2.source_claims[0].qualification,
    'FRONTIER_RIGHTS_REVOKED_OR_UNRESOLVED',field);
   assert.equal(denied.h2.source_claims[0].sha256,null);
   assert.equal(denied.h4.installed,false);
   assert.equal(denied.provider_readback,false);
   assert.equal(denied.public_release,false);
  }
 }
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


// #158: source-scoped ACL arrays cannot turn an unknown/aliased domain into
// a reserved Grex child FileSpace, including through an authorised halo.
test('reserved child FileSpace cannot be claimed by an unknown domain or alias',()=>{
 for(const domain of ['unknown','Eco','custom']){
  const spoofed=[{...nodes[0],domain},nodes[1]];
  const x=inspect({...args,nodes:spoofed});
  assert.equal(x.status,'DENIED',domain);
  assert.equal(x.reason,'FILESPACE_OR_ID_UNRESOLVED',domain);
  assert.equal(x.canonical_mutation,false);
  assert.equal(x.public_release,false);
  assert.ok(!JSON.stringify(x).includes('fixture:eco:source'));
 }
 // Custom, non-reserved child FileSpaces remain reviewable, never admitted.
 const custom=[{...nodes[0],domain:'custom',file_space:'Custom.cgx'},nodes[1]];
 const review=inspect({...args,nodes:custom,file_space:'Custom.cgx'});
 assert.equal(review.status,'SOURCE_REVIEW_ONLY');
 assert.equal(review.host_authenticated,false);
 assert.equal(review.h4.installed,false);
});
test('unknown-domain sibling cannot impersonate reserved Grex FileSpace in halo',()=>{
 const spoofed=[nodes[0],{...nodes[1],domain:'unregistered',file_space:'Romer.cgx'}];
 const x=inspect({...args,nodes:spoofed,
  budgets:{max_cross_domains:1,max_cross_edges:1,max_hops:1},
  access:{authorized_object_ids:['fixture:eco:one','fixture:romer:private'],
   authorized_source_ids:['fixture:eco:source','fixture:romer:private-source']}});
 assert.equal(x.status,'DENIED');
 assert.equal(x.reason,'CHILD_FILESPACE_SCOPE_CONFLICT');
 assert.equal(x.canonical_mutation,false);
 assert.equal(x.public_release,false);
 assert.ok(!JSON.stringify(x).includes('fixture:romer:private'));
});

test('offline mode cannot reuse cached ACTIVE rights or expose stored provenance',()=>{
 const cached={...source_envelopes[0],rights_state:'ACTIVE'};
 for(const view of ['document','3d','chat','graph','interactive','matrix']){
  const x=inspect({...args,view,offline:true,source_envelopes:[cached],
   budgets:{max_cross_domains:1,max_cross_edges:1,max_hops:1},
   access:{authorized_object_ids:['fixture:eco:one','fixture:romer:private'],
    authorized_source_ids:['fixture:eco:source','fixture:romer:private-source']}});
  assert.equal(x.status,'SOURCE_REVIEW_ONLY');
  assert.equal(x.identity,'fixture:eco:one');
  assert.equal(x.selected_file_space,'Eco.cgx');
  assert.equal(x.viewport.state,'FRONTIER');
  assert.equal(x.admission_stage,'R2_REVIEW_FRONTIER');
  assert.deepEqual(x.viewport.frontier,['OFFLINE_AUTHORITY_AND_REVOCATION_UNVERIFIED']);
  assert.deepEqual(x.h1.object_ids,['fixture:eco:one']);
  assert.deepEqual(x.h1.edges,[]);
  assert.deepEqual(x.h2.source_claims,[]);
  assert.equal(x.h2.source_proof,'OFFLINE_UNVERIFIED');
  assert.equal(x.viewport.geometry_ref,null);
  assert.equal(x.viewport.rendered,false);
  assert.equal(x.budgets.max_transfer_bytes,0);
  assert.equal(x.network_fetch,false);
  assert.equal(x.host_authenticated,false);
  assert.equal(x.provider_readback,false);
  assert.equal(x.h4.installed,false);
  assert.equal(x.canonical_mutation,false);
  assert.equal(x.public_release,false);
  assert.ok(!JSON.stringify(x).includes('fixture:eco:source'));
  assert.ok(!JSON.stringify(x).includes('fixture:romer:private'));
  assert.ok(!JSON.stringify(x).includes(cached.sha256));
 }
});
test('offline identity and mode validation deny without source leakage',()=>{
 const invalid=[
  {...args,offline:true,access:{authorized_object_ids:[],
   authorized_source_ids:['fixture:eco:source']}},
  {...args,offline:true,view:'unregistered'},
  {...args,offline:'true'},
  {...args,offline:null},
  {...args,offline:true,file_space:'Romer.cgx'}
 ];
 for(const input of invalid){
  const x=inspect(input);
  assert.equal(x.status,'DENIED');
  assert.equal(x.canonical_mutation,false);
  assert.equal(x.public_release,false);
  assert.ok(!JSON.stringify(x).includes('fixture:eco:source'));
 }
 // Online behaviour remains a review proposal, never provider verification.
 const online=inspect(args);
 assert.equal(online.status,'SOURCE_REVIEW_ONLY');
 assert.equal(online.admission_stage,'R3_VIEW_PROPOSAL');
 assert.equal(online.provider_readback,false);
});

test('opaque source, Object_ID and graph identifiers reject directional/invisible Unicode controls',()=>{
 for(const mark of ['\u202e','\u2066','\u200b','\u034f']){
  const ambiguousId='fixture:eco:one'+mark;
  const changed=[{...nodes[0],object_id:ambiguousId},nodes[1]];
  const cases=[
   {...args,focus_id:ambiguousId,nodes:changed,
    access:{...access,authorized_object_ids:[ambiguousId]}},
   {...args,access:{...access,authorized_source_ids:['fixture:eco:source'+mark]}},
   {...args,nodes:[{...nodes[0],domain:'eco'+mark},nodes[1]]},
   {...args,nodes:[{...nodes[0],edges:[{to:'fixture:romer:private',relation:'HAS_SITE'+mark}]},nodes[1]]},
   {...args,nodes:[{...nodes[0],source_refs:['fixture:eco:source'+mark]},nodes[1]]},
   {...args,offline:true,file_space:'Eco.cgx'+mark,
    nodes:[{...nodes[0],file_space:'Eco.cgx'+mark},nodes[1]]}
  ];
  for(const input of cases){
   const x=inspect(input);
   assert.equal(x.status,'DENIED');
   assert.equal(x.reason,'AMBIGUOUS_IDENTITY_OR_SCOPE');
   assert.equal(x.canonical_mutation,false);
   assert.equal(x.public_release,false);
   assert.ok(!JSON.stringify(x).includes('fixture:eco:source'));
  }
 }
});
test('non-NFC Object_ID and deceptive owner version text cannot become private view claims',()=>{
 const decomposedId='fixture:eco:cafe\u0301';
 const changed=[{...nodes[0],object_id:decomposedId},nodes[1]];
 const denied=inspect({...args,focus_id:decomposedId,nodes:changed,
  access:{...access,authorized_object_ids:[decomposedId]}});
 assert.equal(denied.status,'DENIED');
 assert.equal(denied.reason,'AMBIGUOUS_IDENTITY_OR_SCOPE');
 const active={...source_envelopes[0]};
 for(const unsafe of [
  {...active,version:'v1\u2066'},
  {...active,owner:'apparent-owner\u202e'}
 ]){
  const x=inspect({...args,source_envelopes:[unsafe]});
  assert.equal(x.status,'SOURCE_REVIEW_ONLY');
  assert.equal(x.viewport.state,'FRONTIER');
  assert.equal(x.admission_stage,'R2_REVIEW_FRONTIER');
  assert.equal(x.h2.source_claims[0].qualification,'FRONTIER_SOURCE_QUALIFICATION');
  assert.equal(x.h2.source_claims[0].sha256,null);
  assert.equal(x.h4.installed,false);
  assert.equal(x.public_release,false);
 }
 // Ordinary Unicode names and native ASCII IDs remain valid review metadata.
 const normal=inspect({...args,nodes:[{...nodes[0],owner:'Römer-Grex'},nodes[1]]});
 assert.equal(normal.status,'SOURCE_REVIEW_ONLY');
 assert.equal(normal.h0.owner,'Römer-Grex');
 assert.equal(normal.host_authenticated,false);
});


// Cockpit is a private R3 proposal/Frontier status adapter, never an actual
// browser session, native RootAuthority acceptance, or DBR/host readback.
const selected={parent_file_space:'Cognigrex.cgx',file_space:'Eco.cgx',
 domain:'eco',object_id:'fixture:eco:one'};
const statusInput={surface:'private',selection:selected,inspector:inspect(args)};

test('private cockpit maps exact review identity to non-elevated DAG',()=>{
 const x=cockpit(statusInput);
 assert.equal(x.state,'SOURCE_REVIEW_ONLY');
 assert.equal(x.identity,selected.object_id);
 assert.equal(x.file_space,'Eco.cgx');
 assert.equal(x.presentation_stage,'R3_VIEW_PROPOSAL');
 assert.equal(x.next_step,'REQUEST_INDEPENDENT_NATIVE_ROOT_LEASE_ACL_DBR_AND_READBACK');
 assert.deepEqual(x.workflow.map(y=>y.stage),[
  'DISCOVERED','QUALIFIED','STAGED','TESTED','ADMITTED',
  'DEPLOYED','LIVE_VERIFIED','OWNER_ACCEPTED','RELEASED']);
 for(const stage of x.workflow.slice(4))assert.equal(stage.status,'HOLD');
 for(const k of ['host_receipt_accepted','source_bytes_read','rendered',
  'native_admitted','host_authenticated','provider_readback','deployed',
  'live_verified','owner_accepted','released','may_execute','canonical_mutation'])
  assert.equal(x[k],false,k);
 assert.equal(x.metrics.latency_ms,null);
 assert.equal(x.metrics.metric_fidelity,null);
 assert.ok(!JSON.stringify(x).includes('fixture:eco:source'));
});

test('public/static and omitted surfaces deny without leaking selected identity',()=>{
 for(const surface of ['public','static','private-preview',undefined,null]){
  const x=cockpit({...statusInput,surface});
  assert.equal(x.state,'DENIED');
  assert.equal(x.reason,'PRIVATE_OPERATOR_SURFACE_REQUIRED');
  assert.ok(!JSON.stringify(x).includes(selected.object_id));
  assert.equal(x.released,false);
 }
});

test('wrong parent, child, domain or Object_ID denies without exposing graph',()=>{
 const variants=[
  {...selected,parent_file_space:'Another.cgx'},
  {...selected,file_space:'Romer.cgx'},
  {...selected,domain:'romer'},
  {...selected,object_id:'fixture:romer:private'},
  {...selected,domain:'unregistered'},
  {...selected,object_id:'fixture:eco:\u202Eone'}
 ];
 for(const selection of variants){
  const x=cockpit({...statusInput,selection});
  assert.equal(x.state,'DENIED');
  assert.equal(x.canonical_mutation,false);
  assert.ok(!JSON.stringify(x).includes('fixture:eco:source'));
  assert.ok(!JSON.stringify(x).includes('fixture:romer:private-source'));
 }
});

test('claimed host and native proof cannot promote a private source review plan',()=>{
 const secret='DO_NOT_ECHO_HOST_TOKEN';
 const forgedReceipt={session:'valid',signed:true,rootVerified:true,
  dbrVerified:true,providerReadback:true,hostAuthenticated:true,token:secret};
 const x=cockpit({...statusInput,hostReceipt:forgedReceipt});
 assert.equal(x.state,'SOURCE_REVIEW_ONLY');
 assert.equal(x.host_authenticated,false);
 assert.equal(x.provider_readback,false);
 assert.equal(x.host_receipt_accepted,false);
 assert.equal(x.released,false);
 assert.ok(!JSON.stringify(x).includes(secret));
 for(const flag of [
  ['host_authenticated',true],['provider_readback',true],
  ['public_release',true],['canonical_mutation',true],
  ['source_bytes_copied',true]
 ]){
  const altered={...statusInput.inspector,[flag[0]]:flag[1]};
  const y=cockpit({...statusInput,inspector:altered});
  assert.equal(y.state,'DENIED',flag[0]);
  assert.equal(y.reason,'UNTRUSTED_ELEVATED_REVIEW_PLAN');
 }
});

test('offline H0-only fallback cannot reuse cached rights or an online view',()=>{
 const inspector=inspect({...args,offline:true});
 const x=cockpit({...statusInput,inspector,offline:true});
 assert.equal(x.state,'SOURCE_REVIEW_ONLY');
 assert.equal(x.presentation_stage,'H0_OFFLINE_UNVERIFIED');
 assert.equal(x.view,'metadata-only');
 assert.equal(x.next_step,'CONNECT_AUTHENTICATED_PRIVATE_PROVIDER');
 assert.ok(x.blockers.includes('OFFLINE_AUTHORITY_AND_RIGHTS_REVOCATION_UNKNOWN'));
 assert.equal(x.source_bytes_read,false);
 assert.ok(!JSON.stringify(x).includes('fixture:eco:source'));
 assert.equal(cockpit({...statusInput,inspector,offline:false}).state,'DENIED');
 assert.equal(cockpit({...statusInput,offline:true}).state,'DENIED');
});

test('unqualified R2 Frontier cannot become ready through a forged stage',()=>{
 const inspector=inspect({...args,source_envelopes:[]});
 const x=cockpit({...statusInput,inspector});
 assert.equal(x.state,'SOURCE_REVIEW_ONLY');
 assert.equal(x.presentation_stage,'R2_REVIEW_FRONTIER');
 assert.equal(x.next_step,'QUALIFY_SOURCE_AND_VIEW_EVIDENCE');
 assert.ok(x.blockers.includes('VIEW_EVIDENCE_FRONTIER'));
 const forged={...inspector,admission_stage:'R3_VIEW_PROPOSAL'};
 assert.equal(cockpit({...statusInput,inspector:forged}).state,'DENIED');
});

// #158/#209: R3 review status cannot be synthesized from an empty or
// internally inconsistent set of R0 source declarations. These are negative
// UI contract tests, not real provider ACL, native DBR or browser acceptance.
test('R3 document claims cannot be fabricated from missing or contradictory R0 proof',()=>{
 const valid=statusInput.inspector;
 assert.equal(cockpit(statusInput).presentation_stage,'R3_VIEW_PROPOSAL');
 const claim=valid.h2.source_claims[0];
 const variants=[
  {...valid,h2:{...valid.h2,source_claims:[]}},
  {...valid,h2:{...valid.h2,proof_classes:[]}},
  {...valid,h2:{...valid.h2,source_claims:[claim,claim]}},
  {...valid,h2:{...valid.h2,source_claims:[{...claim,qualification:'FRONTIER_RIGHTS_REVOKED_OR_UNRESOLVED'}]}},
  {...valid,h2:{...valid.h2,source_claims:[{...claim,sha256:null}]}},
  {...valid,h2:{...valid.h2,source_claims:[{...claim,version:null}]}},
  {...valid,h2:{...valid.h2,source_claims:[{...claim,rights:'LICENSE_RESTRICTED'}]}},
  {...valid,h2:{...valid.h2,source_claims:[{...claim,proof_class:'creative'}]}}
 ];
 // The geometry-reference consistency veto runs before the R0-claim veto.
 // Missing/revoked geometry anchor claims must deny as metric-unverified;
 // the remaining malformed R0 claims must deny as source-unqualified.
 const expectedReasons=[
  'UNVERIFIED_METRIC_VIEW_CANNOT_BE_R3',
  'R3_SOURCE_PROOF_CLAIMS_UNQUALIFIED',
  'R3_SOURCE_PROOF_CLAIMS_UNQUALIFIED',
  'UNVERIFIED_METRIC_VIEW_CANNOT_BE_R3',
  'R3_SOURCE_PROOF_CLAIMS_UNQUALIFIED',
  'R3_SOURCE_PROOF_CLAIMS_UNQUALIFIED',
  'R3_SOURCE_PROOF_CLAIMS_UNQUALIFIED',
  'R3_SOURCE_PROOF_CLAIMS_UNQUALIFIED'
 ];
 for(const [index,inspector] of variants.entries()){
  const denied=cockpit({...statusInput,inspector});
  assert.equal(denied.state,'DENIED');
  assert.equal(denied.reason,expectedReasons[index]);
  assert.equal(denied.may_execute,false);
  assert.equal(denied.released,false);
  assert.ok(!JSON.stringify(denied).includes('fixture:eco:source'));
 }
 const frontier=inspect({...args,source_envelopes:[]});
 assert.equal(cockpit({...statusInput,inspector:frontier}).presentation_stage,'R2_REVIEW_FRONTIER');
});

test('#209 cockpit rejects forged metric R3, conflicting Frontier and verified badges',()=>{
 const real3d=inspect({...args,view:'3d'});
 assert.equal(real3d.admission_stage,'R2_REVIEW_FRONTIER');
 const safe=cockpit({...statusInput,inspector:real3d});
 assert.equal(safe.state,'SOURCE_REVIEW_ONLY');
 assert.equal(safe.presentation_stage,'R2_REVIEW_FRONTIER');
 const variants=[
  {...real3d,admission_stage:'R3_VIEW_PROPOSAL',
   viewport:{...real3d.viewport,state:'R3_PRIVATE_VIEW_CANDIDATE'}},
  {...statusInput.inspector,viewport:{...statusInput.inspector.viewport,
   metric_authority:'INDEPENDENTLY_VERIFIED'}},
  {...statusInput.inspector,viewport:{...statusInput.inspector.viewport,
   frontier:['METRIC_PROOF_MISSING']}},
  {...statusInput.inspector,viewport:{...statusInput.inspector.viewport,
   frontier:null}}
 ];
 for(const inspector of variants){
  const denied=cockpit({...statusInput,inspector});
  assert.equal(denied.state,'DENIED');
  assert.equal(denied.reason,'UNVERIFIED_METRIC_VIEW_CANNOT_BE_R3');
  assert.equal(denied.native_admitted,false);
  assert.equal(denied.live_verified,false);
  assert.equal(denied.released,false);
  assert.ok(!JSON.stringify(denied).includes('fixture:eco:source'));
 }
});


// #158/#209: the inspector object is untrusted, including its view label.
test('#209 R3 viewport intent and geometry cannot be spoofed by a caller',()=>{
 const base=statusInput.inspector;
 assert.equal(cockpit(statusInput).presentation_stage,'R3_VIEW_PROPOSAL');
 const variants=[
  {...base,view:'3D'},
  {...base,view:'unregistered'},
  {...base,view:null},
  {...base,viewport:{...base.viewport,geometry_ref:'fixture:unauthorised:geometry'}},
  {...base,viewport:{...base.viewport,geometry_ref:undefined}}
 ];
 for(const [index,inspector] of variants.entries()){
  const denied=cockpit({...statusInput,inspector});
  assert.equal(denied.state,'DENIED');
  assert.equal(denied.reason,index<3?'UNREGISTERED_VIEW_INTENT':'UNVERIFIED_METRIC_VIEW_CANNOT_BE_R3');
  assert.equal(denied.may_execute,false);
  assert.equal(denied.native_admitted,false);
  assert.equal(denied.live_verified,false);
  assert.ok(!JSON.stringify(denied).includes('fixture:eco:source'));
 }
 // Registered, non-metric source-review views remain review-only.
 for(const view of ['document','chat','graph','interactive','matrix']){
  const candidate=inspect({...args,view});
  if(candidate.admission_stage!=='R3_VIEW_PROPOSAL')continue;
  const result=cockpit({...statusInput,inspector:candidate});
  assert.equal(result.state,'SOURCE_REVIEW_ONLY');
  assert.equal(result.released,false);
 }
});


// #158/#209: source-only caller projections cannot relabel an R2/R3 view.
test('registered LOAD lens/projection cannot be relabelled by a caller',()=>{
 const valid=statusInput.inspector;
 const frontier=inspect({...args,view:'3d'});
 assert.equal(cockpit(statusInput).state,'SOURCE_REVIEW_ONLY');
 assert.equal(cockpit({...statusInput,inspector:frontier}).state,'SOURCE_REVIEW_ONLY');
 const variants=[
  {...valid,viewport:{...valid.viewport,lens:'twin-3d'}},
  {...valid,viewport:{...valid.viewport,projection:'geometry-twin'}},
  {...valid,view:'graph'},
  {...frontier,viewport:{...frontier.viewport,lens:'active-object-inspector'}},
  {...frontier,viewport:{...frontier.viewport,projection:'document-section'}}
 ];
 for(const inspector of variants){
  const result=cockpit({...statusInput,inspector});
  assert.equal(result.state,'DENIED');
  assert.equal(result.reason,'VIEWPORT_INTENT_PROJECTION_MISMATCH');
  assert.equal(result.canonical_mutation,false);
  assert.equal(result.released,false);
  assert.ok(!JSON.stringify(result).includes('fixture:eco:source'));
 }
});


test('R2 Frontier cannot bypass the registered LOAD view contract',()=>{
 const frontier=inspect({...args,view:'3d'});
 assert.equal(frontier.admission_stage,'R2_REVIEW_FRONTIER');
 const forged={...frontier,view:'unknown-projection'};
 const denied=cockpit({...statusInput,inspector:forged});
 assert.equal(denied.state,'DENIED');
 assert.equal(denied.reason,'UNREGISTERED_VIEW_INTENT');
 assert.equal(denied.native_admitted,false);
 assert.equal(denied.released,false);
 assert.ok(!JSON.stringify(denied).includes('fixture:eco:source'));
 const safe=cockpit({...statusInput,inspector:frontier});
 assert.equal(safe.state,'SOURCE_REVIEW_ONLY');
 assert.equal(safe.presentation_stage,'R2_REVIEW_FRONTIER');
});

test('offline H0-only review rejects cached graph, source and geometry projections',()=>{
 const offlineInspector=inspect({...args,offline:true});
 const safe=cockpit({...statusInput,inspector:offlineInspector,offline:true});
 assert.equal(safe.presentation_stage,'H0_OFFLINE_UNVERIFIED');
 const variants=[
  {...offlineInspector,view:'unknown-projection'},
  {...offlineInspector,h1:{...offlineInspector.h1,object_ids:[selected.object_id,'fixture:romer:private']}},
  {...offlineInspector,h1:{...offlineInspector.h1,edges:[{from:selected.object_id,to:'fixture:romer:private',relation:'HAS_SITE'}]}},
  {...offlineInspector,h2:{...offlineInspector.h2,source_claims:[{source_id:'fixture:eco:source'}]}},
  {...offlineInspector,viewport:{...offlineInspector.viewport,geometry_ref:'fixture:eco:source'}},
  {...offlineInspector,viewport:{...offlineInspector.viewport,projection:'geometry-twin'}},
  {...offlineInspector,viewport:{...offlineInspector.viewport,lens:'twin-3d'}}
 ];
 for(const [index,inspector] of variants.entries()){
  const denied=cockpit({...statusInput,inspector,offline:true});
  assert.equal(denied.state,'DENIED');
  assert.equal(denied.reason,index===0?'UNREGISTERED_VIEW_INTENT':'OFFLINE_H0_PROJECTION_CONFLICT');
  assert.equal(denied.native_admitted,false);
  assert.equal(denied.released,false);
  assert.ok(!JSON.stringify(denied).includes('fixture:eco:source'));
  assert.ok(!JSON.stringify(denied).includes('fixture:romer:private'));
 }
});


// #158: a stale or caller-forged offline inspector must not smuggle source
// classes, owner identity, capabilities, execution or metric proof into H0.
test('offline H0 projection rejects cached authority, rights, capabilities and budgets',()=>{
 const base=inspect({...args,offline:true});
 assert.equal(cockpit({...statusInput,inspector:base,offline:true}).presentation_stage,
  'H0_OFFLINE_UNVERIFIED');
 const secret='PRIVATE_SOURCE_NOT_FOR_OFFLINE';
 const variants=[
  {...base,h0:{...base.h0,owner:secret}},
  {...base,h1:{...base.h1,cross_domain_enabled:true}},
  {...base,h2:{...base.h2,proof_classes:['scientific']}},
  {...base,h3:{...base.h3,qualified_capabilities:['ccc.install']}},
  {...base,h3:{...base.h3,catalogue_discovery_only:true}},
  {...base,h4:{...base.h4,permissioned_execution:'HOST_VERIFIED'}},
  {...base,viewport:{...base.viewport,metric_authority:'VERIFIED'}},
  {...base,viewport:{...base.viewport,frontier:[]}},
  {...base,budgets:{...base.budgets,max_transfer_bytes:1}},
  {...base,budgets:{...base.budgets,max_nodes:2}},
  {...base,offline_fallback:'H0_H2_DECLARED_METADATA_ONLY'}
 ];
 for(const inspector of variants){
  const denied=cockpit({...statusInput,inspector,offline:true});
  assert.equal(denied.state,'DENIED');
  assert.equal(denied.reason,'OFFLINE_H0_PROJECTION_CONFLICT');
  assert.equal(denied.may_execute,false);
  assert.equal(denied.released,false);
  assert.ok(!JSON.stringify(denied).includes(secret));
  assert.ok(!JSON.stringify(denied).includes('fixture:eco:source'));
 }
});


// #158/#209: online review widgets cannot invent H3 CCC installs, H4 lease
// authority or independent metric verification by editing a projected object.
// Both R3 proposal and R2 Frontier are covered; neither is a host receipt.
test('online cockpit rejects forged capabilities, execution and metric authority',()=>{
 const r3=inspect(args);
 const r2=inspect({...args,source_envelopes:[]});
 for(const base of [r3,r2]){
  const clean=cockpit({...statusInput,inspector:base});
  assert.equal(clean.state,'SOURCE_REVIEW_ONLY');
  const variants=[
   {...base,h3:{...base.h3,qualified_capabilities:['ccc.install']}},
   {...base,h3:{...base.h3,catalogue_discovery_only:false}},
   {...base,h3:{...base.h3,qualified_capabilities:null}},
   {...base,h3:null},
   {...base,h4:{...base.h4,permissioned_execution:'HOST_VERIFIED'}},
   {...base,viewport:{...base.viewport,metric_authority:'INDEPENDENTLY_VERIFIED'}}
  ];
  for(const [index,forged] of variants.entries()){
   const denied=cockpit({...statusInput,inspector:forged});
   assert.equal(denied.state,'DENIED');
   assert.equal(denied.reason,index===5&&base.admission_stage==='R3_VIEW_PROPOSAL'?
    'UNVERIFIED_METRIC_VIEW_CANNOT_BE_R3':
    'ONLINE_REVIEW_CAPABILITY_OR_AUTHORITY_CONFLICT');
   assert.equal(denied.may_execute,false);
   assert.equal(denied.native_admitted,false);
   assert.equal(denied.released,false);
   assert.ok(!JSON.stringify(denied).includes('fixture:eco:source'));
  }
 }
});
