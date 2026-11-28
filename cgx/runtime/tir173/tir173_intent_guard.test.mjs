import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {encodeOrdinal} from './tir173_core.mjs';
import {inspectTir173Intent,TIR173_REVIEW_INTENTS} from './tir173_intent_guard.mjs';
const bytes=readFileSync(new URL('../../../docs/agent-ingestion/local-agent-homes/Z+2_Neo/pilots/raphael_temporal/geometry_language/T173_NEO_ROLE_PROJECTION.review.json',import.meta.url));
const slots=JSON.parse(bytes.toString()).slots;
const dictionary={
  schema:'cgx.t173.shape_dictionary/0.2',
  source_sha256:createHash('sha256').update(bytes).digest('hex'),
  sentinel:null,
  roles:slots.map((s,i)=>({slot:i+1,role:'T173:'+String(i+1).padStart(3,'0'),
    name:'Raphael research role '+(i+1),family:s.class,mesh_ref:String(s.mesh_ref),evidence:s.qualifier}))
};
const negatives=[
  '', ' ', 'SELECT','SELECT T173:000','SELECT T173:174',
  'SELECT T173:999','SELECT T173:001 T173:002','RELATE T173:001,T173:002',
  'SELECT T173:001; DELETE FROM items','SELECT T173:001\nDROP TABLE items',
  'sudo SELECT T173:001','SELECT T173:001 --force',
  'mint T173:001 now','deploy the agent T173:001',
  'execute a real LOAD hydrate for T173:001',
  'give me permission to write T173:001',
  'print shape T173:001','which geometry is T173:001',
  'interpret the meaning of T173:011','modify T173:097 in place',
  'rotate T173:173 by 90 degrees','can T173:001 pass through the material',
  'simulate electrical current on T173:097',
  'is T173:011 chiral and physically proven',
  'SELECT T173:001 then encrypt','SELECT T173:001 and also mint',
  'SELECT  T173:001','select T173:001','TRIAD T173:001!',
  'T173:001 SELECT','PLAN_TRANSFORM T173:097 matrix=identity',
  'ENCODE_BYTES T173:001 ff00','DECODE_BYTES T173:011 0ff',
  'ATLAS_RULE T173:173 CIM-001','compare T173:001 and T173:173',
  'I feel unsure whether to hydrate T173:001',
  'please do what is best with T173:011','T173:001'
];
test('32 exact typed inputs produce source-bound incomplete review plans, never effects',()=>{
  assert.equal(TIR173_REVIEW_INTENTS.length,8);
  let count=0;
  for(const intent of TIR173_REVIEW_INTENTS){
    for(const n of [1,11,97,173]){
      const role='T173:'+String(n).padStart(3,'0');
      const result=inspectTir173Intent(dictionary,intent+' '+role,{expected_role:role});
      assert.equal(result.machine.status,'EXACT_CANONICAL_REVIEW_PLAN');
      assert.equal(result.machine.shape_role,role);
      assert.equal(result.machine.address_trits,encodeOrdinal(n));
      assert.equal(result.machine.mesh_ref,dictionary.roles[n-1].mesh_ref);
      assert.equal(result.machine.dictionary_source_sha256,dictionary.source_sha256);
      assert.equal(result.machine.source_rights_verified,false);
      assert.equal(result.machine.operation_complete,false);
      assert.equal(result.machine.all_inputs_qualified,false);
      assert.equal(result.machine.command_executed,false);
      assert.equal(result.machine.mint_performed,false);
      assert.equal(result.machine.native_admitted,false);
      assert.match(result.human.summary,new RegExp(role));
      assert.match(result.human.missing,/[A-Z]/);
      count++;
    }
  }
  assert.equal(count,32);
});
test('38 project-authored ambiguous/privileged/invalid requests fail closed',()=>{
  assert.equal(negatives.length,38);
  for(const input of negatives){
    const result=inspectTir173Intent(dictionary,input);
    assert.equal(result.machine.status,'ABSTAIN_REVIEW_REQUIRED',input);
    assert.equal(result.machine.command_executed,false,input);
    assert.equal(result.machine.native_admitted,false,input);
    assert.equal(result.machine.hydration_performed,false,input);
    assert.equal(result.machine.model_approved,false,input);
    assert.match(result.human.status,/Abstain:/);
  }
});
test('all 173 dictionary roles are address-preserving; all reserved role requests abstain',()=>{
  for(let i=1;i<=173;i++){
    const role='T173:'+String(i).padStart(3,'0');
    assert.equal(inspectTir173Intent(dictionary,'SELECT '+role).machine.address_trits,encodeOrdinal(i));
  }
  for(const n of [0,174,175,999])
    assert.equal(inspectTir173Intent(dictionary,'SELECT T173:'+String(n).padStart(3,'0')).machine.status,'ABSTAIN_REVIEW_REQUIRED');
});
test('GUIOS selection identity mismatches cannot route a command to another shape',()=>{
  const a=inspectTir173Intent(dictionary,'SELECT T173:001',{expected_role:'T173:173'});
  assert.equal(a.machine.status,'ABSTAIN_REVIEW_REQUIRED');
  assert.equal(a.machine.reason,'ROLE_CONTEXT_MISMATCH');
  assert.equal(a.machine.command_executed,false);
  const b=inspectTir173Intent(dictionary,'SELECT T173:173',{expected_role:'T173:173'});
  assert.equal(b.machine.status,'EXACT_CANONICAL_REVIEW_PLAN');
});
test('invalid dictionary and unknown input shapes cannot be promoted',()=>{
  assert.throws(()=>inspectTir173Intent({...dictionary,sentinel:174},'SELECT T173:001'));
  for(const input of [null,5,{},[],new String('SELECT T173:001'),'A'.repeat(241)]){
    const result=inspectTir173Intent(dictionary,input);
    assert.equal(result.machine.status,'ABSTAIN_REVIEW_REQUIRED');
  }
  const result=inspectTir173Intent(dictionary,'SELECT T173:001',{expected_role:'T173:000'});
  assert.equal(result.machine.status,'ABSTAIN_REVIEW_REQUIRED');
});
