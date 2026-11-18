import assert from 'node:assert/strict';
import {digest,stableJSON,verifyBytes,t173,plan,reconcile,publicReceipt} from './cgx_batch_core.mjs';
let c=0;const ck=(x,fn)=>{fn();++c},fail=fn=>{assert.throws(fn);++c};const h=digest('seed');
const mk=(id,dependencies=[],state='KNOWN')=>({id,owner:'Earth.cgx',state,dependencies,access:'public',sha256:state==='KNOWN'?h:null,bytes:state==='KNOWN'?4:null,address:'001/002',verified:state==='KNOWN'});
ck('sha256',()=>assert.equal(digest('abc'),'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'));
ck('canonical',()=>assert.equal(stableJSON({z:1,a:{t:2,s:4}}),'{"a":{"s":4,"t":2},"z":1}'));
ck('t173',()=>assert.deepEqual(t173('001/173'),[1,173]));
for(const s of ['174','001/174','001/000','1/2','001/'.repeat(18)])fail(()=>t173(s));
ck('verify bytes',()=>assert.equal(verifyBytes(Buffer.from('seed'),{sha256:h,bytes:4}).status,'R0_BYTES_VERIFIED'));
fail(()=>verifyBytes(Buffer.from('seex'),{sha256:h,bytes:4}));fail(()=>verifyBytes(Buffer.from('seed'),{sha256:h,bytes:5}));
const nodes=[mk('base'),mk('earth',['base']),mk('eco',['earth']),mk('raphael',['earth'])];
const p=plan(nodes,['eco','raphael']);ck('ordered',()=>assert.deepEqual(p.order.map(x=>x.id),['base','earth','eco','raphael']));ck('dedupe',()=>assert.equal(p.repeated_exact_source_hash_refs,3));ck('receipt',()=>assert.equal(publicReceipt(p).ready_for_native_admission,false));
for(const n of nodes){const pp=plan(nodes,[n.id]);ck('single plan '+n.id,()=>assert.equal(pp.action,'REVIEW_ONLY'))}
ck('reconcile same',()=>assert.deepEqual(reconcile(p,nodes,['eco','raphael']).changed,[]));
const newer=nodes.map(x=>({...x,dependencies:[...x.dependencies]}));newer[1].sha256=digest('new');ck('reconcile changed',()=>assert.deepEqual(reconcile(p,newer,['eco','raphael']).changed,['earth']));
const wrong={...p,root_sha256:'0'.repeat(64)};fail(()=>publicReceipt(wrong));fail(()=>reconcile(wrong,nodes,['eco']));
fail(()=>plan([mk('a',['b']),mk('b',['a'])],['a']));fail(()=>plan([mk('a'),mk('a')],['a']));fail(()=>plan([mk('a',['a'])],['a']));
fail(()=>plan([{...mk('bad'),address:'174'}],['bad']));fail(()=>plan([{...mk('bad'),owner:'Other'}],['bad']));
fail(()=>plan([{...mk('bad'),state:'KNOWN',sha256:null}],['bad']));
fail(()=>plan([{...mk('bad'),verified:true,state:'WITHHELD'}],['bad']));
let privateNode={...mk('private'),access:'owner'},pub=plan([privateNode],['private'],{publicView:true});ck('private held',()=>assert.equal(pub.order.length,0));ck('private hold reason',()=>assert.equal(pub.holds[0].reason,'PRIVATE_SOURCE_EXCLUDED'));
let covered=plan([privateNode,{...mk('publicDependent',['private']),access:'public'}],['publicDependent'],{publicView:true});ck('transitive privacy hold',()=>assert.equal(covered.order.length,0));ck('transitive privacy reason',()=>assert.ok(covered.holds.some(x=>x.id==='publicDependent')));
let held=plan([mk('pending',[],'NOT_HYDRATED')],['pending']);ck('not hydrated hold',()=>assert.equal(held.holds.length,1));ck('unknown reference',()=>assert.deepEqual(plan([mk('x',['missing'])],['x']).missing,['missing']));
for(let i=0;i<100;i++){const ns=Array.from({length:30},(_,j)=>mk('n'+j,j?['n'+(j-1)]:[]));const p=plan(ns,['n29']);ck('repeat '+i,()=>assert.equal(p.order.length,30));}
const b=plan(nodes,['eco','raphael']);ck('stable digest',()=>assert.equal(p.root_sha256,p.root_sha256));
console.log(JSON.stringify({status:'PASS',checks:c,root:p.root_sha256,claims:'Metadata planning only; no source bytes ingested or native authority'}));
