import test from 'node:test';
import assert from 'node:assert/strict';
import {convergeCGXBatch,renderBatchReviewHTML,SCHEMA} from './cgxBatchConvergence.mjs';
const hash=x=>x.repeat(64);
const src=(source_id,revision,sha,semantic_key='shared:sort',overrides={})=>({source_id,revision,sha256:hash(sha),semantic_key,owner:'achilles',family:'EMASSC.cgx',rights:'internal_only',acl:'owner_only',abi:'read:json:1',...overrides});
const phases=[{id:'file_space',ordinal:1,dependency:[],may_self_mint:false},{id:'unispace_file_space_control',ordinal:2,dependency:['file_space:ACCEPTED'],may_self_mint:false},{id:'data_space',ordinal:3,dependency:['file_space:LANDED_AND_ACCEPTED','unispace_file_space_control:TESTED'],may_self_mint:false},{id:'print_space',ordinal:4,dependency:['data_space:TESTED'],may_self_mint:false}];
const base=()=>({parent:'cgx:root:cognigrex',sources:[src('cgx:a','10','a'),src('cgx:a','2','b'),src('cgx:b','1','c')],capabilities:[{capability_id:'cgx:render:review',source_id:'cgx:a',owner:'achilles',kind:'view',abi:'read:json:1'}],phases,aliases:[{alias:'cgx:old-a',target:'cgx:a'}],transferred_bytes:0});
test('whole-framework convergence, deterministic numeric source order, no activation, print-review',()=>{
 const a=convergeCGXBatch(base());const b=convergeCGXBatch({...base(),sources:base().sources.reverse()});
 assert.equal(a.schema,SCHEMA);assert.deepEqual(a,b);assert.deepEqual(a.source_records.map(s=>s.source_id+'@'+s.revision),['cgx:a@2','cgx:a@10','cgx:b@1']);
 assert.deepEqual(a.phases.map(p=>p.id),['file_space','unispace_file_space_control','data_space','print_space']);
 assert.ok(a.blockers.some(x=>x.startsWith('UNRESOLVED_PHASE_GATE_GRAMMAR:file_space:')));
 assert.equal(a.overlaps.filter(x=>x.kind==='SEMANTIC_OVERLAP_REVIEW_ONLY').length,1);
 for(const k of ['native_admitted','may_mint','may_dispatch','may_publish','may_print','may_transact'])assert.equal(a[k],false);
 const html=renderBatchReviewHTML(a);assert.match(html,/Batch Convergence/);assert.match(html,/Print & Mint Review/);assert.match(html,/Release: HOLD/);assert.doesNotMatch(html,/<script|<iframe|https?:\/\//);
});
test('duplicate identical source occurrence is retained, not silently deleted',()=>{
 const x=base();x.sources.push({...x.sources[0]});const a=convergeCGXBatch(x);
 assert.equal(a.source_records.length,4);assert.ok(a.overlaps.some(k=>k.kind==='SAME_VERSION_REPEATED_REFERENCE'));
});
test('same identity and revision but differing hash/rights/owner is a collision, preserving hypotheses',()=>{
 const x=base();x.sources.push(src('cgx:a','2','d','shared:sort',{rights:'public_clear',acl:'public'}));
 const a=convergeCGXBatch(x);assert.ok(a.blockers.includes('IDENTITY_VERSION_COLLISION:cgx:a@2'));
 assert.equal(a.source_records.filter(x=>x.source_id==='cgx:a'&&x.revision==='2').length,2);
});
test('ABI variants do not silently imply one callable source or equivalent functions',()=>{
 const x=base();x.sources.push(src('cgx:c','1','d','shared:sort',{abi:'write:asset:1'}));
 const a=convergeCGXBatch(x);assert.ok(a.overlaps.some(x=>x.kind==='SEMANTIC_OVERLAP_REVIEW_ONLY'&&x.abi_variants===2));assert.equal(a.may_dispatch,false);
});
test('unknown rights, public exposure conflict and unauthorized capability are held',()=>{
 const x=base();x.sources.push(src('cgx:c','1','d','unique',{rights:'unknown',acl:'unknown'}),src('cgx:d','1','e','unique2',{rights:'restricted',acl:'public'}));x.capabilities.push({capability_id:'cgx:bad:tool',source_id:'cgx:missing',owner:'achilles',kind:'tool',abi:'execute:1'});
 const a=convergeCGXBatch(x);assert.ok(a.blockers.some(s=>s.startsWith('UNCLASSIFIED_RIGHTS_OR_ACL')));assert.ok(a.blockers.some(s=>s.startsWith('RIGHTS_ACL_CONFLICT')));assert.ok(a.blockers.some(s=>s.startsWith('CAPABILITY_SOURCE_UNRESOLVED')));
});
test('alias shadow, cycles, unresolved target and conflicting aliases deny without deleting originals',()=>{
 const x=base();x.aliases.push({alias:'cgx:b',target:'cgx:a'},{alias:'cgx:loop1',target:'cgx:loop2'},{alias:'cgx:loop2',target:'cgx:loop1'},{alias:'cgx:unresolved',target:'cgx:missing'},{alias:'cgx:old-a',target:'cgx:b'});
 const a=convergeCGXBatch(x);for(const k of ['ALIAS_SHADOWS_SOURCE_ID','ALIAS_CYCLE','ALIAS_TARGET_UNQUALIFIED','ALIAS_COLLISION'])assert.ok(a.blockers.some(s=>s.startsWith(k)),k);
});
test('invalid identity, syntax and oversized transfer fail before any work',()=>{
 for(const change of [x=>x.sources[0].sha256='INVALID',x=>x.sources[0].source_id='../escape',x=>x.sources[0].revision='-1',x=>x.sources[0].family='OtherRoot',x=>x.sources[0].acl='world',x=>x.transferred_bytes=60*1024*1024+1,x=>x.parent='cgx:other:root']){
  const x=base();change(x);const a=convergeCGXBatch(x);assert.equal(a.state,'DENIED_INVALID_REVIEW_INPUT');assert.equal(a.may_mint,false);
 }
});
test('DAG detects missing dependencies, self-mint and backward edges',()=>{
 const x=base();x.phases=x.phases.map(v=>({...v,dependency:[...v.dependency]}));x.phases[0].dependency=['data_space:TESTED'];x.phases[3].dependency=['unknown:TESTED'];
 const a=convergeCGXBatch(x);assert.ok(a.blockers.some(s=>s.startsWith('PHASE_BACKEDGE')));assert.ok(a.blockers.some(s=>s.startsWith('UNKNOWN_PHASE_DEPENDENCY')));
 x.phases[0].may_self_mint=true;assert.equal(convergeCGXBatch(x).state,'DENIED_INVALID_REVIEW_INPUT');
});
test('owner mismatch and duplicate callable IDs cannot upgrade into authority',()=>{
 const x=base();x.capabilities.push({capability_id:'cgx:render:review',source_id:'cgx:b',owner:'neo',kind:'tool',abi:'exec:1'});
 const a=convergeCGXBatch(x);assert.ok(a.blockers.some(s=>s.startsWith('CAPABILITY_OWNER_MISMATCH')));assert.ok(a.blockers.some(s=>s.startsWith('DUPLICATE_CAPABILITY_ID')));assert.equal(a.may_dispatch,false);
});
test('a zero-discrepancy assembly still cannot mint, publish or transact',()=>{
 const x=base();x.phases=x.phases.map(p=>({...p,dependency:p.dependency.map(d=>d==='file_space:LANDED_AND_ACCEPTED'?'file_space:ACCEPTED':d)}));
 const a=convergeCGXBatch(x);assert.equal(a.blockers.length,0);assert.equal(a.state,'BATCH_REVIEW_ASSEMBLED');assert.equal(a.native_admitted,false);assert.equal(a.may_publish,false);
});
test('print-review safely escapes provenance labels',()=>{
 const x=base();x.phases=x.phases.map(p=>({...p,dependency:[...p.dependency]}));const report=convergeCGXBatch(x);report.blockers.push('<img src=x onerror=alert(1)>');
 const html=renderBatchReviewHTML(report);assert.match(html,/&lt;img/);assert.doesNotMatch(html,/<img/);
 assert.throws(()=>renderBatchReviewHTML({}),/UNVERIFIED/);
});
