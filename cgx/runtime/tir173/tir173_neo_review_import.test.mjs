import test from 'node:test';
import assert from 'node:assert/strict';
import {reviewLocalNeoBatch} from './tir173_neo_review_import.mjs';

const SH='a'.repeat(64);
function caseOf(input='SELECT T173:001',canonical=true){
 const op=canonical?'SELECT':null,role=canonical?'T173:001':null;
 return {
  machine:{
    schema:'cgx.neo.triad_review_preview/0.1',input,model_sha256:SH,
    learned_intent_candidate:canonical?null:'PLAN_TRANSFORM',
    candidate_cannot_override_guard:true,
    native_admitted:false,physical_claim_qualified:false,executed:false,
    LOAD_hydration:false,signed_DBR:false,model_routing_changed:false,authority:'REVIEW_ONLY',
    guard:{
      schema:'cgx.tir173.review_guard/0.1',
      status:canonical?'EXACT_CANONICAL_REVIEW_PLAN':'ABSTAIN_REVIEW_REQUIRED',
      intent:op,role,mode:canonical?'REVIEW_ONLY':undefined,
      reason:canonical?undefined:'NONCANONICAL_OR_AMBIGUOUS',
      native_admitted:false,command_executed:false,
      privileged_effects_authorised:false,LOAD_hydration_performed:false
    },
    three_analytic_facets:{
      intuitive:{trit:0,status:'UNQUALIFIED_LEARNED_INTENT'},
      deliberative:{trit:canonical?1:-1,status:canonical?'EXACT_TYPED_REVIEW_ONLY':'TYPED_RULE_ABSTAINS'},
      assurance:{trit:0,status:'UNRESOLVED_SOURCE_RIGHTS_SHAPE_AND_AUTHORITY'}
    }
  },
  human:{summary:'Review held; nothing executed',status:'NOT_EXECUTED'}
 };
}
const packet=(cases=[caseOf(),caseOf('rotate T173:001 by 90 degrees',false)])=>({
 schema:'cgx.neo.triad_review_batch/0.1',source_checkpoint_sha256:SH,
 human_machine_consistent:true,native_effects:0,tests:cases,
 canonical_exact_review_plans:cases.filter(x=>x.machine.guard.status==='EXACT_CANONICAL_REVIEW_PLAN').length,
 guarded_abstentions:cases.filter(x=>x.machine.guard.status==='ABSTAIN_REVIEW_REQUIRED').length
});
const copy=x=>structuredClone(x);
test('local-only synchronized preview accepts exact review and retains abstention',()=>{
 const reviewed=reviewLocalNeoBatch(packet());
 assert.equal(reviewed.total_cases,2);
 assert.equal(reviewed.exact_review_plans,1);
 assert.equal(reviewed.guarded_abstentions,1);
 assert.equal(reviewed.items[1].model_candidate,'PLAN_TRANSFORM');
 assert.equal(reviewed.items[1].status,'ABSTAIN_REVIEW_REQUIRED');
 assert.equal(reviewed.imported_packet_unverified,true);
 assert.equal(reviewed.model_weights_verified_by_browser,false);
 assert.ok(reviewed.items.every(x=>x.privileged_action===false));
});
test('native effect or claim of physical proof fails closed',()=>{
 for(const [name,value] of [
  ['native_admitted',true],['executed',true],['LOAD_hydration',true],['signed_DBR',true],
  ['model_routing_changed',true],['physical_claim_qualified',true]
 ]){const p=packet();p.tests[0].machine[name]=value;
    assert.throws(()=>reviewLocalNeoBatch(p),/NEO_PREVIEW_EFFECT_HOLD/,name);
 }
});
test('safety guard cannot be overridden by the model',()=>{
 const p=packet();p.tests[1].machine.candidate_cannot_override_guard=false;
 assert.throws(()=>reviewLocalNeoBatch(p),/NEO_PREVIEW_EFFECT_HOLD/);
});
test('invalid role, injected syntax, and extra effects cannot masquerade as canonical',()=>{
 for(const input of ['SELECT T173:174','SELECT T173:001; DROP TABLE items','SELECT T173:001 and mint']){
   const p=packet([caseOf(input,true)]);
   assert.throws(()=>reviewLocalNeoBatch(p),/NEO_CANONICAL_REVIEW_MISMATCH/);
 }
});
test('missing assurance and invalid trit fail closed',()=>{
 const p=packet();p.tests[0].machine.three_analytic_facets.assurance.status='VERIFIED';
 assert.throws(()=>reviewLocalNeoBatch(p),/NEO_ASSURANCE_MUST_HOLD/);
 const q=packet();q.tests[0].machine.three_analytic_facets.assurance.trit=2;
 assert.throws(()=>reviewLocalNeoBatch(q),/NEO_THREE_FACETS/);
});
test('negative must retain held state even with learned prediction',()=>{
 const p=packet();p.tests[1].machine.three_analytic_facets.deliberative.trit=1;
 assert.throws(()=>reviewLocalNeoBatch(p),/NEO_ABSTENTION_NOT_PRESERVED/);
});
test('reject changed model checksum, unregistered model output, and inconsistent counts',()=>{
 const p=packet();p.tests[0].machine.model_sha256='b'.repeat(64);
 assert.throws(()=>reviewLocalNeoBatch(p),/NEO_PREVIEW_EFFECT_HOLD/);
 const q=packet();q.tests[1].machine.learned_intent_candidate='MINT_AND_DEPLOY';
 assert.throws(()=>reviewLocalNeoBatch(q),/NEO_UNREGISTERED_MODEL_INTENT/);
 const r=packet();r.guarded_abstentions=0;
 assert.throws(()=>reviewLocalNeoBatch(r),/NEO_BATCH_COUNTS/);
});
test('reject malformed batch, oversized packet case, and absent case evidence',()=>{
 assert.throws(()=>reviewLocalNeoBatch({}),/NEO_REVIEW_SCHEMA/);
 const p=packet(Array(17).fill(null).map(()=>caseOf()));
 assert.throws(()=>reviewLocalNeoBatch(p),/NEO_REVIEW_COUNT/);
 const q=packet();q.tests[0].machine.input='x'.repeat(241);
 assert.throws(()=>reviewLocalNeoBatch(q),/NEO_PREVIEW_EFFECT_HOLD/);
});

 test('untrusted review cannot assert resolved assurance or substitute guard schema',()=>{
  for(const trit of [-1,1]){const p=packet();p.tests[0].machine.three_analytic_facets.assurance.trit=trit;assert.throws(()=>reviewLocalNeoBatch(p),/NEO_ASSURANCE_MUST_HOLD/);}
  const p=packet();p.tests[0].machine.guard.schema='untrusted';assert.throws(()=>reviewLocalNeoBatch(p),/NEO_GUARD_EFFECT_HOLD/);
 });
 test('abstention cannot retain a bound operation or unbounded display reason',()=>{
  for(const patch of [{intent:'SELECT'},{role:'T173:001'}]){const p=packet();Object.assign(p.tests[1].machine.guard,patch);assert.throws(()=>reviewLocalNeoBatch(p),/NEO_ABSTENTION_NOT_PRESERVED/);}
  for(const reason of [{unsafe:true},'x'.repeat(161)]){const p=packet();p.tests[1].machine.guard.reason=reason;assert.throws(()=>reviewLocalNeoBatch(p),/NEO_GUARD_REASON/);}
 });
