import {describe,it,expect} from 'vitest';
import {planFamilyAddresses,encodeFamilyPath,decodeFamilyPath,makeReferenceShorthand,restoreReferenceShorthand} from './cgxFamilyAddressModel.mjs';
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
describe('binary/ternary reference language',()=>{
 it('round-trips every real slot and rejects founder/spare codes in both radices',()=>{
  for(const radix of [2,3]){
   for(let slot=1;slot<=173;slot++)expect(decodeFamilyPath(encodeFamilyPath([slot],radix),radix)).toEqual([slot]);
   expect(()=>encodeFamilyPath([174],radix)).toThrow('OBJECT_SLOT_OUT_OF_RANGE');
   const unused=(173).toString(radix).padStart(radix===2?8:5,'0');
   expect(()=>decodeFamilyPath(unused,radix)).toThrow('RESERVED_OR_UNUSED_REFERENCE_CODE');
  }
  expect(()=>decodeFamilyPath('111',2)).toThrow('INVALID_REFERENCE_CODE');
  expect(()=>encodeFamilyPath([1],174)).toThrow('RADIX_MUST_BE_BINARY_OR_TERNARY');
 });
 it('restores repeated ordered references through umbrellas without duplicating dictionary entries',async()=>{
  const refs=Array.from({length:996},(_,i)=>'sha256:source-'+(i%989));
  for(const radix of [2,3]){const {dictionary,packet}=await makeReferenceShorthand(refs,{radix});
   expect(dictionary.source_refs).toHaveLength(989);expect(await restoreReferenceShorthand(packet,dictionary)).toEqual(refs);
   expect(packet.native_mint).toBe(false);
   expect(()=>JSON.stringify(packet)).not.toThrow();
  }
 });
 it('fails closed on altered dictionaries and unresolved/invalid references',async()=>{
  const {dictionary,packet}=await makeReferenceShorthand(['source:a']);
  await expect(restoreReferenceShorthand(packet,{...dictionary,parent:'different-root'})).rejects.toThrow('REFERENCE_DICTIONARY_HASH_MISMATCH');
  await expect(restoreReferenceShorthand({...packet,codes:['00000001']},dictionary)).rejects.toThrow('REFERENCE_NOT_IN_DICTIONARY');
  await expect(restoreReferenceShorthand({...packet,codes:['0000000x']},dictionary)).rejects.toThrow('INVALID_REFERENCE_CODE');
 });
});
