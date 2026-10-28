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
test('unknown view is rejected',()=>assert.throws(()=>planViewportSwitch({spread:spread(),to:'teleport'}),/UNKNOWN_VIEW/));
test('all projections remain non-mutating and no implicit network hydration occurs',()=>{
 const a=spread();const b=planViewportSwitch({spread:a,to:'3d'});
 assert.equal(a.network_fetch,false);assert.equal(a.canonical_mutation,false);assert.equal(b.network_fetch,false);assert.equal(b.public_release,false);
});
