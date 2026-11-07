import {describe,it,expect} from 'vitest';
import {planFamilyAddresses} from './cgxFamilyAddressModel.mjs';
describe('173 plus reference addressing',()=>{
 it('never invents blank objects or mints the reference slot',()=>{
  const p=planFamilyAddresses(['sha256:a','sha256:a','sha256:b']);
  expect(p.unique_reference_count).toBe(2);expect(p.groups[0].slots).toHaveLength(2);
  expect(p.groups[0].founder).toEqual({slot:174,kind:'self-reference',target:'Cognigrex.cgx',target_path:[],mintable:false});
  expect(p.ternary_state_encoding).toBe('UNRESOLVED');expect(p.native_mint).toBe(false);
 });
 it('folds a multi-level library without loss or overfilled groups',()=>{
  const refs=Array.from({length:173*173+1},(_,i)=>'source:'+i),p=planFamilyAddresses(refs);
  expect(p.groups.every(g=>g.slots.length<=173)).toBe(true);
  expect(p.groups.flatMap(g=>g.slots).filter(s=>s.kind==='object-reference').map(s=>s.source_ref)).toEqual(refs);
  expect(new Set(p.groups.map(g=>JSON.stringify(g.path))).size).toBe(p.groups.length);
 });
 it('requires actual references',()=>{expect(()=>planFamilyAddresses([''])).toThrow('EXISTING_SOURCE_REFERENCE_REQUIRED');});
});
