import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {CGXLanguageError,parseSlot,compileLine,encodeBytes,decodeBytes,validateRegistry} from './cgx_geometry_language.mjs';
const d=JSON.parse(readFileSync(new URL('./T173_NEO_ROLE_PROJECTION.review.json',import.meta.url)));
const matches=(f)=>assert.throws(f,CGXLanguageError);
test('full T173 slot sequence, no 174, and 157 payload declarations',()=>{
  assert.equal(validateRegistry(d).slots,173);
  assert.equal(new Set(d.slots.map(e=>e.mesh_ref)).size,157);
  for(let i=1;i<=173;i++){const slot=`T173:${String(i).padStart(3,'0')}`;assert.equal(parseSlot(slot,d).slot,slot);}
  for(const x of ['T173:174','T173:000','T173:175','T173:1','T3:001','T173:-01','T173:999'])matches(()=>parseSlot(x,d));
});
test('typed distinctness classifications retained',()=>{
  const count=(c)=>d.slots.filter(x=>x.class===c).length;
  assert.equal(count('DOCUMENTED_CONVENTIONAL_ALIAS'),9);
  assert.equal(count('FUNCTIONAL_OVERLAY_NOT_DISTINCT_SOLID'),6);
  assert.equal(count('PROVISIONAL_ALIAS_NOT_DISTINCT_SOLID'),1);
  assert.equal(count('NUMERIC_REFERENCE_REQUIRES_INDEPENDENT_ASSURANCE'),26);
  assert.deepEqual(d.seven_proposed_distinctness_workitems,['T173:131','T173:132','T173:133','T173:134','T173:135','T173:136','T173:137']);
});
test('compiler emits dry-run references and neither mints nor resolves gaps',()=>{
  const q=compileLine('SELECT T173:131',d);
  assert.equal(q.qualifier,'FUNCTIONAL_OVERLAY_UNPROVEN_SOLID');assert.equal(q.effects_performed,false);
  const r=compileLine('RELATE T173:001 adjacent_to T173:002',d);
  assert.equal(r.semantic_trit,0);assert.equal(r.requires_evidence,true);
  const t=compileLine('TRIAD T173:131 interacts_with T173:132',d);
  assert.equal(t.kind,'triadic_relation');assert.equal(t.status,'DRY_RUN_REVIEW_ONLY');
  const h=compileLine('PLAN_HYDRATE T173:001',d);
  assert.equal(h.hydrated,false);assert.ok(h.requirements.includes('authenticated_lease'));
  const x=compileLine('PLAN_TRANSFORM T173:001 scale=2 unit=m frame=local',d);
  assert.equal(x.factor,2);assert.equal(x.geometry_mutated,false);
  for(const s of ['SELECT T173:174','RELATE T173:001 owns T173:002','PLAN_TRANSFORM T173:001 scale=0 unit=m frame=local','PLAN_TRANSFORM T173:001 scale=Infinity unit=m frame=local','PLAN_HYDRATE T173:001 rights=free','HELLO T173:001'])matches(()=>compileLine(s,d));
});
test('transport trits are exact and do not assign geometric semantics',()=>{
  const bytes=Uint8Array.from({length:256},(_,i)=>i);
  const trits=encodeBytes(bytes);assert.equal(trits.length,6*256);
  assert.deepEqual(decodeBytes(trits),bytes);
  assert.equal(compileLine('ENCODE_BYTES 00ff7f',d).trits,encodeBytes(Uint8Array.of(0,255,127)));
  assert.equal(compileLine('DECODE_BYTES 000000100110',d).hex,'00ff');
  for(const s of ['222222','00001X','00000','000003'])matches(()=>decodeBytes(s));
  matches(()=>encodeBytes([1,2]));
});
test('tamper/identity/incompatible registry fails closed',()=>{
  let t=structuredClone(d);t.slots[0].slot='T173:002';matches(()=>validateRegistry(t));
  t=structuredClone(d);t.slots[2].native_admitted=true;matches(()=>validateRegistry(t));
  t=structuredClone(d);t.sentinel=null;matches(()=>validateRegistry(t));
});