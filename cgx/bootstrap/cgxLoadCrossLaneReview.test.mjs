import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {stageFamilyPacket,projectUniSpace} from './cgxPremintFamilyProjection.mjs';
import {verifyReconstruction} from './cgxLeafEnvelopeReview.mjs';
import {validateRegistry,resolveLoad,searchLoad} from '../load_minimum/loadOnlineRegistry.mjs';
const loadCatalog=JSON.parse(readFileSync(new URL('../load_minimum/online_registry_projection_2026-10-28.json',import.meta.url),'utf8'));
const source=readFileSync(new URL('../load_minimum/activation_contract.json',import.meta.url));
function stage(){
 return stageFamilyPacket({objectId:'cgx:load:activation-contract',version:'1',
  originalLeaves:[source],family:'Cognigrex.cgx',owner:'achilles',
  semanticKey:'load:activation-contract',rights:'unknown',acl:'unknown'});
}
test('one LOAD registry reused by bootstrap, 131 references and 45 CCC routes stay uninstalled',()=>{
 const result=validateRegistry(loadCatalog);
 assert.equal(result.reference_count,131);
 assert.equal(searchLoad(loadCatalog,{category:'ccc_route',limit:100}).total,45);
 const plan=resolveLoad(loadCatalog,{category:'format_adapter',sourceKey:'json-stdlib-v0.1'});
 assert.equal(plan.status,'REFERENCE_ONLY');
 assert.equal(plan.install_executed,false);
});
test('existing LOAD activation source is content-bound into single parent and reversible',()=>{
 const p=stage();
 assert.equal(p.state,'REVIEW_WITH_HOLDS');
 assert.equal(p.canonical_parent,'cgx:root:cognigrex');
 assert.equal(p.library,'LOAD.cgx');
 assert.equal(p.envelope.manifest.source.sha256,createHash('sha256').update(source).digest('hex'));
 assert.equal(verifyReconstruction(p.envelope,[source]),true);
 assert.equal(p.convergence.metrics.unique_source_ids,1);
 assert.equal(p.convergence.native_admitted,false);
});
test('UniSpace private H0-H4 is a source preview, public and execution remain held',()=>{
 const p=stage();
 const v=projectUniSpace(p,{audience:'owner',requestedLeaves:[0]});
 assert.equal(v.h0.object_id,'cgx:load:activation-contract');
 assert.equal(v.h2.evidence_stage,'REVIEW_ONLY');
 assert.equal(v.h2.source_qualified,false);
 assert.equal(v.h4.execution,'DISABLED_AUTHORITY_HOLD');
 assert.equal(v.hydration.state,'HOLD');
 assert.equal(v.network_transfer,false);
 assert.equal(projectUniSpace(p,{audience:'public'}).state,'HOLD');
 assert.equal(p.may_mint,false);
});
