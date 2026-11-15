import test from 'node:test';
import assert from 'node:assert/strict';
import {buildReviewEnvelope,verifyEnvelope,planHydration,verifyLeaf,verifyReconstruction,MAX_WORK_UNIT_BYTES} from './cgxLeafEnvelopeReview.mjs';
const sample=()=>buildReviewEnvelope({objectId:'cgx:LOAD:sample',version:'v1',
 leaves:[Buffer.from('hello '),Buffer.from('world')],rightsRef:'private:source-rights',aclRef:'private:acl'});
const goodProof={rightsVerified:true,aclVerified:true,sourceHashCurrent:true};
test('deterministic content-addressed source skeleton and reversible two-leaf bytes',()=>{
 const a=sample(),b=sample();
 assert.equal(a.state,'REVIEW_ONLY');assert.equal(a.digest_sha256,b.digest_sha256);
 assert.equal(verifyEnvelope(a),true);
 assert.equal(verifyReconstruction(a,[Buffer.from('hello '),Buffer.from('world')]),true);
 assert.equal(a.native_mint,false);assert.equal(a.network_transfer,false);
});
test('source mutations invalidate leaf or exact reconstructed source',()=>{
 const a=sample();
 assert.equal(verifyLeaf(a,1,Buffer.from('World')),false);
 assert.equal(verifyReconstruction(a,[Buffer.from('hello '),Buffer.from('World')]),false);
 assert.equal(verifyReconstruction(a,[Buffer.from('hello ')]),false);
});
test('permissioned selective hydration returns a non-executing request plan',()=>{
 const a=sample(),p=planHydration(a,[1],goodProof);
 assert.equal(p.state,'REQUEST_PLAN_ONLY');assert.equal(p.requested_bytes,5);
 assert.deepEqual(p.selected_leaves.map(x=>x.index),[1]);
 assert.equal(p.network_transfer,false);assert.equal(p.native_mint,false);
});
test('rights, ACL and source proof are independent holds even with review references',()=>{
 const a=sample();
 for(const key of Object.keys(goodProof)){
  const p=planHydration(a,[0],{...goodProof,[key]:false});
  assert.equal(p.state,'HOLD',key);assert.equal(p.network_transfer,false);
 }
});
test('duplicate or unknown requested leaves fail closed',()=>{
 const a=sample();
 assert.equal(planHydration(a,[0,0],goodProof).reason,'LEAF_REQUEST_DUPLICATE');
 assert.equal(planHydration(a,[5],goodProof).reason,'LEAF_REQUEST_INVALID');
 assert.equal(planHydration(a,['0'],goodProof).reason,'LEAF_REQUEST_INVALID');
});
test('unqualified or self-referencing dependencies cannot be staged',()=>{
 const a=sample();
 assert.equal(buildReviewEnvelope({objectId:'cgx:LOAD:sample',version:'v1',leaves:[Buffer.from('x')],
  dependencies:[{objectId:'cgx:a',version:'v1'}]}).reason,'DEPENDENCY_REQUIRES_EXACT_VERSION_AND_DIGEST');
 assert.equal(buildReviewEnvelope({objectId:'cgx:LOAD:sample',version:'v1',leaves:[Buffer.from('x')],
  dependencies:[{objectId:'cgx:LOAD:sample',version:'v1',manifestSha256:'0'.repeat(64)}]}).reason,'SELF_DEPENDENCY');
});
test('duplicate dependencies held and order-independent digest',()=>{
 const x={objectId:'cgx:a',version:'v1',manifestSha256:'1'.repeat(64)};
 const y={objectId:'cgx:b',version:'v2',manifestSha256:'2'.repeat(64)};
 const cfg={objectId:'cgx:LOAD:c',version:'v1',leaves:[Buffer.from('x')]};
 assert.equal(buildReviewEnvelope({...cfg,dependencies:[x,x]}).reason,'DUPLICATE_DEPENDENCY');
 assert.equal(buildReviewEnvelope({...cfg,dependencies:[x,y]}).digest_sha256,
   buildReviewEnvelope({...cfg,dependencies:[y,x]}).digest_sha256);
});
test('unverified identifiers and path-like fragments are denied',()=>{
 const c={version:'v1',leaves:[Buffer.from('x')]};
 for(const objectId of ['../secret','a\\b','',null])
  assert.equal(buildReviewEnvelope({...c,objectId}).state,'DENIED');
});
test('work unit larger than 60MiB denied before any transport',()=>{
 const p=buildReviewEnvelope({objectId:'cgx:test',version:'v1',
  leaves:[Buffer.alloc(MAX_WORK_UNIT_BYTES+1)]});
 assert.equal(p.reason,'SOURCE_WORK_UNIT_TOO_LARGE');
});
test('manifest hash tampering denied including missing source or malformed leaves',()=>{
 const a=sample();a.manifest.source.sha256='0'.repeat(64);
 assert.equal(verifyEnvelope(a),false);
 const b=sample();delete b.manifest.source;
 assert.equal(verifyEnvelope(b),false);
 const c=sample();c.manifest.leaves=[null];
 assert.equal(verifyEnvelope(c),false);
});
test('even a caller-provided positive proof never grants actual transport or signing',()=>{
 const p=planHydration(sample(),[0,1],goodProof);
 assert.equal(p.state,'REQUEST_PLAN_ONLY');assert.equal(p.network_transfer,false);
 assert.equal(p.canonical_mutation,false);
 assert.match(p.note,/not authenticated/i);
});
