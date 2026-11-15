import {test} from 'vitest';
import assert from 'node:assert/strict';
import {importLoadIndex,buildBatchDraft,restoreBatchDraft,canonical,digest} from './cgxLoadBatchDraft.mjs';
const record=i=>({review_ref:'cgx.review://cognigrex/load/'+String(i).padStart(64,'0'),
 pointer_sha256:String(i).padStart(64,'0'),name:'Source '+i,locator:'https://example.org/'+i,
 source_sha256:i===1?'a'.repeat(64):null,rights_status:'UNREVIEWED',routes:['Cognigrex_Family'],
 native_mint:false,rights_approved:false});
const source=()=>({schema:'CGX-ONE-LOAD-INTAKE/0.17',parent:'Cognigrex.cgx',child:'LOAD.cgx',native_mint:false,
 records:Array.from({length:27},(_,i)=>record(i+1))});
test('existing LOAD reference index folds deterministically into sequential unsigned batches',async()=>{
 const bytes=JSON.stringify(source());const index=await importLoadIndex(bytes);
 assert.equal(index.raw_index_sha256,await digest(bytes));
 const plan=await buildBatchDraft(index);assert.equal(plan.batches.length,2);assert.equal(plan.batches[0].entries.length,25);
 assert.equal(plan.batches[1].depends_on,plan.batches[0].batch_sha256);
 assert.equal(plan.summary.mint_ready_records,0);assert.equal(plan.summary.source_digest_present,1);
 assert.equal(plan.launch_binding.signature,null);assert.equal(plan.launch_binding.chain_id,null);
 for(const flag of Object.values(plan.execution_policy))assert.equal(flag,false);
 assert.deepEqual(await restoreBatchDraft(JSON.stringify(plan)),{draft:plan,index});
 const reversed={...index,records:[...index.records].reverse()};assert.equal((await buildBatchDraft(reversed)).plan_sha256,plan.plan_sha256);
});
test('source BOM and bytes are hashed exactly; no inferred native identity or source version',async()=>{
 const bytes=new TextEncoder().encode('\uFEFF'+JSON.stringify(source()));const i=await importLoadIndex(bytes);
 assert.equal(i.raw_index_sha256,await digest(bytes));const p=await buildBatchDraft(i,{selectedRefs:[i.records[0].review_ref]});
 assert.equal(p.batches[0].entries[0].source_version,null);assert.equal(p.batches[0].entries[0].native_object_id,null);
});
test('existing R0 receipt locator is preserved as an unresolved claim rather than a hash',async()=>{
 const s=source();s.records[0].source_sha256='R0_SHARD_HASH_IN_ORIGINAL_RECEIPT';
 const index=await importLoadIndex(JSON.stringify(s));const plan=await buildBatchDraft(index);
 assert.equal(index.records[0].source_sha256,null);
 assert.equal(index.records[0].source_digest_claim,'R0_SHARD_HASH_IN_ORIGINAL_RECEIPT');
 assert.equal(plan.summary.source_digest_present,0);
 assert.ok(plan.batches[0].entries[0].qualification_holds.includes('R0_BYTES_NOT_HASH_QUALIFIED'));
 await restoreBatchDraft(JSON.stringify(plan));
});
test('wrong root, duplicate refs, foreign routes and forged index authority are rejected',async()=>{
 const bad=[];let x=source();x.parent='Other.cgx';bad.push(x);
 x=source();x.records.push(x.records[0]);bad.push(x);
 x=source();x.records[0].native_mint=true;bad.push(x);
 x=source();x.records[0].rights_approved=true;bad.push(x);
 x=source();x.records[0].routes=['unknown'];bad.push(x);
 x=source();x.records[0].source_sha256='fake';bad.push(x);
 for(const value of bad)await assert.rejects(()=>importLoadIndex(JSON.stringify(value)));
});
test('unknown selection, oversized source and invalid batch limits fail closed',async()=>{
 const index=await importLoadIndex(JSON.stringify(source()));
 for(const options of [{selectedRefs:[]},{selectedRefs:['foreign']},{batchSize:0},{batchSize:101},{batchSize:NaN}])await assert.rejects(()=>buildBatchDraft(index,options));
 await assert.rejects(()=>importLoadIndex('x'.repeat(8*1024*1024+1)));
});
test('edited policy, rights, membership and even rehashed signing claims cannot restore',async()=>{
 const plan=await buildBatchDraft(await importLoadIndex(JSON.stringify(source())));
 const mutations=[p=>{p.execution_policy.broadcast=true;},p=>{p.launch_binding.chain_id=1;},
  p=>{p.summary.mint_ready_records=27;},p=>{p.batches[0].entries.pop();},
  p=>{p.source_records[0].rights_approved=true;},p=>{p.extra_approval='owner';}];
 for(const mutate of mutations){const p=structuredClone(plan);mutate(p);
  const {plan_sha256,...body}=p;p.plan_sha256=await digest(canonical(body));
  await assert.rejects(()=>restoreBatchDraft(JSON.stringify(p)));
 }
});
