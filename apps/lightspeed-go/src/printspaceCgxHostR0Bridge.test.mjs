/** Node-side cross-contract tests; host context/lineage are SYNTHETIC. */
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {reviewPrintspaceHostR0 as review} from './printspaceCgxHostR0Bridge.mjs';
const SOURCE = `
import json
from cgx.manufacturing.printspace_cgx import build_bundle
from cgx.manufacturing.virtual_factory import load_catalogue
from cgx.manufacturing.printspace_host_preflight import prepare_r0_host_review
c=load_catalogue();b=build_bundle(c)
rows=[{'product_id':name,'candidate_object_id':'PS-'+name.upper()+'-CANDIDATE-001',
       'twin_id':name+'-candidate','lineage_git_blob_sha':'1'*40,
       'registry_git_blob_sha':'2'*40} for name in ('diode','board','phone')]
print(json.dumps(prepare_r0_host_review(b,c,rows),ensure_ascii=True,sort_keys=True))
`;
const REPO_ROOT = new URL('../../../', import.meta.url).pathname;
const plan=JSON.parse(execFileSync('python',['-c',SOURCE],{cwd:REPO_ROOT,encoding:'utf8'}));
const safeClone=x=>structuredClone(x);
const fixture=(product='diode')=>{
  const item=plan.r0_cases.find(x=>x.product_id===product);
  const id=item.candidate_object_id,twin=item.twin_id_candidate;
  return {input:{
    plan:safeClone(plan),product_id:product,
    context_response:{execution_performed:false,external_action_performed:false,
      canonical_mutation:false,authority_transfer:false,
      object_context:{schema:'CGX-OBJECT-CONTEXT/0.1',automatic_execution:false,
        canonical_mutation:false,resolved_twin_id:twin,semantic_domain:'romer',
        domain_identity:{semantic_object_id:'cgx:domain:romer',filespace:'Romer.cgx'},
        semantic_resolution:{state:'exact_semantic_object',semantic_object_id:id}}},
    lineage_candidates:[{semantic_object_id:id,twin_id:twin}],
    load_contract:{schema:'LOAD-ALEXANDRIA-ACTIVATION/0.1',
      status:'SOURCE_REVIEW_NOT_ADMITTED',alias:'LOAD.cgx',
      parent_filespace:'Cognigrex.cgx',canonical_object_id:null,
      accepted_parent_object_id:null,canonical_mutation:false,
      network_fetch:'DENY_UNTIL_HOST_AUTHORIZED'},
    client_permissions:{mode:'review_only',revoked:false,
      allowed_object_ids:[id],allowed_filespaces:['Romer.cgx']},
    source_status:{collision:'no_conflict_reported',rights:'cleared_for_review',
      evidence_class:'scientific'},
  },pins:{bundle_sha256:item.bundle_sha256,plan_sha256:plan.plan_sha256,
           product_facet_sha256:item.product_facet_sha256}};
};
const run=x=>review(x.input,x.pins);

test('matches both EXISTING UniSpace host/LOAD adapters for three scoped R0 candidates',()=>{
  for(const product of ['diode','board','phone']){
    const v=run(fixture(product));
    assert.equal(v.state,'PLAN_ONLY_NOT_HYDRATED',JSON.stringify(v));
    assert.equal(v.product_id,product);
    assert.equal(v.filespace,'Romer.cgx');
    assert.equal(v.requested_layer,'R0');
    assert.equal(v.planned_hydration,'H0');
    assert.equal(v.host_context_schema,'UNISPACE-CGX-HOST-CONTEXT-GATE/0.1');
    assert.equal(v.load_review_schema,'UNISPACE-CGX-LOAD-LENS-PLAN/0.1');
    for(const flag of ['native_admitted','source_rights_independently_verified',
      'host_context_readback_authenticated','network_fetch','execution_performed',
      'machine_authorised','native_dbr_written','public_publish_authorized',
      'mint_authorised','commercial_release_authorised'])assert.equal(v[flag],false,flag);
    assert.equal(v.source_bytes_hydrated,0);
  }
});

test('source plan digest and out-of-band hash mismatch fail closed',()=>{
  const a=fixture();a.input.plan.r0_cases[0].candidate_object_id='ALIAS';
  assert.equal(run(a).state,'HOLD');
  const b=fixture();b.pins.bundle_sha256='sha256:'+'a'.repeat(64);
  assert.equal(run(b).hold_code,'SOURCE_PLAN_TAMPER_OR_PIN_MISMATCH');
  const c=fixture();c.pins.product_facet_sha256='sha256:'+'0'.repeat(64);
  assert.equal(run(c).hold_code,'PRODUCT_FACET_OR_CHILD_MISMATCH');
});

test('wrong product, unbound source plan and extra privilege fields denied',()=>{
  const a=fixture();a.input.product_id='wrong';assert.equal(run(a).state,'HOLD');
  const b=fixture();b.input.plan.r0_cases[1].host_context_request_ready=false;
  assert.equal(run(b).state,'HOLD');
  const c=fixture();c.input.requested_layer='R3';
  assert.equal(run(c).hold_code,'UNEXPECTED_OR_UNKNOWN_HOST_INPUT');
});

test('lineage collision, twin mismatch and domain drift are holds',()=>{
  const a=fixture();a.input.lineage_candidates.push({semantic_object_id:'PS-DIODE-CANDIDATE-001',twin_id:'collision'});
  assert.equal(run(a).hold_code,'HOST_LINEAGE_COLLISION_OR_MISMATCH');
  const b=fixture();b.input.context_response.object_context.resolved_twin_id='other';
  assert.equal(run(b).state,'HOLD');
  const c=fixture();c.input.context_response.object_context.domain_identity.filespace='Eco.cgx';
  assert.equal(run(c).state,'HOLD');
});

test('revoked client and unresolved rights remain denied',()=>{
  const a=fixture();a.input.client_permissions.revoked=true;
  assert.equal(run(a).state,'HOLD');
  const b=fixture();b.input.source_status.rights='unknown';
  assert.equal(run(b).state,'HOLD');
  const c=fixture();c.input.source_status.collision='ambiguous';
  assert.equal(run(c).state,'HOLD');
});

test('LOAD activation, H4, private data and host execution denied',()=>{
  const a=fixture();a.input.load_contract.canonical_object_id='FORGED';
  assert.equal(run(a).state,'HOLD');
  const b=fixture();b.input.context_response.execution_performed=true;
  assert.equal(run(b).state,'HOLD');
  const c=fixture();c.input.context_response.object_context.session_token='SECRET';
  assert.equal(run(c).state,'HOLD');
  const d=fixture();d.input.plan.native_admitted=true;
  assert.equal(run(d).state,'HOLD');
});

test('missing pins and private token rejected without source leakage',()=>{
  const f=fixture();assert.equal(review(f.input,null).state,'HOLD');
  f.input.client_permissions.token='SECRET';
  const out=run(f);
  assert.equal(out.state,'HOLD');
  assert.equal(JSON.stringify(out).includes('SECRET'),false);
});
