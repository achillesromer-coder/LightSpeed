/** Owner-proposed 173+1 review addressing. References only; no registry or mint authority. */
export const FAMILY_OBJECT_CAPACITY=173;
export const FAMILY_FOUNDER_SLOT=174;
export const FAMILY_LANGUAGE_PROFILE=Object.freeze({schema:'CGX-173-REFERENCE-LANGUAGE/0.1',object_slots:173,
 payload_values:'0..172 map to slots 1..173',binary_digits_per_slot:8,ternary_digits_per_slot:5,
 founder_reference_slot:174,founder_encoding:'separate typed self-reference; outside payload alphabet',
 semantics:'reference addressing only; no geometric or physical assertions',derivation_rule:'source/version + method + parameters + verified result digest; otherwise retain original'});
function width(radix){if(radix!==2&&radix!==3)throw Error('RADIX_MUST_BE_BINARY_OR_TERNARY');return radix===2?8:5;}
export function encodeFamilyPath(path,radix=2){
 const digits=width(radix);
 if(!Array.isArray(path)||path.length>256||path.some(s=>!Number.isInteger(s)||s<1||s>173))throw Error('OBJECT_SLOT_OUT_OF_RANGE');
 return path.map(s=>(s-1).toString(radix).padStart(digits,'0')).join('.');
}
export function decodeFamilyPath(text,radix=2){
 const digits=width(radix);if(typeof text!=='string')throw Error('INVALID_REFERENCE_CODE');if(text==='')return [];
 const words=text.split('.');if(words.length>256)throw Error('REFERENCE_DEPTH_LIMIT');
 return words.map(word=>{if(word.length!==digits||!(radix===2?/^[01]+$/:/^[012]+$/).test(word))throw Error('INVALID_REFERENCE_CODE');
  const value=parseInt(word,radix);if(value>172)throw Error('RESERVED_OR_UNUSED_REFERENCE_CODE');return value+1;});
}
async function dictionaryHash(dictionary){
 const data=new TextEncoder().encode(JSON.stringify(dictionary));
 return [...new Uint8Array(await globalThis.crypto.subtle.digest('SHA-256',data))].map(n=>n.toString(16).padStart(2,'0')).join('');
}
/** Shared dictionary contains references once. Packet requires that exact dictionary at readback. */
export async function makeReferenceShorthand(sourceRefs,{radix=2,rootRef='Cognigrex.cgx'}={}){
 width(radix);if(!Array.isArray(sourceRefs)||sourceRefs.length>50000)throw Error('REFERENCE_COUNT_LIMIT');
 const plan=planFamilyAddresses(sourceRefs,{rootRef}),dictionary={schema:'CGX-173-REFERENCE-DICTIONARY/0.1',parent:rootRef,source_refs:[...new Set(sourceRefs)]};
 const byRef=new Map();for(const group of plan.groups)for(const slot of group.slots)if(slot.kind==='object-reference')byRef.set(slot.source_ref,encodeFamilyPath([...group.path,slot.slot],radix));
 return {dictionary,packet:{schema:'CGX-173-REFERENCE-PACKET/0.1',dictionary_sha256:await dictionaryHash(dictionary),radix,
  codes:sourceRefs.map(ref=>byRef.get(ref)),native_mint:false}};
}
export async function restoreReferenceShorthand(packet,dictionary){
 if(packet?.schema!=='CGX-173-REFERENCE-PACKET/0.1'||dictionary?.schema!=='CGX-173-REFERENCE-DICTIONARY/0.1')throw Error('REFERENCE_SCHEMA_MISMATCH');
 if(!Array.isArray(packet.codes)||packet.codes.length>50000||!Array.isArray(dictionary.source_refs)||dictionary.source_refs.length>50000)throw Error('REFERENCE_COUNT_LIMIT');
 if(packet.dictionary_sha256!==await dictionaryHash(dictionary))throw Error('REFERENCE_DICTIONARY_HASH_MISMATCH');
 if(new Set(dictionary.source_refs).size!==dictionary.source_refs.length)throw Error('DUPLICATE_DICTIONARY_REFERENCE');
 width(packet.radix);const plan=planFamilyAddresses(dictionary.source_refs,{rootRef:dictionary.parent}),byCode=new Map();
 for(const group of plan.groups)for(const slot of group.slots)if(slot.kind==='object-reference')byCode.set(encodeFamilyPath([...group.path,slot.slot],packet.radix),slot.source_ref);
 return packet.codes.map(code=>{decodeFamilyPath(code,packet.radix);if(!byCode.has(code))throw Error('REFERENCE_NOT_IN_DICTIONARY');return byCode.get(code);});
}
export function planFamilyAddresses(sourceRefs,{rootRef='Cognigrex.cgx'}={}){
 if(typeof rootRef!=='string'||!rootRef.trim())throw Error('ROOT_REFERENCE_REQUIRED');
 if(!Array.isArray(sourceRefs)||sourceRefs.some(r=>typeof r!=='string'||!r.trim()))throw Error('EXISTING_SOURCE_REFERENCE_REQUIRED');
 const unique=[...new Set(sourceRefs)],groups=[];
 function fold(refs,path){
  const node={path,founder:{slot:FAMILY_FOUNDER_SLOT,kind:'self-reference',target:rootRef,target_path:[...path],mintable:false},slots:[]};
  groups.push(node);
  if(refs.length<=FAMILY_OBJECT_CAPACITY){
   node.slots=refs.map((source_ref,i)=>({slot:i+1,kind:'object-reference',source_ref,native_mint_ready:false}));
  }else{
   let span=FAMILY_OBJECT_CAPACITY;
   while(Math.ceil(refs.length/span)>FAMILY_OBJECT_CAPACITY)span*=FAMILY_OBJECT_CAPACITY;
   for(let i=0;i<refs.length;i+=span){
    const slot=node.slots.length+1,child=[...path,slot];
    node.slots.push({slot,kind:'umbrella-reference',child_path:child,mintable:false});
    fold(refs.slice(i,i+span),child);
   }
  }
 }
 fold(unique,[]);
 return {schema:'CGX-173-PLUS-REFERENCE-ADDRESS-REVIEW/0.1',parent:rootRef,evidence_class:'OWNER_PROPOSED_ADDRESSING',
  object_slots_per_group:173,reference_slot:174,source_reference_count:sourceRefs.length,unique_reference_count:unique.length,
  duplicate_references:sourceRefs.length-unique.length,ordering:'input order; no inferred semantic class',groups,
  ternary_state_encoding:'UNRESOLVED',physical_completeness_verified:false,geometry_catalogue_verified:false,
  reference_language:FAMILY_LANGUAGE_PROFILE,
  founder_is_object:false,new_database:false,native_mint:false,canonical_write:false};
}
