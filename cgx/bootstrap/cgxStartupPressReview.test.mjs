import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {planStartupPressReview,buildHostStartupPressReceipt} from './cgxStartupPressReview.mjs';
import {planFirstSpacesReview} from '../../apps/lightspeed-go/src/cgxFirstSpacesReviewModel.mjs';
const contract=JSON.parse(readFileSync(new URL('../domain_templates/achilles_file_space_launch_review_contract.json',import.meta.url)));
test('existing first-space contract creates a single parent, one LOAD alias and dependency-pinned mint candidates',()=>{
 const p=planStartupPressReview({contract});
 assert.equal(p.state,'STARTUP_SOURCE_REVIEW_READY_NOT_NATIVE');
 assert.equal(p.canonical_parent,'cgx:root:cognigrex');
 assert.equal(p.resolver,'LOAD.cgx');
 assert.equal(p.bootstrap_family_count,5);
 assert.equal(p.lattice.nodes.length,12);
 const social=p.lattice.nodes.find(x=>x.key==='space.socialspace');
 assert.equal(social?.parent,'space.filespace');
 assert.equal(social?.profile_mint_authorized,false);
 assert.equal(p.press.candidates.length,11);
 assert.equal(p.press.canonical_type_candidates,6);
 assert.equal(p.first_spaces.length,4);
 assert.equal(p.first_spaces[0].id,'file_space');
 assert.equal(p.first_spaces[3].id,'print_space');
 assert.equal(p.lattice.nodes.filter(x=>x.kind==='canonical-parent').length,1);
 assert.equal(p.lattice.nodes.filter(x=>x.key==='facet.load').length,1);
 assert.ok(p.lattice.edges.some(e=>e.from==='family.emassc'&&e.to==='family.ls'));
 assert.equal(p.native_minted,false);
 assert.equal(p.signed,false);
 assert.equal(p.deployed,false);
 assert.equal(p.source_deleted,false);
 assert.equal(p.press.native_mint_intents_created,0);
});
test('visual rearrangement and concept approval never change lattice dependencies or mint sequencing',()=>{
 const initial=planFirstSpacesReview();
 const reversed=[...initial.order].reverse();
 const rearranged=planStartupPressReview({contract,layout:'space-grid',order:reversed,
  decisions:{'family.eco':'approve','space.dataspace':'defer'}});
 assert.equal(rearranged.state,'STARTUP_SOURCE_REVIEW_READY_NOT_NATIVE');
 assert.deepEqual(rearranged.lattice.visual_order,reversed);
 assert.deepEqual(rearranged.press.candidates.map(x=>x.candidate_key),initial.mint_sequence);
 const candidate=rearranged.press.candidates.find(x=>x.candidate_key==='family.eco');
 assert.equal(candidate.design_review_state,'DESIGN_APPROVED_ONLY');
 assert.equal(candidate.founder_signoff_verified,false);
 assert.equal(candidate.eligible_for_native_mint,false);
 assert.equal(candidate.actual_minted,false);
 assert.equal(rearranged.native_minted,false);
});
test('fraudulent layout, unknown family and duplicate keys fail closed',()=>{
 const init=planFirstSpacesReview();
 for(const opts of [
  {order:init.order.slice(1)},
  {order:[...init.order.slice(0,-1),init.order[0]]},
  {layout:'signed'},
  {focus:'cgx:root:cognigrex'},
  {decisions:{'facet.load':'mint-now'}},
  {decisions:{'unknown-node':'approve'}}
 ])assert.equal(planStartupPressReview({contract,...opts}).state,'HOLD');
});
test('source contract cannot claim minted parent or reorder established first-space phases',()=>{
 assert.equal(planStartupPressReview({contract:{...contract,canonical_objects_minted:1}}).state,'HOLD');
 assert.equal(planStartupPressReview({contract:{...contract,state:'NATIVE_MINTED'}}).state,'HOLD');
 const flipped={...contract,phase_order:[...contract.phase_order].reverse()};
 assert.equal(planStartupPressReview({contract:flipped}).state,'HOLD');
 const forged=JSON.parse(JSON.stringify(contract));
 forged.phase_order[1].dependency=['UNVERIFIED_ALREADY_DONE'];
 assert.equal(planStartupPressReview({contract:forged}).state,'HOLD');
});
test('actual host index readback contains source hash, native holds and no signed mint',()=>{
 const p=buildHostStartupPressReceipt();
 assert.equal(p.state,'STARTUP_SOURCE_REVIEW_READY_NOT_NATIVE');
 assert.match(p.source_contract.sha256,/^[0-9a-f]{64}$/);
 assert.match(p.source_contract.git_head,/^[0-9a-f]{40}$/);
 assert.equal(p.source_contract.indexed_git_blob_verified,true);
 assert.equal(p.approval_gates.signed_issuer,'HOLD');
 assert.equal(p.approval_gates.independent_two_node_dbr,'HOLD');
 assert.equal(p.press.native_mint_intents_created,0);
});
