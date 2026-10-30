import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {planKnowledgeSpread,planViewportSwitch,planNovelMatching} from './loadSemanticViewport.mjs';
const registry=JSON.parse(readFileSync(new URL('./online_registry_projection_2026-10-28.json',import.meta.url),'utf8'));
// Deliberately SYNTHETIC regression fixtures: not published objects, measured geometry or native IDs.
const nodes=[
 {object_id:'fixture:eco:tree',domain:'eco',kind:'biological-individual',epistemic_state:'observed',
  evidence_ceiling:'synthetic-fixture',source_refs:['fixture:s1','fixture:protected'],
  geometry:{source_ref:'fixture:geo',frame:'EPSG:7856',units:'m'},
  edges:[{to:'fixture:eco:taxon',relation:'PART_OF'},{to:'fixture:romer:site',relation:'HAS_SITE'},{to:'fixture:eco:secret',relation:'EVIDENCED_BY'}]},
 {object_id:'fixture:eco:taxon',domain:'eco',kind:'taxon',source_refs:['fixture:s2'],edges:[]},
 {object_id:'fixture:romer:site',domain:'romer',kind:'site',source_refs:['fixture:s3'],edges:[]},
 {object_id:'fixture:eco:secret',domain:'eco',kind:'private',source_refs:['fixture:protected2'],edges:[]}
];
const access={authorized_object_ids:['fixture:eco:tree','fixture:eco:taxon','fixture:romer:site'],authorized_source_ids:['fixture:s1','fixture:s2','fixture:s3','fixture:geo']};
const spread=opts=>planKnowledgeSpread({nodes,focus_id:'fixture:eco:tree',access,...opts});
test('minimum semantic halo contains only authorised selected objects',()=>{
 const s=spread(); assert.equal(s.objects.length,3);
 assert.ok(!JSON.stringify(s).includes('fixture:eco:secret'));assert.ok(!JSON.stringify(s).includes('fixture:protected'));
});
test('cross-domain bandwidth zero excludes Römer from Eco child',()=>{
 const s=spread({budgets:{max_cross_domains:0}});assert.deepEqual(s.domains_visited,['eco']);assert.equal(s.objects.length,2);
});
test('node inclusion ceiling is independent of reasoning depth',()=>{
 const a=spread({budgets:{max_nodes:1,reasoning_depth:'deep'}});
 assert.equal(a.objects.length,1);assert.equal(a.budgets.reasoning_depth,'deep');
});
test('relationship hop ceiling prevents unneeded hydration',()=>{
 const a=spread({budgets:{max_hops:0}});assert.equal(a.objects.length,1);
});
test('compute-time and rate are limits only, no actual compute claimed',()=>{
 const a=spread({budgets:{max_compute_ms:4500,max_ops_per_second:20}});
 assert.equal(a.budgets.max_compute_ms,4500);assert.equal(a.budgets.max_ops_per_second,20);
 assert.equal(a.actual_compute_ms,null);assert.equal(a.actual_ops_per_second,null);
});
test('view switch preserves ID, source, scope and evidence ceiling',()=>{
 const a=spread();
 for(const view of ['document','3d','chat','graph','interactive','matrix']){
  const v=planViewportSwitch({spread:a,from:'document',to:view});
  assert.equal(v.identity,'fixture:eco:tree');assert.equal(v.rendered,false);
  assert.equal(v.evidence_ceiling,'synthetic-fixture');assert.equal(v.semantic_mutation,false);
 }
});
test('C39 geometry source must be bound to focus R0 as well as separately ACL-permitted',()=>{
 const unbound=nodes.map(n=>n.object_id==='fixture:eco:tree'
  ? {...n,source_refs:['fixture:s1'],geometry:{source_ref:'fixture:geo',frame:'EPSG:7856',units:'m'}}
  : n);
 const plan=spread({nodes:unbound});
 assert.equal(plan.status,'REVIEW_ONLY');
 assert.equal(plan.objects[0].geometry,null);
 assert.ok(!JSON.stringify(plan).includes('fixture:geo'));
 const switched=planViewportSwitch({spread:plan,to:'3d'});
 assert.equal(switched.state,'FRONTIER_GEOMETRY_UNQUALIFIED');
 assert.equal(switched.geometry_ref,null);
 assert.equal(switched.public_release,false);
 assert.equal(switched.interactive_execution,false);
 // A legitimate attachment still only produces a non-rendered view plan.
 const bound=unbound.map(n=>n.object_id==='fixture:eco:tree'
  ? {...n,source_refs:['fixture:s1','fixture:geo']} : n);
 const candidate=planViewportSwitch({spread:spread({nodes:bound}),to:'3d'});
 assert.equal(candidate.state,'SOURCE_LINKED_3D_REVIEW_ONLY');
 assert.equal(candidate.geometry_ref,'fixture:geo');
 assert.equal(candidate.geometry_display_mode,'NONMETRIC_SOURCE_REVIEW');
 assert.equal(candidate.metric_geometry_verified,false);
 assert.equal(candidate.physical_world_coordinates_exportable,false);
 assert.equal(candidate.scientific_authority,'HOLD_UNVERIFIED');
 assert.equal(candidate.rendered,false);
 assert.equal(candidate.public_release,false);
 // A bound but non-permitted source remains unavailable.
 const withheld=spread({nodes:bound,access:{...access,authorized_source_ids:['fixture:s1']}});
 assert.equal(withheld.objects[0].geometry,null);
 assert.equal(planViewportSwitch({spread:withheld,to:'3d'}).state,'FRONTIER_GEOMETRY_UNQUALIFIED');
});
test('3D requires permitted native geometry and units/coordinate frame',()=>{
 const changed=nodes.map(n=>n.object_id==='fixture:eco:tree'?{...n,geometry:{source_ref:'fixture:hidden',units:null,frame:null}}:n);
 const a=spread({nodes:changed});assert.equal(planViewportSwitch({spread:a,to:'3d'}).state,'FRONTIER_GEOMETRY_UNQUALIFIED');
});
test('model chat and interactive mode never imply execution',()=>{
 const a=spread();
 assert.equal(planViewportSwitch({spread:a,to:'interactive'}).interactive_execution,false);
 assert.match(planViewportSwitch({spread:a,to:'chat'}).requirements.join(' '),/model\/provider/);
});
test('no authorised focus is denied',()=>assert.equal(planKnowledgeSpread({nodes,focus_id:'fixture:eco:secret',access}).status,'DENIED'));
test('missing ACL is rejected',()=>assert.throws(()=>planKnowledgeSpread({nodes,focus_id:'fixture:eco:tree',access:{}}),/EXPLICIT_AUTHORIZATION_REQUIRED/));
test('duplicate Object_ID is rejected, not merged',()=>assert.throws(()=>spread({nodes:[...nodes,nodes[0]]}),/COLLIDING_GRAPH_ID/));
test('invalid or excessive bandwidth budget is rejected',()=>assert.throws(()=>spread({budgets:{max_nodes:999999}}),/BUDGET_EXCEEDED/));
test('novel source is only a candidate even on identical source checksum',()=>{
 const source=registry.records.find(r=>r.category==='conversion_source'&&r.owner_domain==='romer');
 const p=planNovelMatching(registry,{domain:'romer',source_hash:source.source_sha256});
 assert.equal(p.status,'SOURCE_IDENTITY_CANDIDATE');assert.equal(p.created_object_ids,0);assert.equal(p.native_admission,false);
});
test('unmatched novel source becomes Frontier without object invention',()=>{
 const p=planNovelMatching(registry,{domain:'eco',source_name:'fixture:unseen'});
 assert.equal(p.status,'FRONTIER_NEW');assert.equal(p.verified_object_id,null);
});
test('novel matching rejects forged registry source provenance',()=>{
 const forged=JSON.parse(JSON.stringify(registry));
 const source=forged.records.find(r=>r.category==='conversion_source');
 source.source_git_blob='0'.repeat(40);
 assert.throws(()=>planNovelMatching(forged,{domain:source.owner_domain,source_hash:source.source_sha256}),/SOURCE_PROOF_MISMATCH/);
});
test('novel matching rejects false native acceptance claims',()=>{
 const forged=JSON.parse(JSON.stringify(registry));forged.summary.native_accepted=1;
 assert.throws(()=>planNovelMatching(forged,{domain:'romer',source_name:'fixture'}),/UNSUPPORTED_AUTHORITY_CLAIM/);
});
test('provider ID and checksum disagreement is a Frontier identity conflict, not an OR match',()=>{
 const source=registry.records.find(r=>r.category==='conversion_source'&&r.source_drive_id&&r.source_sha256);
 assert.ok(source);
 const p=planNovelMatching(registry,{domain:source.owner_domain,source_id:source.source_drive_id,source_hash:'f'.repeat(64)});
 assert.equal(p.status,'SOURCE_IDENTITY_CONFLICT');
 assert.deepEqual(p.source_matches,[]);
 assert.ok(p.conflict_mapping_ids.includes(source.source_key));
 assert.equal(p.verified_object_id,null);
 assert.equal(p.native_admission,false);
});
test('concordant provider ID and checksum remain source-only candidates',()=>{
 const source=registry.records.find(r=>r.category==='conversion_source'&&r.source_drive_id&&r.source_sha256);
 const p=planNovelMatching(registry,{domain:source.owner_domain,source_id:source.source_drive_id,source_hash:source.source_sha256});
 assert.equal(p.status,'SOURCE_IDENTITY_CANDIDATE');
 assert.equal(p.native_admission,false);
});
test('unknown view is rejected',()=>assert.throws(()=>planViewportSwitch({spread:spread(),to:'teleport'}),/UNKNOWN_VIEW/));
test('all projections remain non-mutating and no implicit network hydration occurs',()=>{
 const a=spread();const b=planViewportSwitch({spread:a,to:'3d'});
 assert.equal(a.network_fetch,false);assert.equal(a.canonical_mutation,false);assert.equal(b.network_fetch,false);assert.equal(b.public_release,false);
});


test('scientific 3D caller proof and ephemeris claims cannot elevate source-linked geometry (#209)',()=>{
 const forged=nodes.map(n=>n.object_id==='fixture:eco:tree'?{
  ...n,source_refs:['fixture:s1','fixture:geo'],proof_class:'scientific',
  evidence_ceiling:'NATIVE_VERIFIED',native_admitted:true,host_handshake_verified:true,
  geometry:{source_ref:'fixture:geo',frame:'ICRF',units:'AU',
   epoch:'2025-06-04T12:00:00Z',time_scale:'TDB',origin:'SOLAR_SYSTEM_BARYCENTER',
   physical_scale:true,verified:true,ephemeris:'HORIZONS',native_dbr_verified:true}
 }:n);
 const s=spread({nodes:forged});
 const v=planViewportSwitch({spread:s,to:'3d'});
 assert.equal(v.state,'SOURCE_LINKED_3D_REVIEW_ONLY');
 assert.equal(v.geometry_ref,'fixture:geo');
 assert.equal(v.metric_geometry_verified,false);
 assert.equal(v.physical_world_coordinates_exportable,false);
 assert.equal(v.native_admitted,false);
 assert.equal(v.host_handshake_verified,false);
 assert.equal(v.rendered,false);
 assert.equal(v.public_release,false);
 assert.equal(v.metric_scale,null);
 assert.equal(v.artistic_glyph_scale,null);
 assert.equal(v.camera_transform,null);
 assert.match(v.requirements.join(' '),/time-scale/);
 assert.match(v.requirements.join(' '),/glyph/);
 assert.ok(!JSON.stringify(v).includes('HORIZONS'));
});

test('creative source-linked 3D is still nonmetric and not native/owner accepted',()=>{
 const creative=nodes.map(n=>n.object_id==='fixture:eco:tree'?{
  ...n,proof_class:'creative',source_refs:['fixture:s1','fixture:geo'],
  geometry:{source_ref:'fixture:geo',frame:'fictional-local',units:'m',
   source_verified:true,rights_verified:true}
 }:n);
 const v=planViewportSwitch({spread:spread({nodes:creative}),to:'3d'});
 assert.equal(v.state,'SOURCE_LINKED_3D_REVIEW_ONLY');
 assert.equal(v.geometry_display_mode,'NONMETRIC_SOURCE_REVIEW');
 assert.equal(v.scientific_authority,'HOLD_UNVERIFIED');
 assert.equal(v.metric_geometry_verified,false);
 assert.equal(v.interactive_execution,false);
 assert.equal(v.public_release,false);
});
